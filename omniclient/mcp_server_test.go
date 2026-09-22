package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNewOmninodeServer(t *testing.T) {
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("NewOmninodeServer panicked: %v", r)
		}
	}()

	server := NewOmninodeServer()
	if server == nil {
		t.Fatal("server is nil")
	}
	if server.gateway == nil {
		t.Fatal("gateway is nil")
	}
}

func TestGatewayBrowseUsesLocalHTTPContract(t *testing.T) {
	requestSeen := make(chan struct{}, 1)
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("method = %s, want POST", r.Method)
		}
		if r.URL.Path != "/api/v1/browse" {
			t.Errorf("path = %s, want /api/v1/browse", r.URL.Path)
		}

		var body map[string]any
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatalf("decode request: %v", err)
		}
		if body["url"] != "https://example.com" {
			t.Errorf("url = %v", body["url"])
		}
		if body["extract_content"] != "markdown" {
			t.Errorf("extract_content = %v", body["extract_content"])
		}

		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"title":"Example","content":"Hello","node_id":"node-test","format":"markdown","request_id":"task-test","status":"completed"}`))
		requestSeen <- struct{}{}
	}))
	defer ts.Close()

	gateway := NewHTTPGateway(ts.URL)
	res, err := gateway.Browse(context.Background(), "https://example.com", "markdown")
	if err != nil {
		t.Fatalf("Browse returned error: %v", err)
	}
	if res.NodeID != "node-test" {
		t.Fatalf("NodeID = %q, want node-test", res.NodeID)
	}
	if res.Title != "Example" || res.Content != "Hello" {
		t.Fatalf("unexpected result: %+v", res)
	}
	select {
	case <-requestSeen:
	default:
		t.Fatal("HTTP handler did not observe request")
	}
}
