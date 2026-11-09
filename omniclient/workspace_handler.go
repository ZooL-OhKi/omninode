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
	h := &WorkspaceHandler{root: root, processed: make(map[string]struct{}), storePath: filepath.Join(root, ".omninode", "processed-tasks.json")}
	h.loadProcessed()
	return h
}

func (h *WorkspaceHandler) loadProcessed() {
	data, err := os.ReadFile(h.storePath)
	if err != nil { return }
	var ids []string
	if json.Unmarshal(data, &ids) != nil { return }
	for _, id := range ids { h.processed[id] = struct{}{} }
}

func (h *WorkspaceHandler) saveProcessed() error {
	if err := os.MkdirAll(filepath.Dir(h.storePath), 0o750); err != nil { return err }
	ids := make([]string, 0, len(h.processed))
	for id := range h.processed { ids = append(ids, id) }
	data, err := json.Marshal(ids)
	if err != nil { return err }
	return os.WriteFile(h.storePath, data, 0o600)
}

func (h *WorkspaceHandler) rollbackProcessed(taskID string, executionErr error) error {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.processed, taskID)
	if saveErr := h.saveProcessed(); saveErr != nil {
		return fmt.Errorf("rollback idempotenza non riuscito: %v; errore originale: %w", saveErr, executionErr)
	}
	return executionErr
}

func (h *WorkspaceHandler) Execute(envelope TaskEnvelope) (json.RawMessage, error) {
	if envelope.TaskID == "" { return nil, errors.New("task_id mancante") }
	h.mu.Lock()
	if _, exists := h.processed[envelope.TaskID]; exists {
		h.mu.Unlock()
		return json.Marshal(map[string]string{"task_id": envelope.TaskID, "status": "duplicate_ignored"})
	}
	h.processed[envelope.TaskID] = struct{}{}
	if err := h.saveProcessed(); err != nil {
		delete(h.processed, envelope.TaskID)
		h.mu.Unlock()
		return nil, fmt.Errorf("persistenza idempotenza non riuscita: %w", err)
	}
	h.mu.Unlock()
	result, err := h.execute(envelope)
	if err != nil { return nil, h.rollbackProcessed(envelope.TaskID, err) }
	return result, nil
}

func (h *WorkspaceHandler) execute(envelope TaskEnvelope) (json.RawMessage, error) {
	switch envelope.TaskType {
	case "workspace.write": return h.write(envelope.Payload)
	default: return nil, fmt.Errorf("task_type non supportato: %s", envelope.TaskType)
	}
}

func (h *WorkspaceHandler) write(payload json.RawMessage) (json.RawMessage, error) {
	var request struct {
		Path string `json:"path"`
		Content string `json:"content"`
	}
	if err := json.Unmarshal(payload, &request); err != nil {
		return nil, fmt.Errorf("payload workspace.write non valido: %w", err)
	}
	portable := strings.ReplaceAll(request.Path, "\\", "/")
	if strings.TrimSpace(portable) == "" || strings.ContainsAny(portable, "\x00:") {
		return nil, errors.New("percorso non valido")
	}
	for _, part := range strings.Split(portable, "/") {
		if part == ".." || strings.EqualFold(strings.TrimRight(part, " ."), ".omninode") {
			return nil, errors.New("percorso riservato o non consentito")
		}
	}
	name := filepath.FromSlash(portable)
	if !filepath.IsLocal(name) || filepath.Clean(name) == "." {
		return nil, errors.New("percorso fuori dal workspace consentito")
	}
	root, err := os.OpenRoot(h.root)
	if err != nil { return nil, err }
	defer root.Close()
	if err := root.MkdirAll(filepath.Dir(name), 0o750); err != nil { return nil, err }
	file, err := root.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o640)
	if err != nil { return nil, fmt.Errorf("creazione esclusiva non riuscita: %w", err) }
	_, writeErr := file.WriteString(request.Content)
	if writeErr == nil { writeErr = file.Sync() }
	closeErr := file.Close()
	if writeErr != nil { return nil, fmt.Errorf("scrittura incompleta; file conservato senza retry automatico: %w", writeErr) }
	if closeErr != nil { return nil, closeErr }
	return json.Marshal(map[string]string{"path": request.Path, "status": "written"})
}
