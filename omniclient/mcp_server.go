package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "sync"

    "github.com/modelcontextprotocol/go-sdk/mcp"
)

// OmninodeServer exposes fabric capabilities through MCP.
type OmninodeServer struct {
    mcpServer   *mcp.Server
    gateway     *GatewayClient
    nodeStatus  map[string]NodeStatus
    statusMutex sync.RWMutex
}

// NodeStatus represents a distributed node state.
type NodeStatus struct {
    ID       string         `json:"node_id"`
    Status   string         `json:"status"`
    Load     int            `json:"load"`
    LastSeen int64          `json:"last_seen"`
    Metadata map[string]any `json:"metadata,omitempty"`
}

func NewOmninodeServer() *OmninodeServer {
    s := &OmninodeServer{
        gateway:    NewGatewayClientFromEnv(),
        nodeStatus: make(map[string]NodeStatus),
    }
    s.mcpServer = mcp.NewServer(&mcp.Implementation{Name: "omninode", Version: "0.1.0"}, nil)
    s.registerTools()
    return s
}

func (s *OmninodeServer) registerTools() {
    mcp.AddTool(s.mcpServer, &mcp.Tool{Name: "list_nodes", Description: "List all connected Omninode nodes with their status"}, s.handleListNodes)
    mcp.AddTool(s.mcpServer, &mcp.Tool{Name: "get_node_status", Description: "Get status of a specific node"}, s.handleGetNodeStatus)
    mcp.AddTool(s.mcpServer, &mcp.Tool{Name: "dispatch_task", Description: "Dispatch a computation task to an online node"}, s.handleDispatchTask)
    mcp.AddTool(s.mcpServer, &mcp.Tool{Name: "get_fabric_health", Description: "Get overall health status of the Omninode fabric"}, s.handleGetFabricHealth)
}

func toolResult(value any) (*mcp.CallToolResult, error) {
    data, err := json.MarshalIndent(value, "", "  ")
    if err != nil {
        return nil, err
    }
    return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: string(data)}}}, nil
}

func (s *OmninodeServer) handleListNodes(ctx context.Context, req *mcp.CallToolRequest, input any) (*mcp.CallToolResult, any, error) {
    if s.gateway != nil {
        nodes, err := s.gateway.ListNodes()
        if err != nil {
            return nil, nil, err
        }
        return toolResult(nodes)
    }
    s.statusMutex.RLock()
    defer s.statusMutex.RUnlock()
    nodes := make([]NodeStatus, 0, len(s.nodeStatus))
    for _, node := range s.nodeStatus {
        nodes = append(nodes, node)
    }
    return toolResult(nodes)
}

func (s *OmninodeServer) handleGetNodeStatus(ctx context.Context, req *mcp.CallToolRequest, input any) (*mcp.CallToolResult, any, error) {
    var args map[string]any
    if req.Params != nil && req.Params.Arguments != nil {
        if err := json.Unmarshal(req.Params.Arguments, &args); err != nil {
            return nil, nil, fmt.Errorf("invalid arguments: %w", err)
        }
    }
    nodeID, ok := args["node_id"].(string)
    if !ok || nodeID == "" {
        return nil, nil, fmt.Errorf("node_id is required")
    }
    if s.gateway != nil {
        node, err := s.gateway.GetNode(nodeID)
        if err != nil {
            return nil, nil, err
        }
        return toolResult(node)
    }
    node, exists := s.GetNodeStatus(nodeID)
    if !exists {
        return toolResult(map[string]string{"error": "node not found"})
    }
    return toolResult(node)
}

func (s *OmninodeServer) handleDispatchTask(ctx context.Context, req *mcp.CallToolRequest, input any) (*mcp.CallToolResult, any, error) {
    var args map[string]any
    if req.Params != nil && req.Params.Arguments != nil {
        if err := json.Unmarshal(req.Params.Arguments, &args); err != nil {
            return nil, nil, fmt.Errorf("invalid arguments: %w", err)
        }
    }
    nodeID, ok := args["node_id"].(string)
    if !ok || nodeID == "" {
        return nil, nil, fmt.Errorf("node_id is required")
    }
    taskType, ok := args["task_type"].(string)
    if !ok || taskType == "" {
        return nil, nil, fmt.Errorf("task_type is required")
    }
    payload, ok := args["payload"].(map[string]any)
    if !ok {
        return nil, nil, fmt.Errorf("payload must be an object")
    }
    if s.gateway == nil {
        return nil, nil, fmt.Errorf("gateway is not configured; set OMNINODE_GATEWAY_URL and OMNINODE_API_KEY")
    }
    result, err := s.gateway.DispatchTask(nodeID, taskType, payload)
    if err != nil {
        return nil, nil, err
    }
    return toolResult(result)
}

func (s *OmninodeServer) handleGetFabricHealth(ctx context.Context, req *mcp.CallToolRequest, input any) (*mcp.CallToolResult, any, error) {
    if s.gateway != nil {
        health, err := s.gateway.FabricHealth()
        if err != nil {
            return nil, nil, err
        }
        return toolResult(health)
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
    health := map[string]any{"total_nodes": total, "online_nodes": online, "offline_nodes": total - online, "average_load": averageLoad, "health_status": "healthy", "fabric_version": "0.1.0", "mode": "local-fallback"}
    if total > 0 && online == 0 {
        health["health_status"] = "critical"
    } else if averageLoad > 80 {
        health["health_status"] = "warning"
    }
    return toolResult(health)
}

func (s *OmninodeServer) StartMCPStdio() error {
    return s.mcpServer.Run(context.Background(), &mcp.StdioTransport{})
}

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
