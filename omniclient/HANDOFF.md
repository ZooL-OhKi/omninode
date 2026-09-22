# Omninode MCP Client - Complete Handoff Guide

**For:** AI assistants and developers starting from zero
**Date:** 2026-09-22
**Status:** CI PASSING - Stable build
**Repo:** https://github.com/ZooL-OhKi/omninode
**Path:** omniclient/

---

## TABLE OF CONTENTS

1. Overview
2. Architecture
3. Quick Start (5 min)
4. Full Setup (step-by-step)
5. MCP SDK API Reference
6. Troubleshooting
7. Testing
8. Development Workflow

---

## 1. OVERVIEW

This is an MCP (Model Context Protocol) client for Omninode - a distributed
computational node system. It exposes 4 tools via MCP:

1. list_nodes - List all connected nodes
2. get_node_status - Get status of a specific node
3. dispatch_task - Dispatch computational tasks to nodes
4. get_fabric_health - Get overall fabric health

---

## 2. ARCHITECTURE

```
omniclient/
├── main.go              # Entry point, starts MCP stdio server
├── mcp_server.go        # MCP server with 4 registered tools
├── gateway_client.go    # HTTP client for Omninode Gateway API
├── go.mod               # Go dependencies (MCP SDK v1.8.1+)
├── go.sum               # Verified checksums
└── wails.json           # Wails config (hybrid UI)
```

### Key Dependencies

```
github.com/modelcontextprotocol/go-sdk v1.8.1+  # MCP SDK
github.com/wailsapp/wails/v2 v2.9.0             # UI framework
```

### Data Flow

```
MCP Client (LLM) <-> MCP Server (this code) <-> Gateway API <-> Nodes
```

---

## 3. QUICK START (5 MINUTES)

```bash
# 1. Clone
git clone https://github.com/ZooL-OhKi/omninode
cd omninode/omniclient

# 2. Dependencies
go mod download
go mod verify

# 3. Environment
export OMNINODE_GATEWAY_URL="https://gateway.omninode.io"
export OMNINODE_API_KEY="your-api-key"

# 4. Build and run
go build ./...
go run .
```

If it builds without errors, you're ready!

---

## 4. FULL SETUP (STEP-BY-STEP)

### Prerequisites

- Go 1.23 or later
- Git
- Access to Omninode Gateway (URL + API key)

### Step 1: Verify Go Version

```bash
go version
# Must be: go version go1.23.x or later
```

### Step 2: Clone Repository

```bash
git clone https://github.com/ZooL-OhKi/omninode
cd omninode/omniclient
```

### Step 3: Download Dependencies

```bash
go mod download
go mod verify
# Should output: all modules verified
```

### Step 4: Configure Environment

Create a .env file or export variables:

```bash
export OMNINODE_GATEWAY_URL="https://gateway.omninode.io"
export OMNINODE_API_KEY="your-api-key-here"
```

### Step 5: Build

```bash
go build ./...
# Should complete with no output (no errors)
```

### Step 6: Run

```bash
go run .
# Server starts, waits for MCP connections on stdio
```

### Step 7: Verify CI

Go to: https://github.com/ZooL-OhKi/omninode/actions

All checks should be green (passing).

---

## 5. MCP SDK API REFERENCE

### 5.1 Creating MCP Server

```go
import "github.com/modelcontextprotocol/go-sdk/mcp"

s.mcpServer = mcp.NewServer(&mcp.Implementation{
    Name:    "omninode",
    Version: "0.1.0",
}, nil)
```

**Key points:**
- Use `&mcp.Implementation{}` (NOT `&mcp.ServerOptions{}`)
- Second parameter is `nil` for default config

### 5.2 Registering Tools

```go
mcp.AddTool(s.mcpServer, &mcp.Tool{
    Name:        "list_nodes",
    Description: "List all connected nodes",
    InputSchema: json.RawMessage(`{"type":"object"}`),
}, s.handleListNodes)
```

**Key points:**
- Use `mcp.AddTool(server, &Tool{...}, handler)` (package function)
- InputSchema: use `json.RawMessage(...)` with JSON string
- Handler: method on your server struct

### 5.3 Handler Signature

```go
func (s *OmninodeServer) handleListNodes(
    ctx context.Context,
    req *mcp.CallToolRequest,
) (*mcp.CallToolResult, error) {
    // Parse arguments from req.Params.Arguments (json.RawMessage)
    var args struct {
        NodeID string `json:"node_id"`
    }
    if err := json.Unmarshal(req.Params.Arguments, &args); err != nil {
        return nil, err
    }
    
    // Your logic here
    result := map[string]any{"nodes": []string{"node1", "node2"}}
    
    // Return result
    return &mcp.CallToolResult{
        Content: []mcp.Content{
            &mcp.TextContent{Text: string(mustJSON(result))},
        },
    }, nil
}
```

