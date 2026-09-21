# OmniClient

Desktop application for Omninode fabric, built with Go and Wails.

## Prerequisites

- Go 1.21+
- Node.js 18+
- Wails CLI (`go install github.com/wailsapp/wails/v2/cmd/wails@latest`)

## Development

```bash
wails dev
```

## Build

```bash
wails build
```

## Architecture

OmniClient connects to the Omninode fabric via MCP (Model Context Protocol) and provides:
- Local agent orchestration
- Zero-touch updates via GitHub Actions
- Distributed computation coordination

## MCP Server

OmniClient includes a built-in MCP server that exposes 4 tools to external AI agents:

| Tool | Description |
|------|-------------|
| `list_nodes` | List all connected nodes with status |
| `get_node_status` | Get detailed status of a specific node |
| `dispatch_task` | Dispatch computation task to a node |
| `get_fabric_health` | Get overall fabric health metrics |

### Running MCP Server

**GUI Mode (default):**
```bash
wails dev
# MCP SSE server runs on :8080
```

**Stdio Mode (for agent integration):**
```bash
./omniclient --mcp-stdio
# MCP server runs on stdin/stdout
```

## Testing MCP

### Python Test Client

```bash
# Install dependencies
pip install requests

# Run tests (stdio mode)
python test_mcp_client.py --stdio

# Run tests (SSE mode, requires wails dev running)
python test_mcp_client.py --sse
```

### AI Agent Integration

See [MCP_SETUP.md](MCP_SETUP.md) for configuration guides:
- Gemini Desktop
- Claude Desktop
- Cursor IDE
- Generic MCP clients

### Example: Gemini Desktop

1. Build OmniClient: `wails build`
2. Add to Gemini MCP config:
```json
{
  "mcpServers": {
    "omninode": {
      "command": "/path/to/omniclient",
      "args": ["--mcp-stdio"]
    }
  }
}
```
3. Ask Gemini: "Show me the Omninode fabric health"

## Project Structure

```
omniclient/
├── main.go              # Wails app + MCP integration
├── mcp_server.go        # MCP server implementation
├── go.mod               # Go module dependencies
├── wails.json           # Wails configuration
├── test_mcp_client.py   # Python test client
├── MCP_SETUP.md         # Agent configuration guide
└── README.md            # This file
```

## License

MIT
