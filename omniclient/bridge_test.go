package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func newBridgeTestServer(t *testing.T) (*BridgeService, string) {
	t.Helper()
	root := t.TempDir()
	workspace := NewWorkspaceHandler(root)
	bridge, err := NewBridgeService(workspace, "test-token-0123456789abcdef0123456789abcdef", "http://127.0.0.1:8080")
	if err != nil {
		t.Fatalf("NewBridgeService: %v", err)
	}
	return bridge, root
}

func bridgePost(t *testing.T, bridge *BridgeService, host, origin, token, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "http://"+host+"/api/bridge/execute", strings.NewReader(body))
	req.Host = host
	if origin != "" {
		req.Header.Set("Origin", origin)
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	rec := httptest.NewRecorder()
	bridge.ServeHTTP(rec, req)
	return rec
}

func TestBridgeCreatesFileAndReturnsResult(t *testing.T) {
	bridge, root := newBridgeTestServer(t)
	body := `{"request_id":"req-00000001","path":"notes/gemini.md","content":"# risultato"}`
	rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", "test-token-0123456789abcdef0123456789abcdef", body)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, body = %s", rec.Code, rec.Body.String())
	}
	data, err := os.ReadFile(filepath.Join(root, "notes", "gemini.md"))
	if err != nil || string(data) != "# risultato" {
		t.Fatalf("file non creato correttamente: %v, %q", err, data)
	}
}

func TestBridgeDuplicateSamePayloadDoesNotWriteAgain(t *testing.T) {
	bridge, root := newBridgeTestServer(t)
	token := "test-token-0123456789abcdef0123456789abcdef"
	body := `{"request_id":"req-00000002","path":"dup.txt","content":"stesso"}`
	first := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", token, body)
	if first.Code != http.StatusOK {
		t.Fatalf("prima richiesta: %d", first.Code)
	}
	second := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", token, body)
	if second.Code != http.StatusOK {
		t.Fatalf("duplicato: %d", second.Code)
	}
	var response BridgeResponse
	if err := json.Unmarshal(second.Body.Bytes(), &response); err != nil || !response.Duplicate {
		t.Fatalf("risposta duplicato non valida: %s, %v", second.Body.String(), err)
	}
	if _, err := os.Stat(filepath.Join(root, "dup.txt")); err != nil {
		t.Fatalf("file originale mancante: %v", err)
	}
}

func TestBridgeConflictingPayloadRejected(t *testing.T) {
	bridge, _ := newBridgeTestServer(t)
	token := "test-token-0123456789abcdef0123456789abcdef"
	base := `{"request_id":"req-00000003","path":"conflict.txt","content":"primo"}`
	if rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", token, base); rec.Code != http.StatusOK {
		t.Fatalf("prima richiesta: %d", rec.Code)
	}
	conflict := `{"request_id":"req-00000003","path":"conflict.txt","content":"diverso"}`
	rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", token, conflict)
	if rec.Code != http.StatusConflict {
		t.Fatalf("atteso 409, ottenuto %d: %s", rec.Code, rec.Body.String())
	}
}

func TestBridgeRejectsUnauthorizedAndUnsafeRequests(t *testing.T) {
	bridge, _ := newBridgeTestServer(t)
	token := "test-token-0123456789abcdef0123456789abcdef"
	body := `{"request_id":"req-00000004","path":"safe.txt","content":"x"}`

	if rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", "", body); rec.Code != http.StatusUnauthorized {
		t.Fatalf("token mancante: %d", rec.Code)
	}
	if rec := bridgePost(t, bridge, "example.com:8080", "http://127.0.0.1:8080", token, body); rec.Code != http.StatusForbidden {
		t.Fatalf("host non loopback: %d", rec.Code)
	}
	if rec := bridgePost(t, bridge, "127.0.0.1:8080", "https://evil.example", token, body); rec.Code != http.StatusForbidden {
		t.Fatalf("origine non autorizzata: %d", rec.Code)
	}
	traversal := `{"request_id":"req-00000005","path":"../escape.txt","content":"x"}`
	if rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", token, traversal); rec.Code != http.StatusBadRequest {
		t.Fatalf("path traversal: %d", rec.Code)
	}
}

func TestBridgeRejectsUnknownFields(t *testing.T) {
	bridge, _ := newBridgeTestServer(t)
	body := `{"request_id":"req-00000006","path":"x.txt","content":"x","command":"rm -rf /"}`
	rec := bridgePost(t, bridge, "127.0.0.1:8080", "http://127.0.0.1:8080", "test-token-0123456789abcdef0123456789abcdef", body)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("campo sconosciuto accettato: %d", rec.Code)
	}
}
