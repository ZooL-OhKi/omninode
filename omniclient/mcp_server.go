package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// ============================================================================
// OMNINODE SERVER
// ============================================================================

type OmninodeServer struct {
	mcpServer   *mcp.Server
	gateway     *GatewayClient
	nodeStatus  map[string]NodeStatus
	statusMutex sync.RWMutex
}

type NodeStatus struct {
	ID       string         `json:"node_id"`
	Status   string         `json:"status"`
	Load     int            `json:"load"`
	LastSeen int64          `json:"last_seen"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// ============================================================================
// TOOL: run_sandbox_code
// ============================================================================

type RunSandboxCodeInput struct {
	Language string `json:"language" jsonschema:"required,enum=python,enum=javascript,enum=bash,description=Linguaggio di programmazione da usare per l'esecuzione"`
	Code     string `json:"code" jsonschema:"required,description=Codice sorgente completo da eseguire nella sandbox"`
}

type RunSandboxCodeOutput struct {
	Stdout   string `json:"stdout,omitempty"`
	Stderr   string `json:"stderr,omitempty"`
	ExitCode int    `json:"exit_code"`
	NodeID   string `json:"node_id"`
}

func (s *OmninodeServer) handleRunSandboxCode(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input RunSandboxCodeInput,
) (*mcp.CallToolResult, RunSandboxCodeOutput, error) {
	if input.Code == "" {
		return nil, RunSandboxCodeOutput{}, fmt.Errorf("code cannot be empty")
	}

	result, err := s.gateway.Execute(ctx, input.Language, input.Code)
	if err != nil {
		return nil, RunSandboxCodeOutput{}, fmt.Errorf("execution failed: %w", err)
	}

	output := RunSandboxCodeOutput{
		Stdout:   result.Stdout,
		Stderr:   result.Stderr,
		ExitCode: result.ExitCode,
		NodeID:   result.NodeID,
	}

	return nil, output, nil
}

// ============================================================================
// TOOL: list_nodes
// ============================================================================

type ListNodesInput struct{}

type ListNodesOutput struct {
	Nodes []NodeStatus `json:"nodes"`
}

func (s *OmninodeServer) handleListNodes(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input ListNodesInput,
) (*mcp.CallToolResult, ListNodesOutput, error) {
	if s.gateway != nil {
		nodes, err := s.gateway.ListNodes()
		if err != nil {
			return nil, ListNodesOutput{}, err
		}
		return nil, ListNodesOutput{Nodes: nodes}, nil
	}

	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()
	nodes := make([]NodeStatus, 0, len(s.nodeStatus))
	for _, node := range s.nodeStatus {
		nodes = append(nodes, node)
	}
	return nil, ListNodesOutput{Nodes: nodes}, nil
}

// ============================================================================
// TOOL: get_node_status
// ============================================================================

type GetNodeStatusInput struct {
	NodeID string `json:"node_id" jsonschema:"required,description=ID del nodo da interrogare"`
}

type GetNodeStatusOutput struct {
	NodeStatus
	Exists bool `json:"exists"`
}

func (s *OmninodeServer) handleGetNodeStatus(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input GetNodeStatusInput,
) (*mcp.CallToolResult, GetNodeStatusOutput, error) {
	if s.gateway != nil {
		node, err := s.gateway.GetNode(input.NodeID)
		if err != nil {
			return nil, GetNodeStatusOutput{Exists: false}, err
		}
		return nil, GetNodeStatusOutput{NodeStatus: node, Exists: true}, nil
	}

	node, exists := s.GetNodeStatus(input.NodeID)
	return nil, GetNodeStatusOutput{NodeStatus: node, Exists: exists}, nil
}

// ============================================================================
// TOOL: dispatch_task
// ============================================================================

type DispatchTaskInput struct {
	NodeID   string         `json:"node_id" jsonschema:"required,description=ID del nodo a cui dispatchare il task"`
	TaskType string         `json:"task_type" jsonschema:"required,description=Tipo di task da eseguire"`
	Payload  map[string]any `json:"payload" jsonschema:"required,description=Payload del task"`
}

type DispatchTaskOutput struct {
	Result map[string]any `json:"result"`
	NodeID string         `json:"node_id"`
}

func (s *OmninodeServer) handleDispatchTask(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input DispatchTaskInput,
) (*mcp.CallToolResult, DispatchTaskOutput, error) {
	if input.NodeID == "" {
		return nil, DispatchTaskOutput{}, fmt.Errorf("node_id is required")
	}
	if input.TaskType == "" {
		return nil, DispatchTaskOutput{}, fmt.Errorf("task_type is required")
	}
	if s.gateway == nil {
		return nil, DispatchTaskOutput{}, fmt.Errorf("gateway is not configured")
	}

	result, err := s.gateway.DispatchTask(input.NodeID, input.TaskType, input.Payload)
	if err != nil {
		return nil, DispatchTaskOutput{}, err
	}

	return nil, DispatchTaskOutput{Result: result, NodeID: input.NodeID}, nil
}

// ============================================================================
// TOOL: get_fabric_health
// ============================================================================

type GetFabricHealthInput struct{}

type GetFabricHealthOutput struct {
	TotalNodes   int    `json:"total_nodes"`
	OnlineNodes  int    `json:"online_nodes"`
	OfflineNodes int    `json:"offline_nodes"`
	AverageLoad  int    `json:"average_load"`
	HealthStatus string `json:"health_status"`
	Mode         string `json:"mode"`
}

func (s *OmninodeServer) handleGetFabricHealth(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input GetFabricHealthInput,
) (*mcp.CallToolResult, GetFabricHealthOutput, error) {
	if s.gateway != nil {
		health, err := s.gateway.FabricHealth()
		if err != nil {
			return nil, GetFabricHealthOutput{}, err
		}
		return nil, GetFabricHealthOutput{
			TotalNodes:   health["total_nodes"].(int),
			OnlineNodes:  health["online_nodes"].(int),
			OfflineNodes: health["offline_nodes"].(int),
			AverageLoad:  health["average_load"].(int),
			HealthStatus: health["health_status"].(string),
			Mode:         health["mode"].(string),
		}, nil
	}

	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()
	total, online, load := len(s.nodeStatus), 0, 0
	for _, node := range s.nodeStatus {
		if node.Status == "online" {
			online++
			load += node.Load
		}
	}
	averageLoad := 0
	if online > 0 {
		averageLoad = load / online
	}
	healthStatus := "healthy"
	if total > 0 && online == 0 {
		healthStatus = "critical"
	} else if averageLoad > 80 {
		healthStatus = "warning"
	}
	return nil, GetFabricHealthOutput{
		TotalNodes:   total,
		OnlineNodes:  online,
		OfflineNodes: total - online,
		AverageLoad:  averageLoad,
		HealthStatus: healthStatus,
		Mode:         "local-fallback",
	}, nil
}

// ============================================================================
// SERVER SETUP
// ============================================================================

func NewOmninodeServer() *OmninodeServer {
	s := &OmninodeServer{
		gateway:    NewGatewayClientFromEnv(),
		nodeStatus: make(map[string]NodeStatus),
	}

	s.mcpServer = mcp.NewServer(&mcp.Implementation{
		Name:    "omninode",
		Version: "0.1.0",
	}, nil)

	s.registerTools()
	return s
}

func (s *OmninodeServer) registerTools() {
	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "run_sandbox_code",
		Description: "Execute code in a sandboxed environment (Python, JavaScript, or Bash). Returns stdout, stderr, and exit code.",
	}, s.handleRunSandboxCode)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "list_nodes",
		Description: "List all connected Omninode nodes with their status",
	}, s.handleListNodes)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "get_node_status",
		Description: "Get status of a specific node",
	}, s.handleGetNodeStatus)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "dispatch_task",
		Description: "Dispatch a computation task to an online node",
	}, s.handleDispatchTask)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "get_fabric_health",
		Description: "Get overall health status of the Omninode fabric",
	}, s.handleGetFabricHealth)
}

func (s *OmninodeServer) StartMCPStdio() error {
	ctx := context.Background()
	_, err := s.mcpServer.Connect(ctx, &mcp.StdioTransport{}, nil)
	return err
}

// ============================================================================
// NODE STATUS HELPERS
// ============================================================================

func (s *OmninodeServer) UpdateNodeStatus(nodeID string, status NodeStatus) {
	s.statusMutex.Lock()
	defer s.statusMutex.Unlock()
	status.ID = nodeID
	s.nodeStatus[nodeID] = status
	log.Printf("updated local node %s: %s", nodeID, status.Status)
}

func (s *OmninodeServer) GetNodeStatus(nodeID string) (NodeStatus, bool) {
	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()
	status, exists := s.nodeStatus[nodeID]
	return status, exists
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

func toolResult(value any) (*mcp.CallToolResult, error) {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return nil, err
	}
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(data)},
		},
	}, nil
}
