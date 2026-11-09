package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

const (
	StatusPrepared                   = "prepared"
	StatusDispatchedInFlight         = "dispatched_in_flight"
	StatusCompleted                  = "completed"
	StatusFailed                     = "failed"
	StatusCrashUncertainHaltNoRetry  = "crash_uncertain_halt_no_retry"
)

// TaskRecord traccia lo stato di esecuzione locale di un task per garantire idempotenza.
type TaskRecord struct {
	TaskID string `json:"task_id"`
	Status string `json:"status"`
	Result string `json:"result,omitempty"`
}

// LocalIdempotencyStore gestisce un registro append-only/file-based sicuro per i task.
type LocalIdempotencyStore struct {
	mu    sync.Mutex
	path  string
	cache map[string]TaskRecord
}

// NewIdempotencyStore inizializza lo store di idempotenza nel workspace designato.
func NewIdempotencyStore(workspaceRoot string) (*LocalIdempotencyStore, error) {
	dir := filepath.Join(workspaceRoot, ".omninode")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return nil, err
	}
	storePath := filepath.Join(dir, "idempotency.json")
	store := &LocalIdempotencyStore{
		path:  storePath,
		cache: make(map[string]TaskRecord),
	}
	store.load()
	if err := store.RecoverInFlight(); err != nil {
		return nil, err
	}
	return store, nil
}

func (s *LocalIdempotencyStore) load() {
	s.mu.Lock()
	defer s.mu.Unlock()

	file, err := os.Open(s.path)
	if err != nil {
		return
	}
	defer file.Close()

	var records []TaskRecord
	if err := json.NewDecoder(file).Decode(&records); err == nil {
		for _, r := range records {
			s.cache[r.TaskID] = r
		}
	}
}

// Has verifica se un task è già stato registrato.
func (s *LocalIdempotencyStore) Has(taskID string) (bool, TaskRecord) {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec, exists := s.cache[taskID]
	return exists, rec
}

// Save registra atomicamente lo stato di un task.
func (s *LocalIdempotencyStore) Save(taskID, status, result string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.cache[taskID] = TaskRecord{
		TaskID: taskID,
		Status: status,
		Result: result,
	}
	return s.persistLocked()
}

// MarkDispatched persiste lo stato in-flight prima dell'effetto fisico.
func (s *LocalIdempotencyStore) MarkDispatched(taskID string) error {
	return s.Save(taskID, StatusDispatchedInFlight, "")
}

// RecoverInFlight trasforma ogni record in-flight al bootstrap in un arresto incerto.
func (s *LocalIdempotencyStore) RecoverInFlight() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	changed := false
	for id, r := range s.cache {
		if r.Status == StatusDispatchedInFlight {
			r.Status = StatusCrashUncertainHaltNoRetry
			s.cache[id] = r
			changed = true
		}
	}
	if !changed {
		return nil
	}
	return s.persistLocked()
}

func (s *LocalIdempotencyStore) persistLocked() error {
	var records []TaskRecord
	for _, r := range s.cache {
		records = append(records, r)
	}
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return err
	}
	tmpFile := s.path + ".tmp"
	if err := os.WriteFile(tmpFile, data, 0600); err != nil {
		return err
	}
	return os.Rename(tmpFile, s.path)
}
