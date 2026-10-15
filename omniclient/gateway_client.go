package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"time"
)

// ExecuteResult mappa la risposta di un nodo dopo aver eseguito codice
type ExecuteResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	NodeID   string `json:"node_id"`
}

// BrowseResult mappa la risposta di un nodo dopo aver esplorato una pagina web
type BrowseResult struct {
	Title   string `json:"title"`
	Content string `json:"content"`
	NodeID  string `json:"node_id"`
}

// DispatchResponse mappa la risposta 202 Accepted dal gateway
type DispatchResponse struct {
	Status      string `json:"status"`
	NodeID      string `json:"node_id"`
	TaskID      string `json:"task_id"`
	TaskType    string `json:"task_type"`
	Payload     any    `json:"payload"`
	SubmittedAt int64  `json:"submitted_at"`
}

// TaskStatus mappa lo stato di un task dal database SQLite
type TaskStatus struct {
	TaskID    string `json:"task_id"`
	TaskType  string `json:"task_type"`
	Payload   any    `json:"payload"`
	Status    string `json:"status"`
	Result    any    `json:"result"`
	Error     string `json:"error"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

// AutonomyRunStepRequest è il payload per un passo atomico di autonomia.
type AutonomyRunStepRequest struct {
	TargetFile   string   `json:"target_file"`
	Content      string   `json:"content"`
	ContextFiles []string `json:"context_files,omitempty"`
}

// Gateway definisce il contratto per parlare con il control plane di Omninode
type Gateway interface {
	RestartNode(nodeID string) error
	Execute(ctx context.Context, language, code string) (*ExecuteResult, error)
	Browse(ctx context.Context, url, format string) (*BrowseResult, error)
	DispatchTask(ctx context.Context, nodeID string, taskType string, payload map[string]any) (*DispatchResponse, error)
	GetTaskStatus(ctx context.Context, taskID string) (*TaskStatus, error)
	AutonomyRunStep(ctx context.Context, targetFile, content string, contextFiles []string) (map[string]any, error)
	WorkspaceList(ctx context.Context, subpath string) (map[string]any, error)
	WorkspaceRead(ctx context.Context, path string) (map[string]any, error)
	WorkspaceRollback(ctx context.Context, path string) (map[string]any, error)
	CommandVerify(ctx context.Context, preset string) (map[string]any, error)
}

// HTTPGateway è l'implementazione del client verso il cluster
type HTTPGateway struct {
	baseURL string
	client  *http.Client
	apiKey  string
}

// NewHTTPGateway crea un gateway con un client HTTP resiliente di default
func NewHTTPGateway(baseURL string) *HTTPGateway {
	defaultClient := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			Proxy: http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   5 * time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   5 * time.Second,
			ResponseHeaderTimeout: 10 * time.Second,
			IdleConnTimeout:       90 * time.Second,
		},
	}
	return NewHTTPGatewayWithClient(baseURL, defaultClient)
}

// NewHTTPGatewayWithClient permette di iniettare un client HTTP custom (es. per test)
func NewHTTPGatewayWithClient(baseURL string, client *http.Client) *HTTPGateway {
	return &HTTPGateway{
		baseURL: baseURL,
		client:  client,
		apiKey:  "", // API key verrà impostata separatamente
	}
}

// SetAPIKey configura l'API key per le richieste autenticate
func (g *HTTPGateway) SetAPIKey(apiKey string) {
	g.apiKey = apiKey
}

// doJSON è il motore di rete interno, testabile e agnostico rispetto agli endpoint reali
func (g *HTTPGateway) doJSON(ctx context.Context, method, path string, reqBody any, resBody any) error {
	fullURL := g.baseURL + path

	var bodyReader io.Reader
	if reqBody != nil {
		jsonData, err := json.Marshal(reqBody)
		if err != nil {
			return fmt.Errorf("errore serializzazione request: %w", err)
		}
		bodyReader = bytes.NewReader(jsonData)
	}

	req, err := http.NewRequestWithContext(ctx, method, fullURL, bodyReader)
	if err != nil {
		return fmt.Errorf("errore creazione request: %w", err)
	}

	req.Header.Set("Accept", "application/json")
	if reqBody != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if g.apiKey != "" {
		req.Header.Set("x-omninode-key", g.apiKey)
	}

	res, err := g.client.Do(req)
	if err != nil {
		return fmt.Errorf("errore esecuzione request: %w", err)
	}
	defer res.Body.Close()

	// Limita la lettura a 5MB per prevenire attacchi OOM su payload eccessivi
	limitedBody := io.LimitReader(res.Body, 5*1024*1024)

	if res.StatusCode < 200 || res.StatusCode >= 300 {
		errData, _ := io.ReadAll(limitedBody)
		return fmt.Errorf("HTTP %d: %s", res.StatusCode, string(bytes.TrimSpace(errData)))
	}

	if resBody != nil {
		if err := json.NewDecoder(limitedBody).Decode(resBody); err != nil {
			return fmt.Errorf("errore decodifica response: %w", err)
		}
	}

	return nil
}

// DispatchTask invia un task al gateway e riceve una risposta 202 Accepted con task_id
func (g *HTTPGateway) DispatchTask(ctx context.Context, nodeID string, taskType string, payload map[string]any) (*DispatchResponse, error) {
	reqBody := map[string]any{
		"task_type": taskType,
		"payload":   payload,
	}

	var res DispatchResponse
	err := g.doJSON(ctx, http.MethodPost, "/nodes/"+nodeID+"/tasks", reqBody, &res)
	if err != nil {
		return nil, err
	}

	return &res, nil
}

// GetTaskStatus interroga lo stato di un task dal database SQLite
func (g *HTTPGateway) GetTaskStatus(ctx context.Context, taskID string) (*TaskStatus, error) {
	var res TaskStatus
	err := g.doJSON(ctx, http.MethodGet, "/api/v1/tasks/"+taskID, nil, &res)
	if err != nil {
		return nil, err
	}

	return &res, nil
}

// AutonomyRunStep esegue un passo atomico write + verify_all + rollback on failure.
func (g *HTTPGateway) AutonomyRunStep(ctx context.Context, targetFile, content string, contextFiles []string) (map[string]any, error) {
	if targetFile == "" {
		return nil, fmt.Errorf("target_file è obbligatorio")
	}
	if content == "" {
		return nil, fmt.Errorf("content è obbligatorio")
	}

	var res map[string]any
	req := AutonomyRunStepRequest{
		TargetFile:   targetFile,
		Content:      content,
		ContextFiles: contextFiles,
	}
	if err := g.doJSON(ctx, http.MethodPost, "/api/v1/autonomy/run-step", req, &res); err != nil {
		return nil, err
	}
	return res, nil
}

// WorkspaceList elenca i file del workspace repository.
func (g *HTTPGateway) WorkspaceList(ctx context.Context, subpath string) (map[string]any, error) {
	var res map[string]any
	path := "/api/v1/autonomy/workspace/list"
	if subpath != "" {
		path += "?subpath=" + url.QueryEscape(subpath)
	}
	if err := g.doJSON(ctx, http.MethodGet, path, nil, &res); err != nil {
		return nil, err
	}
	return res, nil
}

// WorkspaceRead legge un file testuale dal workspace repository.
func (g *HTTPGateway) WorkspaceRead(ctx context.Context, path string) (map[string]any, error) {
	if path == "" {
		return nil, fmt.Errorf("path è obbligatorio")
	}
	var res map[string]any
	endpoint := "/api/v1/autonomy/workspace/read?path=" + url.QueryEscape(path)
	if err := g.doJSON(ctx, http.MethodGet, endpoint, nil, &res); err != nil {
		return nil, err
	}
	return res, nil
}

// WorkspaceRollback ripristina l’ultimo snapshot di un file.
func (g *HTTPGateway) WorkspaceRollback(ctx context.Context, path string) (map[string]any, error) {
	if path == "" {
		return nil, fmt.Errorf("path è obbligatorio")
	}
	var res map[string]any
	req := map[string]string{"path": path}
	if err := g.doJSON(ctx, http.MethodPost, "/api/v1/autonomy/workspace/rollback", req, &res); err != nil {
		return nil, err
	}
	return res, nil
}

// CommandVerify esegue esclusivamente un preset statico di verifica.
func (g *HTTPGateway) CommandVerify(ctx context.Context, preset string) (map[string]any, error) {
	if preset == "" {
		return nil, fmt.Errorf("preset è obbligatorio")
	}
	var res map[string]any
	req := map[string]string{"preset": preset}
	if err := g.doJSON(ctx, http.MethodPost, "/api/v1/autonomy/command/verify", req, &res); err != nil {
		return nil, err
	}
	return res, nil
}

// --- METODI PUBBLICI MOCKATI (IN ATTESA DI SPECIFICHE) ---

func (g *HTTPGateway) RestartNode(nodeID string) error {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return nil
}

func (g *HTTPGateway) Execute(ctx context.Context, language, code string) (*ExecuteResult, error) {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return &ExecuteResult{
		Stdout:   "Codice eseguito con successo sul nodo (Mock)",
		Stderr:   "",
		ExitCode: 0,
		NodeID:   "node-alpha-01",
	}, nil
}

func (g *HTTPGateway) Browse(ctx context.Context, pageURL, format string) (*BrowseResult, error) {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return &BrowseResult{
		Title:   "Pagina estratta da Omninode",
		Content: "# Contenuto Markdown (Mock)\nQuesto è il parsing di: " + pageURL,
		NodeID:  "node-browser-02",
	}, nil
}
