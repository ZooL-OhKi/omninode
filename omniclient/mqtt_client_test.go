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

func TestV1Topics(t *testing.T) {
	cases := map[string]func(string) string{
		"omninode/v1/nodes/worker-1/tasks":       taskTopic,
		"omninode/v1/nodes/worker-1/responses":   responseTopic,
		"omninode/v1/nodes/worker-1/heartbeat":   heartbeatTopic,
		"omninode/v1/nodes/worker-1/control":     controlTopic,
		"omninode/v1/nodes/worker-1/control/ack": controlAckTopic,
	}
	for expected, builder := range cases {
		if got := builder("worker-1"); got != expected {
			t.Fatalf("unexpected topic: got %s, want %s", got, expected)
		}
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

func TestControlAcknowledgementIsStructuredJSON(t *testing.T) {
	ack := ControlAcknowledgement{Type: "task_approval", TaskID: "task-1", Acknowledged: true}
	encoded, err := json.Marshal(ack)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err := json.Unmarshal(encoded, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["task_id"] != "task-1" || decoded["acknowledged"] != true {
		t.Fatalf("unexpected acknowledgement: %s", encoded)
	}
}

func TestWorkspaceHandlerRejectsPathTraversal(t *testing.T) {
	handler := NewWorkspaceHandler(t.TempDir())
	payload := json.RawMessage(`{"path":"../outside.txt","content":"no"}`)
	if _, err := handler.Execute(TaskEnvelope{TaskID: "task-1", TaskType: "workspace.write", Payload: payload}); err == nil {
		t.Fatal("expected path traversal rejection")
	}
}