**Key points:**
- Signature: `func(context.Context, *mcp.CallToolRequest) (*mcp.CallToolResult, error)`
- Arguments: `req.Params.Arguments` is `json.RawMessage`
- Return: `*mcp.CallToolResult` with `Content` slice

### 5.4 Starting Server

```go
func (s *OmninodeServer) StartMCPStdio() error {
    ctx := context.Background()
    _, err := s.mcpServer.Connect(ctx, &mcp.StdioTransport{}, nil)
    return err
}
```

**Key points:**
- Use `Connect(ctx, transport, nil)` (3 parameters)
- Transport: `&mcp.StdioTransport{}` for stdio

### 5.5 Complete Example (mcp_server.go)

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "sync"
    "github.com/modelcontextprotocol/go-sdk/mcp"
)

type OmninodeServer struct {
    mcpServer   *mcp.Server
    gateway     *GatewayClient
    nodeStatus  map[string]NodeStatus
    statusMutex sync.RWMutex
}

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
        Name:        "list_nodes",
        Description: "List all connected nodes",
        InputSchema: json.RawMessage(`{"type":"object"}`),
    }, s.handleListNodes)
    
    // Add more tools...
}

func (s *OmninodeServer) handleListNodes(
    ctx context.Context,
    req *mcp.CallToolRequest,
) (*mcp.CallToolResult, error) {
    nodes, err := s.gateway.ListNodes()
    if err != nil {
        return nil, err
    }
    return toolResult(nodes)
}

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

func (s *OmninodeServer) StartMCPStdio() error {
    ctx := context.Background()
    _, err := s.mcpServer.Connect(ctx, &mcp.StdioTransport{}, nil)
    return err
}
```

---

## 6. TROUBLESHOOTING

### Checksum Mismatch

**Error:**
```
verifying github.com/modelcontextprotocol/go-sdk@v1.0.0: checksum mismatch
downloaded: h1:Z4MSjLi38bTgLrd/LjSmofqRqyBiVKRyQSJgw8q8V74=
go.sum:     h1:PESNYOmyM1c369tRkzXLY5hHrazj8x9CY1Xu0fLCryM=
```

**Fix:**
```bash
rm go.sum
go mod tidy
go mod verify
git add go.sum
git commit -m "Fix go.sum checksums"
git push
```

### Build Errors - Unknown Field

**Error:**
```
unknown field Name in struct literal of type mcp.ServerOptions
```

**Cause:** Using old API (v0.2.0 or earlier)

**Fix:**
```bash
go get github.com/modelcontextprotocol/go-sdk@main
go mod tidy
go build ./...
```

### Build Errors - Undefined Type

**Error:**
```
undefined: mcp.CallToolRequest
```

**Cause:** Old SDK version

**Fix:**
```bash
go get github.com/modelcontextprotocol/go-sdk@main
go mod tidy
```

### CI Fails on go mod verify

**Local test:**
```bash
go clean -modcache
go mod download
go mod verify
```

If local passes but CI fails:
```bash
git add go.mod go.sum
git commit -m "Update go.sum with verified checksums"
git push
```

### Common Compilation Errors Table

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown field Name in mcp.ServerOptions` | Old API | Use `&mcp.Implementation{Name: ...}` |
| `cannot use map[string]any as *jsonschema.Schema` | Wrong InputSchema | Use `json.RawMessage(...)` |
| `undefined: mcp.CallToolRequest` | Old SDK | Upgrade to v1.8.1+ |
| `too many arguments in call to Connect` | Wrong signature | `Connect(ctx, transport, nil)` |

---

## 7. TESTING

### Test with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run your server
go run .

# In another terminal
mcp-inspector
# Connect to stdio: go run .
```

### Test with Python Script

```python
import subprocess
import json

proc = subprocess.Popen(
    ["go", "run", "."],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "list_nodes",
        "arguments": {}
    }
}

proc.stdin.write(json.dumps(request) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print(response)
```

### Unit Tests

```bash
go test ./... -v
```

---

## 8. DEVELOPMENT WORKFLOW

### 1. Make Changes

```bash
vim mcp_server.go
# or your preferred editor
```

### 2. Build and Test Locally

```bash
go build ./...
go run .  # Verify it starts without panic
```

### 3. Commit and Push

```bash
git add .
git commit -m "Clear description of changes"
git push origin main
```

### 4. Verify CI

Go to: https://github.com/ZooL-OhKi/omninode/actions

Wait for all checks to turn green.

---

## CURRENT STATE

**Last Commit:** c96c977 - "Fix MCP SDK compatibility - upgrade to latest version"
**CI Status:** PASSING
**Build Status:** STABLE
**MCP SDK Version:** v1.8.1-0.20260921161013-07e46a2864f7

---

## RESOURCES

- MCP SDK Go: https://github.com/modelcontextprotocol/go-sdk
- MCP Spec: https://modelcontextprotocol.io
- Examples: https://github.com/modelcontextprotocol/go-sdk/tree/main/mcp
- Wails: https://wails.io

---

END OF HANDOFF
