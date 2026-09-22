package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// GatewayClient client HTTP per Omninode Gateway
type GatewayClient struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
}

// ExecuteResult risultato dell'esecuzione codice in sandbox
type ExecuteResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	NodeID   string `json:"node_id"`
}

// NewGatewayClientFromEnv crea client da variabili ambiente
func NewGatewayClientFromEnv() *GatewayClient {
	baseURL := os.Getenv("OMNINODE_GATEWAY_URL")
	if baseURL == "" {
		baseURL = "http://localhost:8080"
	}
	apiKey := os.Getenv("OMNINODE_API_KEY")
	return &GatewayClient{
		baseURL: baseURL,
		apiKey:  apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Execute esegue codice in sandbox su un nodo remoto
func (g *GatewayClient) Execute(ctx context.Context, language, code string) (*ExecuteResult, error) {
	payload := map[string]string{
		"language": language,
		"code":     code,
	}

	resp, err := g.doRequest(ctx, "POST", "/api/v1/execute", payload)
	if err != nil {
		return nil, err
	}

	var result ExecuteResult
	if err := json.Unmarshal(resp, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal execute response: %w", err)
	}

	return &result, nil
}

// ListNodes lista tutti i nodi connessi
func (g *GatewayClient) ListNodes() ([]NodeStatus, error) {
	resp, err := g.doRequest(context.Background(), "GET", "/api/v1/nodes", nil)
	if err != nil {
		return nil, err
	}

	var nodes []NodeStatus
	if err := json.Unmarshal(resp, &nodes); err != nil {
		return nil, fmt.Errorf("failed to unmarshal nodes response: %w", err)
	}

	return nodes, nil
}

// GetNode ottiene lo stato di un nodo specifico
func (g *GatewayClient) GetNode(nodeID string) (NodeStatus, error) {
	resp, err := g.doRequest(context.Background(), "GET", fmt.Sprintf("/api/v1/nodes/%s", nodeID), nil)
	if err != nil {
		return NodeStatus{}, err
	}

	var node NodeStatus
	if err := json.Unmarshal(resp, &node); err != nil {
		return NodeStatus{}, fmt.Errorf("failed to unmarshal node response: %w", err)
	}

	return node, nil
}

// DispatchTask dispatcha un task a un nodo
func (g *GatewayClient) DispatchTask(nodeID, taskType string, payload map[string]any) (map[string]any, error) {
	body := map[string]any{
		"task_type": taskType,
		"payload":   payload,
	}

	resp, err := g.doRequest(context.Background(), "POST", fmt.Sprintf("/api/v1/nodes/%s/tasks", nodeID), body)
	if err != nil {
		return nil, err
	}

	var result map[string]any
	if err := json.Unmarshal(resp, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal task response: %w", err)
	}

	return result, nil
}

// FabricHealth ottiene la salute del fabric
func (g *GatewayClient) FabricHealth() (map[string]any, error) {
	resp, err := g.doRequest(context.Background(), "GET", "/api/v1/health", nil)
	if err != nil {
		return nil, err
	}

	var health map[string]any
	if err := json.Unmarshal(resp, &health); err != nil {
		return nil, fmt.Errorf("failed to unmarshal health response: %w", err)
	}

	return health, nil
}

// doRequest esegue una request HTTP con auth
func (g *GatewayClient) doRequest(ctx context.Context, method, path string, body any) ([]byte, error) {
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewReader(jsonBody)
	}

	url := g.baseURL + path
	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if g.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+g.apiKey)
	}

	resp, err := g.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("gateway error %d: %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}
