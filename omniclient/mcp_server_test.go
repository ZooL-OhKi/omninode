package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestNewOmninodeServer verifica che l'inizializzazione del server MCP non generi panic
func TestNewOmninodeServer(t *testing.T) {
	t.Helper()
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("NewOmninodeServer ha generato un panic: %v", r)
		}
	}()

	server := NewOmninodeServer()
	if server == nil {
		t.Fatal("Il server inizializzato e nil")
	}
	if server.gateway == nil {
		t.Fatal("Il gateway del server non e stato inizializzato")
	}
}

// TestGatewayHTTPWithTestServer verifica il contratto HTTP reale del client usando httptest.NewServer
func TestGatewayHTTPWithTestServer(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("Metodo HTTP atteso POST, ricevuto %s", r.Method)
		}
		if r.URL.Path != "/api/v1/browse" {
			t.Errorf("Path atteso /api/v1/browse, ricevuto %s", r.URL.Path)
		}
		if r.Header.Get("Content-Type") != "application/json" {
			t.Errorf("Header Content-Type application/json atteso")
		}

		var req map[string]interface{}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Errorf("Errore nella decodifica del body JSON di richiesta: %v", err)
		}

		if req["url"] != "https://example.com" {
			t.Errorf("URL atteso 'https://example.com', ricevuto '%v'", req["url"])
		}

		resp := map[string]interface{}{
			"title":      "Pagina estratta da Omninode",
			"content":    "# Contenuto Markdown (Mock)\n\t\tQuesto è il parsing di: https://example.com",
			"node_id":    "node-browser-02",
			"format":     "markdown",
			"request_id": "req_mock_12345",
			"status":     "completed",
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(resp)
	}))
	defer ts.Close()

	gateway := NewHTTPGateway(ts.URL)

	res, err := gateway.Browse(context.Background(), "https://example.com", "markdown")
	if err != nil {
		t.Fatalf("Errore imprevisto durante la chiamata Browse: %v", err)
	}

	if res == nil {
		t.Fatal("Il risultato restituito da Browse non puo essere nil")
	}
	if res.NodeID != "node-browser-02" {
		t.Errorf("NodeID atteso 'node-browser-02', ricevuto '%s'", res.NodeID)
	}
	if res.Title != "Pagina estratta da Omninode" {
		t.Errorf("Title atteso 'Pagina estratta da Omninode', ricevuto '%s'", res.Title)
	}
}

type fakeGateway struct {
	listResult     map[string]any
	readResult     map[string]any
	rollbackResult map[string]any
	verifyResult   map[string]any
	autonomyResult map[string]any
}

func (f *fakeGateway) RestartNode(nodeID string) error { return nil }
func (f *fakeGateway) Execute(ctx context.Context, language, code string) (*ExecuteResult, error) {
	return &ExecuteResult{}, nil
}
func (f *fakeGateway) Browse(ctx context.Context, url, format string) (*BrowseResult, error) {
	return &BrowseResult{}, nil
}
func (f *fakeGateway) DispatchTask(ctx context.Context, nodeID, taskType string, payload map[string]any) (*DispatchResponse, error) {
	return &DispatchResponse{TaskID: "task-1"}, nil
}
func (f *fakeGateway) GetTaskStatus(ctx context.Context, taskID string) (*TaskStatus, error) {
	return &TaskStatus{Status: "completed"}, nil
}
func (f *fakeGateway) AutonomyRunStep(ctx context.Context, targetFile, content string, contextFiles []string) (map[string]any, error) {
	return f.autonomyResult, nil
}
func (f *fakeGateway) WorkspaceList(ctx context.Context, subpath string) (map[string]any, error) {
	return f.listResult, nil
}
func (f *fakeGateway) WorkspaceRead(ctx context.Context, path string) (map[string]any, error) {
	return f.readResult, nil
}
func (f *fakeGateway) WorkspaceRollback(ctx context.Context, path string) (map[string]any, error) {
	return f.rollbackResult, nil
}
func (f *fakeGateway) CommandVerify(ctx context.Context, preset string) (map[string]any, error) {
	return f.verifyResult, nil
}
func (f *fakeGateway) FabricHealth() (map[string]interface{}, error) {
	return map[string]interface{}{"health_status": "ok"}, nil
}

func TestOmninodeCommandVerifyRejectsUnknownPreset(t *testing.T) {
	server := NewOmninodeServerWithGateway(&fakeGateway{})
	_, _, err := server.handleOmninodeCommandVerify(
		context.Background(), nil,
		OmninodeCommandVerifyInput{Preset: "rm -rf /"},
	)
	if err == nil {
		t.Fatal("atteso errore per preset non consentito")
	}
}

func TestOmninodeWorkspaceReadDecodesGatewayResult(t *testing.T) {
	gateway := &fakeGateway{
		readResult: map[string]any{
			"path":       "node1-gateway/ok.py",
			"content":    "VALUE = 1\n",
			"sha256":     "abc",
			"size_bytes": 10,
		},
	}
	server := NewOmninodeServerWithGateway(gateway)

	_, output, err := server.handleOmninodeWorkspaceRead(
		context.Background(), nil,
		OmninodeWorkspaceReadInput{Path: "node1-gateway/ok.py"},
	)
	if err != nil {
		t.Fatalf("errore imprevisto: %v", err)
	}
	if output.Path != "node1-gateway/ok.py" || output.Content != "VALUE = 1\n" || output.SHA256 != "abc" {
		t.Fatalf("output inatteso: %+v", output)
	}
}

func TestOmninodeAutonomyStepCallsAtomicRunStep(t *testing.T) {
	gateway := &fakeGateway{
		autonomyResult: map[string]any{
			"status":       "committed",
			"changed_files": []string{"node1-gateway/ok.py"},
			"rolled_back":  false,
		},
	}
	server := NewOmninodeServerWithGateway(gateway)

	_, output, err := server.handleOmninodeAutonomyStep(
		context.Background(), nil,
		OmninodeAutonomyStepInput{
			TargetFile: "node1-gateway/ok.py",
			Content:    "VALUE = 2\n",
		},
	)
	if err != nil {
		t.Fatalf("errore imprevisto: %v", err)
	}
	if output.Status != "committed" || output.RolledBack {
		t.Fatalf("output inatteso: %+v", output)
	}
	if len(output.ChangedFiles) != 1 || output.ChangedFiles[0] != "node1-gateway/ok.py" {
		t.Fatalf("changed_files inattesi: %+v", output.ChangedFiles)
	}
}
