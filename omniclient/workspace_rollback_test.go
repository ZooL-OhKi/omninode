package main

import (
	"errors"
	"os"
	"testing"
)

func TestWorkspaceRollbackPersistenceFailureReleasesMutex(t *testing.T) {
	h := NewWorkspaceHandler(t.TempDir())
	h.processed["failed-task"] = struct{}{}
	if err := os.MkdirAll(h.storePath, 0o750); err != nil {
		t.Fatal(err)
	}
	original := errors.New("execution failed")
	err := h.rollbackProcessed("failed-task", original)
	if !errors.Is(err, original) {
		t.Fatalf("original error lost: %v", err)
	}
	if err == original {
		t.Fatal("expected persistence failure context")
	}
	if !h.mu.TryLock() {
		t.Fatal("mutex remains locked after rollback persistence failure")
	}
	defer h.mu.Unlock()
	if _, exists := h.processed["failed-task"]; exists {
		t.Fatal("failed task remains in memory")
	}
}

func TestWorkspaceRollbackSuccessPreservesOriginalError(t *testing.T) {
	h := NewWorkspaceHandler(t.TempDir())
	h.processed["failed-task"] = struct{}{}
	original := errors.New("execution failed")
	if err := h.rollbackProcessed("failed-task", original); err != original {
		t.Fatalf("unexpected error: %v", err)
	}
	reloaded := NewWorkspaceHandler(h.root)
	if _, exists := reloaded.processed["failed-task"]; exists {
		t.Fatal("failed task remains in persistent store")
	}
	if !h.mu.TryLock() {
		t.Fatal("mutex remains locked after successful rollback")
	}
	h.mu.Unlock()
}
