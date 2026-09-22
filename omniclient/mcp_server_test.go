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
