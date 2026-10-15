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

func TestWorkspaceHandlerIgnoresDuplicateTask(t *testing.T) {
	root := t.TempDir()
	handler := NewWorkspaceHandler(root)
	envelope := TaskEnvelope{
		TaskID:   "duplicate-1",
		TaskType: "workspace.write",
		Payload:  json.RawMessage(`{"path":"duplicate.txt","content":"first"}`),
	}

	if _, err := handler.Execute(envelope); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "duplicate.txt"), []byte("changed"), 0o640); err != nil {
		t.Fatal(err)
	}

	result, err := handler.Execute(envelope)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]string
	if err := json.Unmarshal(result, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["status"] != "duplicate_ignored" {
		t.Fatalf("expected duplicate_ignored, got: %s", result)
	}

	data, err := os.ReadFile(filepath.Join(root, "duplicate.txt"))
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != "changed" {
		t.Fatalf("duplicate task was executed again: %q", data)
	}
}

func TestWorkspaceHandlerPersistsProcessedTasks(t *testing.T) {
	root := t.TempDir()
	handler := NewWorkspaceHandler(root)
	envelope := TaskEnvelope{
		TaskID:   "persistent-1",
		TaskType: "workspace.write",
		Payload:  json.RawMessage(`{"path":"persistent.txt","content":"first"}`),
	}
	if _, err := handler.Execute(envelope); err != nil {
		t.Fatal(err)
	}

	reloaded := NewWorkspaceHandler(root)
	result, err := reloaded.Execute(envelope)
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]string
	if err := json.Unmarshal(result, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["status"] != "duplicate_ignored" {
		t.Fatalf("expected persisted duplicate handling, got: %s", result)
	}
}
