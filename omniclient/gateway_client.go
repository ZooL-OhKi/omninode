package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// GatewayClient connects OmniClient to the Node1 Gateway REST API.
type GatewayClient struct {
	baseURL string
	apiKey  string
	http    *http.Client
}

func NewGatewayClientFromEnv() *GatewayClient {
	baseURL := strings.TrimRight(os.Getenv("OMNINODE_GATEWAY_URL"), "/")
	apiKey := os.Getenv("OMNINODE_API_KEY")
	if baseURL == "" || apiKey == "" {
		return nil
	}
	return &GatewayClient{
		baseURL: baseURL,
		apiKey:  apiKey,
		http:    &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *GatewayClient) request(method, path string, input any, output any) error {
	var body io.Reader
	if input != nil {
		encoded, err := json.Marshal(input)
		if err != nil {
			return err
		}
		body = bytes.NewReader(encoded)
	}

	req, err := http.NewRequest(method, c.baseURL+path, body)
	if err != nil {
		return err
	}
	req.Header.Set("X-Omninode-Key", c.apiKey)
	req.Header.Set("Accept", "application/json")
	if input != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		data, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return fmt.Errorf("gateway returned %s: %s", resp.Status, strings.TrimSpace(string(data)))
	}
	return json.NewDecoder(resp.Body).Decode(output)
}

func (c *GatewayClient) ListNodes() ([]NodeStatus, error) {
	var nodes []NodeStatus
	return nodes, c.request(http.MethodGet, "/nodes", nil, &nodes)
}

func (c *GatewayClient) GetNode(nodeID string) (NodeStatus, error) {
	var node NodeStatus
	return node, c.request(http.MethodGet, "/nodes/"+nodeID, nil, &node)
}

func (c *GatewayClient) DispatchTask(nodeID, taskType string, payload map[string]any) (map[string]any, error) {
	result := make(map[string]any)
	input := map[string]any{"task_type": taskType, "payload": payload}
	return result, c.request(http.MethodPost, "/nodes/"+nodeID+"/tasks", input, &result)
}

func (c *GatewayClient) FabricHealth() (map[string]any, error) {
	result := make(map[string]any)
	return result, c.request(http.MethodGet, "/fabric/health", nil, &result)
}
