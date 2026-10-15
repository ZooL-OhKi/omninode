package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestWorkspaceHandlerWritesInsideRoot(t *testing.T) {
	root := t.TempDir()
	handler := NewWorkspaceHandler(root)
	payload := json.RawMessage(`{"path":"reports/result.txt","content":"ok"}`)
	result, err := handler.Execute(TaskEnvelope{TaskID: "task-1", TaskType: "workspace.write", Payload: payload})
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(filepath.Join(root, "reports", "result.txt"))
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != "ok" {
		t.Fatalf("unexpected file content: %q", data)
	}
	if len(result) == 0 {
		t.Fatal("expected structured result")
	}
}

func TestWorkspaceHandlerRejectsUnknownTask(t *testing.T) {
	handler := NewWorkspaceHandler(t.TempDir())
	if _, err := handler.Execute(TaskEnvelope{TaskID: "task-1", TaskType: "shell.exec", Payload: json.RawMessage(`{"command":"rm -rf /"}`)}); err == nil {
		t.Fatal("expected unsupported task rejection")
	}
}
