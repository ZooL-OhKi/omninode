package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// OmninodeServer gestisce il MCP Server e la coordinazione dei nodi
type OmninodeServer struct {
	mcpServer   *mcp.Server
	nodeStatus  map[string]NodeStatus
	statusMutex sync.RWMutex
}

// NodeStatus rappresenta lo stato di un nodo distribuito
type NodeStatus struct {
	ID       string `json:"id"`
	Status   string `json:"status"` // "online", "offline", "busy"
	Load     int    `json:"load"`   // 0-100
	LastSeen int64  `json:"last_seen"`
}

// NewOmninodeServer crea un nuovo server Omninode con MCP integrato
func NewOmninodeServer() *OmninodeServer {
	s := &OmninodeServer{
		nodeStatus: make(map[string]NodeStatus),
	}

	// Configura il server MCP
	s.mcpServer = mcp.NewServer(&mcp.ServerOptions{
		Name:    "omninode",
		Version: "0.1.0",
	}, nil)

	// Registra i tools MCP esponibili agli agenti IA
	s.registerTools()

	return s
}

// registerTools registra i tools MCP disponibili
func (s *OmninodeServer) registerTools() {
	// Tool: list_nodes - Lista tutti i nodi connessi
	s.mcpServer.AddTool(&mcp.Tool{
		Name:        "list_nodes",
		Description: "List all connected Omninode nodes with their status",
		InputSchema: map[string]interface{}{},
	}, s.handleListNodes)

	// Tool: get_node_status - Ottieni stato di un nodo specifico
	s.mcpServer.AddTool(&mcp.Tool{
		Name:        "get_node_status",
		Description: "Get status of a specific node",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"node_id": map[string]interface{}{
					"type":        "string",
					"description": "The ID of the node to query",
				},
			},
			"required": []string{"node_id"},
		},
	}, s.handleGetNodeStatus)

	// Tool: dispatch_task - Invia un task a un nodo
	s.mcpServer.AddTool(&mcp.Tool{
		Name:        "dispatch_task",
		Description: "Dispatch a computation task to a node",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"node_id": map[string]interface{}{
					"type":        "string",
					"description": "Target node ID",
				},
				"task_type": map[string]interface{}{
					"type":        "string",
					"description": "Type of task (compute, query, transform)",
				},
				"payload": map[string]interface{}{
					"type":        "object",
					"description": "Task payload data",
				},
			},
			"required": []string{"node_id", "task_type", "payload"},
		},
	}, s.handleDispatchTask)

	// Tool: get_fabric_health - Ottieni salute complessiva del fabric
	s.mcpServer.AddTool(&mcp.Tool{
		Name:        "get_fabric_health",
		Description: "Get overall health status of the Omninode fabric",
		InputSchema: map[string]interface{}{},
	}, s.handleGetFabricHealth)
}

// handleListNodes gestisce la richiesta list_nodes
func (s *OmninodeServer) handleListNodes(ctx context.Context, params *mcp.ToolCallParams) (*mcp.ToolCallResult, error) {
	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()

	nodes := make([]NodeStatus, 0, len(s.nodeStatus))
	for _, node := range s.nodeStatus {
		nodes = append(nodes, node)
	}

	data, err := json.MarshalIndent(nodes, "", "  ")
	if err != nil {
		return nil, err
	}

	return &mcp.ToolCallResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}, nil
}

// handleGetNodeStatus gestisce la richiesta get_node_status
func (s *OmninodeServer) handleGetNodeStatus(ctx context.Context, params *mcp.ToolCallParams) (*mcp.ToolCallResult, error) {
	nodeID, ok := params.Arguments["node_id"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid node_id")
	}

	s.statusMutex.RLock()
	status, exists := s.nodeStatus[nodeID]
	s.statusMutex.RUnlock()

	if !exists {
		return &mcp.ToolCallResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf(`{"error": "Node %s not found"}`, nodeID)},
			},
		}, nil
	}

	data, err := json.MarshalIndent(status, "", "  ")
	if err != nil {
		return nil, err
	}

	return &mcp.ToolCallResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}, nil
}

// handleDispatchTask gestisce la richiesta dispatch_task
func (s *OmninodeServer) handleDispatchTask(ctx context.Context, params *mcp.ToolCallParams) (*mcp.ToolCallResult, error) {
	nodeID, _ := params.Arguments["node_id"].(string)
	taskType, _ := params.Arguments["task_type"].(string)
	payload := params.Arguments["payload"]

	// Qui si implementerebbe la logica reale di dispatch via MQTT/HTTP
	// Per ora simuliamo la risposta
	response := map[string]interface{}{
		"status":    "dispatched",
		"node_id":   nodeID,
		"task_type": taskType,
		"payload":   payload,
		"task_id":   fmt.Sprintf("task-%d", len(s.nodeStatus)),
	}

	data, err := json.MarshalIndent(response, "", "  ")
	if err != nil {
		return nil, err
	}

	return &mcp.ToolCallResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}, nil
}

// handleGetFabricHealth gestisce la richiesta get_fabric_health
func (s *OmninodeServer) handleGetFabricHealth(ctx context.Context, params *mcp.ToolCallParams) (*mcp.ToolCallResult, error) {
	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()

	total := len(s.nodeStatus)
	online := 0
	totalLoad := 0

	for _, node := range s.nodeStatus {
		if node.Status == "online" {
			online++
			totalLoad += node.Load
		}
	}

	avgLoad := 0
	if online > 0 {
		avgLoad = totalLoad / online
	}

	health := map[string]interface{}{
		"total_nodes":    total,
		"online_nodes":   online,
		"offline_nodes":  total - online,
		"average_load":   avgLoad,
		"health_status":  "healthy",
		"fabric_version": "0.1.0",
	}

	if online == 0 && total > 0 {
		health["health_status"] = "critical"
	} else if avgLoad > 80 {
		health["health_status"] = "warning"
	}

	data, err := json.MarshalIndent(health, "", "  ")
	if err != nil {
		return nil, err
	}

	return &mcp.ToolCallResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}, nil
}

// StartMCPStdio avvia il server MCP su stdio (per integrazione con agenti locali)
func (s *OmninodeServer) StartMCPStdio() error {
	log.Println("Starting MCP server on stdio...")
	return s.mcpServer.RunStdio(context.Background())
}

// StartMCPSSE avvia il server MCP su HTTP SSE (per integrazione remota)
func (s *OmninodeServer) StartMCPSSE(addr string) error {
	mux := http.NewServeMux()

	// Endpoint SSE per connessioni MCP
	mux.HandleFunc("/sse", func(w http.ResponseWriter, r *http.Request) {
		log.Println("New SSE connection")
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		// Qui si gestirebbe lo stream SSE reale
		for {
			select {
			case <-r.Context().Done():
				log.Println("SSE connection closed")
				return
			}
		}
	})

	log.Printf("Starting MCP SSE server on %s", addr)
	return http.ListenAndServe(addr, mux)
}

// UpdateNodeStatus aggiorna lo stato di un nodo (chiamato dal gateway MQTT)
func (s *OmninodeServer) UpdateNodeStatus(nodeID string, status NodeStatus) {
	s.statusMutex.Lock()
	defer s.statusMutex.Unlock()
	s.nodeStatus[nodeID] = status
	log.Printf("Updated node %s status: %s (load: %d%%)", nodeID, status.Status, status.Load)
}

// GetNodeStatus restituisce lo stato di un nodo specifico
func (s *OmninodeServer) GetNodeStatus(nodeID string) (NodeStatus, bool) {
	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()
	status, exists := s.nodeStatus[nodeID]
	return status, exists
}
