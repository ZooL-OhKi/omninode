# Omninode - Decentralized AI Compute Fabric

Omninode is a cloud-only decentralized and zero-cost system designed to
provide operational infrastructure for Artificial Intelligence systems.

The project allows AI systems to act in the digital world by using tools such
as web browsing and sandboxed code execution.

## Project Status

Current development is focused on the omniclient module:

    /omniclient

Omniclient is a hybrid application with two operating modes:

1. Graphical interface:
   Wails with Go and a web frontend.

2. MCP server:
   Exposes Omninode tools to local AI clients through the MCP stdio
   interface.

## Important Documentation Rule

Before changing code, read this file:

    omniclient/HANDOFF.md

The handoff describes the current architecture, file ownership rules, MCP
patterns, known limitations, and next tasks.

Do not invent new core structures before reading the handoff.

## Environment

- Go: 1.23 or later
- MCP SDK: github.com/modelcontextprotocol/go-sdk
- Wails: github.com/wailsapp/wails/v2
- Operating system: Windows, Linux, or macOS

## Core File Ownership

The core implementation is intentionally divided into three Go files:

- main.go
  Dual GUI and CLI entrypoint.

- gateway_client.go
  Network abstraction, Gateway interface, result structures, and
  HTTPGateway implementation.

- mcp_server.go
  MCP server, OmninodeGateway wrapper, tool input/output structures,
  handlers, tool registration, and MCP stdio startup.

Do not duplicate structures between these files.

Do not create additional Go files for core logic unless the architecture is
explicitly revised.

## Current Tools

The current MCP tools are:

- restart_node
- run_sandbox_code
- browse_webpage

The tool implementations use typed input and output structures and JSON
schema reflection through struct tags.

## Quick Start

From the repository root:

    cd omniclient
    go mod tidy
    go build -o omniclient
    .\omniclient.exe --mcp-stdio

For a normal Wails GUI launch:

    .\omniclient.exe

## Current Known Limitations

1. StartMCPStdio is currently held with a blocking select statement.
   It must be replaced with the correct MCP SDK stdio transport setup.

2. HTTPGateway is currently mocked or incomplete.
   Real HTTP or gRPC communication with the Omninode fabric still needs to
   be implemented.

3. The exact gateway API contract must be defined before replacing the mock
   implementation.

## Recommended Next Tasks

Work in this order:

1. Read omniclient/HANDOFF.md.
2. Verify the current build with go build ./....
3. Implement real MCP stdio transport in mcp_server.go.
4. Add tests for MCP startup and tool registration.
5. Define the gateway API contract.
6. Replace HTTPGateway stubs with real network calls.
7. Add integration tests using a local mock gateway.

## Validation Commands

    cd omniclient
    go mod tidy
    go build ./...
    go test ./...

Do not claim that MCP stdio is operational until the stdio transport has been
tested with an MCP client.

## Handoff Confirmation

After reading this file and omniclient/HANDOFF.md, report:

- the Go version;
- the MCP SDK version from go.mod;
- whether go build ./... passes;
- whether StartMCPStdio uses a real transport or a temporary blocker;
- which core file should be modified for the requested task.