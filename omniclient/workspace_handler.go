package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

type WorkspaceHandler struct {
	root string
	mu sync.Mutex
	processed map[string]struct{}
	storePath string
}

func NewWorkspaceHandler(root string) *WorkspaceHandler {
	handler := &WorkspaceHandler{
		root: root,
		processed: make(map[string]struct{}),
		storePath: filepath.Join(root, ".omninode", "processed-tasks.json"),
	}
	handler.loadProcessed()
	return handler
}

func (h *WorkspaceHandler) loadProcessed() {
	data, err := os.ReadFile(h.storePath)
	if err != nil {
		return
	}
	var ids []string
	if json.Unmarshal(data, &ids) != nil {
		return
	}
	for _, id := range ids {
		h.processed[id] = struct{}{}
	}
}

func (h *WorkspaceHandler) saveProcessed() error {
	if err := os.MkdirAll(filepath.Dir(h.storePath), 0o750); err != nil {
		return err
	}
	ids := make([]string, 0, len(h.processed))
	for id := range h.processed {
		ids = append(ids, id)
	}
	data, err := json.Marshal(ids)
	if err != nil {
		return err
	}
	return os.WriteFile(h.storePath, data, 0o600)
}

func (h *WorkspaceHandler) Execute(envelope TaskEnvelope) (json.RawMessage, error) {
	if envelope.TaskID == "" {
		return nil, errors.New("task_id mancante")
	}

	h.mu.Lock()
	if _, exists := h.processed[envelope.TaskID]; exists {
		h.mu.Unlock()
		return json.Marshal(map[string]string{
			"task_id": envelope.TaskID,
			"status": "duplicate_ignored",
		})
	}
	h.processed[envelope.TaskID] = struct{}{}
	if err := h.saveProcessed(); err != nil {
		delete(h.processed, envelope.TaskID)
		h.mu.Unlock()
		return nil, fmt.Errorf("persistenza idempotenza non riuscita: %w", err)
	}
	h.mu.Unlock()

	result, err := h.execute(envelope)
	if err != nil {
		h.mu.Lock()
		delete(h.processed, envelope.TaskID)
		if saveErr := h.saveProcessed(); saveErr != nil {
			return nil, fmt.Errorf("rollback idempotenza non riuscito: %v; errore originale: %w", saveErr, err)
		}
		h.mu.Unlock()
		return nil, err
	}
	return result, nil
}

func (h *WorkspaceHandler) execute(envelope TaskEnvelope) (json.RawMessage, error) {
	switch envelope.TaskType {
	case "workspace.write":
		return h.write(envelope.Payload)
	default:
		return nil, fmt.Errorf("task_type non supportato: %s", envelope.TaskType)
	}
}

func (h *WorkspaceHandler) write(payload json.RawMessage) (json.RawMessage, error) {
	var request struct {
		Path    string `json:"path"`
		Content string `json:"content"`
	}
	if err := json.Unmarshal(payload, &request); err != nil {
		return nil, fmt.Errorf("payload workspace.write non valido: %w", err)
	}
	if strings.Contains(request.Path, "\x00") {
		return nil, errors.New("percorso non valido")
	}

	target := filepath.Join(h.root, filepath.FromSlash(request.Path))
	cleanRoot, err := filepath.Abs(h.root)
	if err != nil {
		return nil, err
	}
	cleanTarget, err := filepath.Abs(target)
	if err != nil {
		return nil, err
	}
	rel, err := filepath.Rel(cleanRoot, cleanTarget)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return nil, errors.New("percorso fuori dal workspace consentito")
	}

	if err := os.MkdirAll(filepath.Dir(cleanTarget), 0o750); err != nil {
		return nil, err
	}
	if err := os.WriteFile(cleanTarget, []byte(request.Content), 0o640); err != nil {
		return nil, err
	}
	return json.Marshal(map[string]string{"path": request.Path, "status": "written"})
}
