# Omniclient - AI Handoff and Architecture Guide

## Purpose

Omniclient is the headless CLI and worker component of Omninode. It has no Wails GUI and does not require desktop build tags or graphical dependencies.

It connects:

    User or AI agent <-> MCP stdio server <-> Omninode Gateway/Fabric
    Omniclient worker -> MQTT broker -> Gateway FastAPI -> Bento Box dashboard

The application supports:

1. MCP stdio mode, selected with `--mcp-stdio`.
2. Headless worker mode with periodic MQTT heartbeat messages.

The web UI is provided by the Node1 Gateway, not by Omniclient.

## Golden Rules

Follow these rules before modifying code:

1. Read this file completely.
2. Inspect existing definitions before adding new ones.
3. Do not duplicate structs.
4. Keep network code in `gateway_client.go`.
5. Keep MCP code in `mcp_server.go`.
6. Keep process startup and CLI argument handling in `main.go`.
7. Keep MQTT worker and heartbeat logic in its dedicated implementation file.
8. Do not add Wails, frontend bundlers, desktop tags, or GUI dependencies.
9. Do not assume that a gateway method exists. Verify its interface first.
10. Do not claim that a feature is operational until it has been tested.
11. Preserve ASCII-only documentation when editing handoff files.

## Core File Map

### main.go

Responsibilities:

- Define the package entrypoint.
- Parse command-line arguments.
- Start MCP stdio mode when `--mcp-stdio` is present.
- Start or supervise the headless worker and heartbeat loop otherwise.
- Send diagnostics to stderr so stdout remains available for MCP stdio.

Do not place MCP tool definitions, HTTP request code, or frontend code here.

### gateway_client.go

Responsibilities:

- Define the Gateway interface.
- Define transport-level result structures.
- Define `BrowseResult` and `ExecuteResult`.
- Define `HTTPGateway`.
- Implement or mock HTTP communication with the Omninode Gateway.
- Keep transport errors and HTTP details in this file.

Do not place MCP server registration or tool handlers here.

### mcp_server.go

Responsibilities:

- Define `OmninodeServer`.
- Define `OmninodeGateway`.
- Define MCP tool input and output structures.
- Define typed tool handlers.
- Register MCP tools.
- Define `StartMCPStdio`.

Do not redeclare `Gateway`, `ExecuteResult`, `BrowseResult`, or `HTTPGateway` here.

## MQTT Heartbeat Architecture

The headless worker announces its presence to the Gateway through MQTT.

Heartbeat topic:

    omninode/nodes/{node-id}/heartbeat

The `{node-id}` segment must identify the running client instance. The heartbeat payload should contain the node identity and operational information required by the Gateway, such as status, load, and timestamp, according to the current MQTT contract.

The Gateway FastAPI service consumes heartbeat messages, maintains the active-node view, and exposes the node state through its API. Nodes without a heartbeat for the configured TTL may be marked offline.

Typical local configuration:

- MQTT broker: `127.0.0.1:1883`
- Gateway: `http://127.0.0.1:8000`
- Gateway API key: `OMNINODE_API_KEY`

Do not invent MQTT payload fields or QoS requirements. Verify the current implementation and protocol definitions before changing the heartbeat contract.

## Gateway and Bento Box Dashboard

The Node1 Gateway is a FastAPI service listening on port 8000. It serves the official Bento Box dashboard directly:

    http://localhost:8000/

Relevant endpoints include:

- `GET /`: serves the dashboard.
- `GET /health`: Gateway health check.
- `GET /api/v1/nodes`: returns active nodes and requires the `x-omninode-key` header.
- `/static/*`: dashboard CSS and JavaScript assets.

The dashboard uses a dark responsive layout and displays:

- System connection status.
- Active nodes and their status/load.
- A command/chat area reserved for future Gateway or LLM integration.

The browser dashboard is not built or launched by Omniclient.

## MCP Tools

Current tools must be verified against `mcp_server.go` before changing documentation or behavior. Known tools include:

- `restart_node`
- `run_sandbox_code`
- `browse_webpage`
- `workspace.write`

Every tool must have:

- An input structure.
- An output structure.
- `json` and `jsonschema` tags where required by the SDK.
- One handler.
- One registration.
- Validation and error handling.
- Tests where practical.

## MCP Stdio Mode

Start the MCP server with:

    ./omniclient --mcp-stdio

On Windows PowerShell:

    .\omniclient.exe --mcp-stdio

MCP diagnostics must go to stderr. Do not write logs to stdout because stdout carries the MCP protocol stream.

Before relying on an SDK method or type, inspect the version in `go.mod` and confirm the API against the installed module.

## Build and Validation Workflow

From the `omniclient` directory:

    go version
    go mod tidy
    go build -o omniclient.exe .
    go test ./...

The build must work without `-tags desktop` and without Wails installed. There must be no dependency on `wails.json`, the Wails `frontend/` directory, or GUI initialization.

After every Go change:

1. Format changed Go files with `gofmt`.
2. Run `go build -o omniclient.exe .`.
3. Run `go test ./...`.
4. Inspect `git diff`.
5. Confirm no Wails imports remain.
6. Confirm stdout is reserved for MCP stdio in MCP mode.
7. Confirm documentation remains ASCII-only.

## Recommended Start Sequence

For local development:

1. Start the MQTT broker on `127.0.0.1:1883`.
2. Start the Gateway from `node1-gateway` with `python main.py`.
3. Build Omniclient with `go build -o omniclient.exe .`.
4. Start the headless worker and verify heartbeat reception.
5. Open `http://localhost:8000` and inspect Active Nodes.
6. Start `omniclient.exe --mcp-stdio` separately when an AI agent needs MCP access.

## Common Mistakes to Avoid

### Reintroducing Wails

Do not add:

- `github.com/wailsapp/wails/v2` imports.
- `wails.Run`.
- Wails asset embedding.
- `wails.json`.
- A Wails `frontend/` directory.
- Desktop-only build tags.

### Corrupting MCP stdio

Do not print diagnostic logs to stdout in `--mcp-stdio` mode. Use the standard logger configured for stderr.

### Unverified gateway assumptions

Do not assume:

- That a route exists.
- That an endpoint is HTTP rather than RPC.
- That a tool is available.
- That a language is supported.
- That a method exists on `Gateway`.
- That a heartbeat payload field is accepted.
- That a successful build proves runtime MQTT or MCP functionality.

## Required AI Handoff Response

After reading this file, report exactly:

    Handoff read.
    Go version: <version>
    MCP SDK version: <version>
    Build status: <pass or fail>
    Test status: <pass or fail>
    Wails dependency status: <removed or present>
    MQTT heartbeat status: <implemented, partial, or not verified>
    MCP stdio status: <real transport or temporary blocker>
    Gateway status: <mock, partial, or real>
    Core file to modify next: <file>
    Proposed next task: <task>
