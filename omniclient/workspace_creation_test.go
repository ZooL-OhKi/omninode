package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func creationPayload(path, content string) json.RawMessage {
	data, _ := json.Marshal(map[string]string{"path": path, "content": content})
	return data
}

func TestWorkspaceCreateRejectsOverwrite(t *testing.T) {
	root := t.TempDir()
	h := NewWorkspaceHandler(root)
	if _, err := h.Execute(TaskEnvelope{TaskID: "first", TaskType: "workspace.write", Payload: creationPayload("note.txt", "original")}); err != nil { t.Fatal(err) }
	if _, err := h.Execute(TaskEnvelope{TaskID: "second", TaskType: "workspace.write", Payload: creationPayload("note.txt", "replacement")}); err == nil { t.Fatal("overwrite accepted") }
	data, err := os.ReadFile(filepath.Join(root, "note.txt"))
	if err != nil || string(data) != "original" { t.Fatalf("original changed: %q, %v", data, err) }
}

func TestWorkspaceCreateRejectsReservedAndInvalidPaths(t *testing.T) {
	for _, path := range []string{"", ".", "../escape.txt", "..\\escape.txt", "/absolute.txt", "C:\\outside.txt", "file.txt:stream", ".omninode/processed-tasks.json", ".OMNINODE/new.txt", ".omninode./new.txt"} {
		t.Run(path, func(t *testing.T) {
			h := NewWorkspaceHandler(t.TempDir())
			if _, err := h.write(creationPayload(path, "denied")); err == nil { t.Fatalf("accepted invalid path %q", path) }
		})
	}
}

func TestWorkspaceCreateRejectsSymlinkEscape(t *testing.T) {
	root, outside := t.TempDir(), t.TempDir()
	if err := os.Symlink(outside, filepath.Join(root, "escape")); err != nil { t.Skipf("symlink unavailable: %v", err) }
	h := NewWorkspaceHandler(root)
	if _, err := h.write(creationPayload("escape/new.txt", "denied")); err == nil { t.Fatal("symlink escape accepted") }
	if _, err := os.Stat(filepath.Join(outside, "new.txt")); !os.IsNotExist(err) { t.Fatalf("outside file state: %v", err) }
}
