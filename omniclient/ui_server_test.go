package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestUIHandlerServesPWAIndexAndManifest(t *testing.T) {
	handler, err := NewUIHandler("http://127.0.0.1:8000", "test-secret")
	if err != nil {
		t.Fatalf("errore inizializzazione NewUIHandler: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("atteso status 200 per /, ottenuto %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "OmniNode Control Center") {
		t.Fatalf("contenuto index.html non trovato nella risposta")
	}

	reqManifest := httptest.NewRequest(http.MethodGet, "/manifest.json", nil)
	recManifest := httptest.NewRecorder()
	handler.ServeHTTP(recManifest, reqManifest)

	if recManifest.Code != http.StatusOK {
		t.Fatalf("atteso status 200 per /manifest.json, ottenuto %d", recManifest.Code)
	}
}

func TestUIHandlerProxiesWorkspaceWriteWithSecret(t *testing.T) {
	var capturedAuth string
	var capturedRPC map[string]interface{}

	fakeGateway := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedAuth = r.Header.Get("Authorization")
		_ = json.NewDecoder(r.Body).Decode(&capturedRPC)
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"jsonrpc": "2.0",
			"id":      capturedRPC["id"],
			"result": map[string]interface{}{
				"status": "completed",
			},
		})
	}))
	defer fakeGateway.Close()

	handler, err := NewUIHandler(fakeGateway.URL, "super-secret-token")
	if err != nil {
		t.Fatalf("errore NewUIHandler: %v", err)
	}

	payload := []byte(`{"agent_id":"archivista","path":"note.txt","content":"test pwa"}`)
	req := httptest.NewRequest(http.MethodPost, "/api/task/write", bytes.NewReader(payload))
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("atteso status 200, ottenuto %d: %s", rec.Code, rec.Body.String())
	}
	if capturedAuth != "Bearer super-secret-token" {
		t.Fatalf("header Authorization non iniettato correttamente: %s", capturedAuth)
	}
	if capturedRPC["method"] != "workspace.write" {
		t.Fatalf("metodo JSON-RPC errato: %v", capturedRPC["method"])
	}
}

func TestUIHandlerNaturalLanguagePromptCreatesFile(t *testing.T) {
	var capturedRPC map[string]interface{}

	fakeGateway := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewDecoder(r.Body).Decode(&capturedRPC)
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"jsonrpc": "2.0",
			"id":      capturedRPC["id"],
			"result": map[string]interface{}{
				"status": "completed",
			},
		})
	}))
	defer fakeGateway.Close()

	handler, err := NewUIHandler(fakeGateway.URL, "secret-123")
	if err != nil {
		t.Fatalf("errore NewUIHandler: %v", err)
	}

	payload := []byte(`{"prompt":"Crea un file di appunti note-ia.txt nel workspace di Archivista: Contenuto generato da comando naturale"}`)
	req := httptest.NewRequest(http.MethodPost, "/api/task/prompt", bytes.NewReader(payload))
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("atteso status 200, ottenuto %d: %s", rec.Code, rec.Body.String())
	}
	params, ok := capturedRPC["params"].(map[string]interface{})
	if !ok {
		t.Fatalf("params mancanti nel payload JSON-RPC")
	}
	if params["path"] != "note-ia.txt" {
		t.Fatalf("atteso path note-ia.txt, ottenuto %v", params["path"])
	}
	if params["content"] != "Contenuto generato da comando naturale" {
		t.Fatalf("contenuto errato: %v", params["content"])
	}
}
