package main

import (
	"encoding/json"
	"testing"
)

func TestBuildTLSConfigRequiresAllCredentials(t *testing.T) {
	if _, err := buildTLSConfig("", "cert.pem", "key.pem", "broker.local"); err == nil {
		t.Fatal("expected error when CA path is empty")
	}
	if _, err := buildTLSConfig("ca.pem", "", "key.pem", "broker.local"); err == nil {
		t.Fatal("expected error when client certificate is empty")
	}
	if _, err := buildTLSConfig("ca.pem", "cert.pem", "", "broker.local"); err == nil {
		t.Fatal("expected error when client key is empty")
	}
}

func TestBuildTLSConfigFailsOnMissingFiles(t *testing.T) {
	_, err := buildTLSConfig("/nonexistent/ca.pem", "/nonexistent/cert.pem", "/nonexistent/key.pem", "broker.local")
	if err == nil {
		t.Fatal("expected certificate loading failure")
	}
}

func TestTaskAndResponseTopicsUseV1(t *testing.T) {
	if got := taskTopic("worker-1"); got != "omninode/v1/nodes/worker-1/tasks" {
		t.Fatalf("unexpected task topic: %s", got)
	}
	if got := responseTopic("worker-1"); got != "omninode/v1/nodes/worker-1/responses" {
		t.Fatalf("unexpected response topic: %s", got)
	}
}

func TestTaskResponseIsStructuredJSON(t *testing.T) {
	response := TaskResponse{TaskID: "task-1", Status: "completed", Result: json.RawMessage(`{"ok":true}`)}
	encoded, err := json.Marshal(response)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err := json.Unmarshal(encoded, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["task_id"] != "task-1" || decoded["status"] != "completed" {
		t.Fatalf("unexpected response: %s", encoded)
	}
}

func TestWorkspaceHandlerRejectsPathTraversal(t *testing.T) {
	handler := NewWorkspaceHandler(t.TempDir())
	payload := json.RawMessage(`{"path":"../outside.txt","content":"no"}`)
	if _, err := handler.Execute(TaskEnvelope{TaskID: "task-1", TaskType: "workspace.write", Payload: payload}); err == nil {
		t.Fatal("expected path traversal rejection")
	}
}
