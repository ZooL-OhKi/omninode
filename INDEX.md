# Omninode Repository Index

**For AI and developers starting from zero**

---

## START HERE

**Main entry point:** `omniclient/HANDOFF.md`

This is the complete guide for understanding and working with this codebase.

---

## DOCUMENTATION FILES

### Root Level
- `INDEX.md` - This file (you are here)
- `README.md` - Project overview
- `omniclient/HANDOFF.md` - COMPLETE GUIDE (read this first)
- `omniclient/README.md` - Quick reference

### Key Files
- `omniclient/go.mod` - Dependencies (MCP SDK v1.8.1+)
- `omniclient/mcp_server.go` - MCP server implementation
- `omniclient/gateway_client.go` - Gateway API client
- `omniclient/main.go` - Entry point

---

## QUICK REFERENCE

### Setup (5 min)
```bash
cd omniclient
go mod download
go mod verify
go build ./...
```

### MCP SDK Patterns
- Server: `mcp.NewServer(&mcp.Implementation{Name: "...", Version: "..."}, nil)`
- Tools: `mcp.AddTool(server, &mcp.Tool{...}, handler)`
- Handler: `func(ctx, *mcp.CallToolRequest) (*mcp.CallToolResult, error)`
- Start: `server.Connect(ctx, &mcp.StdioTransport{}, nil)`

### Troubleshooting
- Checksum mismatch: `rm go.sum && go mod tidy && go mod verify`
- Old API errors: `go get github.com/modelcontextprotocol/go-sdk@main`

---

## STATUS

- **CI:** PASSING
- **Build:** STABLE
- **Last Update:** 2026-09-22

---

## LINKS

- GitHub: https://github.com/ZooL-OhKi/omninode
- Actions: https://github.com/ZooL-OhKi/omninode/actions
- MCP SDK: https://github.com/modelcontextprotocol/go-sdk

---

END OF INDEX
