package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type WorkspaceHandler struct {
	root string
}

func NewWorkspaceHandler(root string) *WorkspaceHandler {
	return &WorkspaceHandler{root: root}
}

func (h *WorkspaceHandler) Execute(envelope TaskEnvelope) (json.RawMessage, error) {
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
