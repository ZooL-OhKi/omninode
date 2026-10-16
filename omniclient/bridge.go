package main

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"
)

const (
	maxBridgeBodyBytes    = 1 << 20
	maxBridgeContentBytes = 512 << 10
	bridgeExecuteTimeout  = 10 * time.Second
)

var bridgeRequestIDPattern = regexp.MustCompile(`^[A-Za-z0-9._-]{8,128}$`)

type BridgeRequest struct {
	RequestID string `json:"request_id"`
	Path      string `json:"path"`
	Content   string `json:"content"`
}

type BridgeResponse struct {
	RequestID string          `json:"request_id"`
	Status    string          `json:"status"`
	Path      string          `json:"path"`
	Duplicate bool            `json:"duplicate,omitempty"`
	Result    json.RawMessage `json:"result,omitempty"`
}

type bridgeRecord struct {
	payloadHash string
	response    BridgeResponse
	statusCode  int
}

type BridgeService struct {
	workspace     *WorkspaceHandler
	token         string
	allowedOrigin string

	mu      sync.Mutex
	records map[string]bridgeRecord
}

func NewBridgeService(workspace *WorkspaceHandler, token, allowedOrigin string) (*BridgeService, error) {
	if workspace == nil {
		return nil, errors.New("workspace handler obbligatorio")
	}
	if len(token) < 32 {
		return nil, errors.New("token bridge troppo corto: usare almeno 32 caratteri")
	}
	allowedOrigin = strings.TrimSpace(allowedOrigin)
	if allowedOrigin == "" {
		return nil, errors.New("allowed origin obbligatorio")
	}
	return &BridgeService{
		workspace:     workspace,
		token:         token,
		allowedOrigin: allowedOrigin,
		records:       make(map[string]bridgeRecord),
	}, nil
}

func (b *BridgeService) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeBridgeError(w, http.StatusMethodNotAllowed, "metodo non consentito")
		return
	}
	if !isLoopbackRequest(r) {
		writeBridgeError(w, http.StatusForbidden, "host non consentito")
		return
	}
	if origin := r.Header.Get("Origin"); origin != "" && subtle.ConstantTimeCompare([]byte(origin), []byte(b.allowedOrigin)) != 1 {
		writeBridgeError(w, http.StatusForbidden, "origine non autorizzata")
		return
	}
	if !b.authorized(r) {
		writeBridgeError(w, http.StatusUnauthorized, "token di sessione non valido")
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, maxBridgeBodyBytes)
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	var req BridgeRequest
	if err := dec.Decode(&req); err != nil {
		writeBridgeError(w, http.StatusBadRequest, "payload JSON non valido o troppo grande")
		return
	}
	if err := validateBridgeRequest(req); err != nil {
		writeBridgeError(w, http.StatusBadRequest, err.Error())
		return
	}

	payloadHash := bridgePayloadHash(req)
	b.mu.Lock()
	if prior, exists := b.records[req.RequestID]; exists {
		b.mu.Unlock()
		if prior.payloadHash != payloadHash {
			writeBridgeError(w, http.StatusConflict, "request_id già usato con un payload diverso")
			return
		}
		duplicate := prior.response
		duplicate.Duplicate = true
		writeBridgeJSON(w, prior.statusCode, duplicate)
		return
	}
	b.mu.Unlock()

	result, err := b.execute(req)
	if err != nil {
		writeBridgeError(w, http.StatusBadRequest, err.Error())
		return
	}

	response := BridgeResponse{
		RequestID: req.RequestID,
		Status:    "written",
		Path:      req.Path,
		Result:    result,
	}
	b.mu.Lock()
	b.records[req.RequestID] = bridgeRecord{payloadHash: payloadHash, response: response, statusCode: http.StatusOK}
	b.mu.Unlock()
	writeBridgeJSON(w, http.StatusOK, response)
}

func (b *BridgeService) authorized(r *http.Request) bool {
	auth := r.Header.Get("Authorization")
	const prefix = "Bearer "
	if !strings.HasPrefix(auth, prefix) {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(strings.TrimPrefix(auth, prefix)), []byte(b.token)) == 1
}

func (b *BridgeService) execute(req BridgeRequest) (json.RawMessage, error) {
	if len(req.Content) > maxBridgeContentBytes {
		return nil, fmt.Errorf("contenuto oltre il limite di %d byte", maxBridgeContentBytes)
	}
	payload, err := json.Marshal(map[string]string{"path": req.Path, "content": req.Content})
	if err != nil {
		return nil, err
	}

	type execution struct {
		result json.RawMessage
		err    error
	}
	completed := make(chan execution, 1)
	go func() {
		result, err := b.workspace.write(payload)
		completed <- execution{result: result, err: err}
	}()

	select {
	case done := <-completed:
		return done.result, done.err
	case <-time.After(bridgeExecuteTimeout):
		return nil, errors.New("timeout esecuzione workspace.write")
	}
}

func validateBridgeRequest(req BridgeRequest) error {
	if !bridgeRequestIDPattern.MatchString(req.RequestID) {
		return errors.New("request_id non valido: usare 8-128 caratteri alfanumerici, punto, trattino o underscore")
	}
	if strings.TrimSpace(req.Path) == "" {
		return errors.New("path obbligatorio")
	}
	if req.Content == "" {
		return errors.New("content obbligatorio")
	}
	return nil
}

func bridgePayloadHash(req BridgeRequest) string {
	canonical, _ := json.Marshal(map[string]string{"path": req.Path, "content": req.Content})
	sum := sha256.Sum256(canonical)
	return fmt.Sprintf("%x", sum)
}

func isLoopbackRequest(r *http.Request) bool {
	host := r.Host
	if h, _, err := net.SplitHostPort(host); err == nil {
		host = h
	}
	if host == "localhost" {
		return true
	}
	ip := net.ParseIP(strings.Trim(host, "[]"))
	return ip != nil && ip.IsLoopback()
}

func writeBridgeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeBridgeError(w http.ResponseWriter, status int, message string) {
	writeBridgeJSON(w, status, map[string]string{"status": "error", "error": message})
}
