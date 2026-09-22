# Omninode

Distributed computational node system with MCP (Model Context Protocol) interface.

---

## START HERE

**For AI and developers:** See `INDEX.md` in the root directory.

That file contains:
- Quick start guide
- Documentation index
- MCP SDK patterns
- Troubleshooting

---

## Project Structure

```
omninode/
├── INDEX.md              ← START HERE
├── README.md             ← This file
├── omniclient/           ← MCP client implementation
│   ├── HANDOFF.md        ← Complete guide (9.6KB)
│   ├── main.go
│   ├── mcp_server.go
│   ├── gateway_client.go
│   ├── go.mod
│   └── go.sum
└── .github/workflows/    ← CI/CD pipelines
```

---

## Quick Commands

```bash
# Setup
cd omniclient
go mod download
go mod verify
go build ./...

# Run
export OMNINODE_GATEWAY_URL="https://..."
export OMNINODE_API_KEY="..."
go run .
```

---

## Status

- **CI:** PASSING
- **Build:** STABLE
- **MCP SDK:** v1.8.1+

---

## Links

- Documentation: `INDEX.md`
- Complete Guide: `omniclient/HANDOFF.md`
- GitHub Actions: https://github.com/ZooL-OhKi/omninode/actions
- MCP SDK: https://github.com/modelcontextprotocol/go-sdk

---

MIT License
