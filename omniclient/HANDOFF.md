# Omniclient - AI Handoff and Architecture Guide

## Purpose

Omniclient is the desktop and CLI component of Omninode.

It connects:

    User <-> Local AI client <-> MCP server <-> Omninode fabric

The application has two modes:

1. Wails GUI mode.
2. MCP stdio server mode, selected with:

       --mcp-stdio

The objective is to expose practical tools that allow an AI system to work
with the distributed Omninode fabric.

## Golden Rules

Follow these rules before modifying code:

1. Read this file completely.
2. Inspect the existing definitions before adding new ones.
3. Do not duplicate structs.
4. Do not create additional Go files for core logic.
5. Keep network code in gateway_client.go.
6. Keep MCP code in mcp_server.go.
7. Keep process startup and Wails setup in main.go.
8. Do not assume that a gateway method exists. Verify its interface first.
9. Do not claim that a feature is operational until it has been tested.
10. Preserve ASCII-only documentation when editing handoff files.

## Core File Map

### main.go

Responsibilities:

- Define the package entrypoint.
- Parse command-line arguments.
- Start MCP stdio mode when --mcp-stdio is present.
- Start the Wails GUI otherwise.
- Connect GUI-facing objects to the gateway abstraction.
- Call FabricHealth only through the gateway interface exposed by the
  current architecture.

Do not place MCP tool definitions or HTTP request code here.

### gateway_client.go

Responsibilities:

- Define the Gateway interface.
- Define transport-level result structures.
- Define BrowseResult and ExecuteResult.
- Define HTTPGateway.
- Implement or mock network communication with the Omninode fabric.
- Keep transport errors and HTTP details in this file.

Do not place MCP server registration or tool handlers here.

The current architecture expects definitions similar to:

    type Gateway interface {
        ...
    }

    type ExecuteResult struct {
        ...
    }

    type BrowseResult struct {
        ...
    }

    type HTTPGateway struct {
        ...
    }

Verify the exact current definitions before using or extending them.

### mcp_server.go

Responsibilities:

- Define OmninodeServer.
- Define OmninodeGateway.
- Define MCP tool input structures.
- Define MCP tool output structures.
- Define typed tool handlers.
- Register MCP tools.
- Define StartMCPStdio.

Current tool handlers:

- handleRestartNode
- handleRunSandboxCode
- handleBrowseWebpage

Do not redeclare Gateway, ExecuteResult, BrowseResult, or HTTPGateway here.

## Current MCP Tools

### restart_node

Purpose:

- Request a node restart through the gateway.

Input:

- node_id

Expected behavior:

- Validate the node identifier.
- Call the gateway restart operation.
- Return a typed result.
- Propagate gateway errors.

### run_sandbox_code

Purpose:

- Execute code on a selected Omninode sandbox.

Expected input fields include:

- language
- code

Supported languages must be confirmed from the current implementation and
gateway contract. Do not assume a language is supported merely because it
appears in documentation.

Expected output fields include:

- stdout
- stderr
- exit_code
- node_id

The handler must pass the request context to the gateway.

### browse_webpage

Purpose:

- Request web page browsing or retrieval through the gateway.

Expected input and output structures are defined in the current source.
Read those definitions before changing the tool.

The implementation should preserve:

- URL validation;
- request context propagation;
- gateway error propagation;
- typed output;
- safe limits on response size and execution time.

## MCP SDK Pattern

The project uses the official Go MCP SDK.

Before relying on a method or type, inspect the version in go.mod and confirm
the API against the installed module.

### Server Construction

The intended pattern is:

    server := mcp.NewServer(
        &mcp.Implementation{
            Name:    "omninode-client",
            Version: "v1.0.0",
        },
        nil,
    )

Use the exact constructor signature provided by the installed SDK version.

### Typed Tool Structures

Use Go structures for tool input and output.

Example:

    type ExampleInput struct {
        Value string `json:"value" jsonschema:"required,description=Input value"`
    }

Do not manually create JSON schema maps unless the installed SDK requires it
for a specific API that cannot use reflection.

Use json tags for wire format and jsonschema tags for schema generation.

### Typed Handler Shape

The intended pattern is:

    func (
        s *OmninodeServer,
    ) handleExample(
        ctx context.Context,
        req *mcp.CallToolRequest,
        input ExampleInput,
    ) (*mcp.CallToolResult, ExampleOutput, error)

Use the exact handler shape supported by the installed MCP SDK. If compilation
shows a different generic signature, inspect the SDK source and update this
document rather than guessing.

### Tool Registration

The intended pattern is:

    mcp.AddTool(
        s.mcpServer,
        &mcp.Tool{
            Name:        "example",
            Description: "Example tool",
        },
        s.handleExample,
    )

Do not register the same tool more than once.

## StartMCPStdio Status

Important: StartMCPStdio is not currently considered complete.

The current implementation contains a blocking select statement or another
temporary blocker. This keeps the process alive but does not prove that MCP
messages can be received or answered.

The next implementation task is:

1. Inspect the installed SDK transport API.
2. Identify the correct stdio transport type.
3. Connect the server to stdin and stdout.
4. Preserve process cancellation through context.
5. Return transport errors.
6. Test initialize, tools/list, and tools/call requests.

Do not replace the blocker with guessed code.

## Gateway Status

The gateway layer is currently mocked or incomplete.

Before implementing real network access:

1. Identify the current Gateway interface.
2. List every method required by main.go and mcp_server.go.
3. Define request and response formats.
4. Define authentication.
5. Define timeouts.
6. Define retry behavior.
7. Define error handling.
8. Add a local mock server for tests.
9. Implement HTTPGateway only after the contract is clear.

Never add a method such as Execute, Browse, RestartNode, or FabricHealth to a
concrete type without checking the interface and all callers.

## Validation Workflow

From omniclient:

    go version
    go mod tidy
    go build ./...
    go test ./...

For source inspection:

    go doc github.com/modelcontextprotocol/go-sdk/mcp
    go list -m all
    go list -m -json github.com/modelcontextprotocol/go-sdk

After every code change:

1. Format changed Go files with gofmt.
2. Run go build ./....
3. Run go test ./....
4. Inspect git diff.
5. Confirm no duplicate structs were introduced.
6. Confirm documentation remains ASCII-only.

## Safe Implementation Order

The recommended implementation sequence is:

### Phase 1: Stabilize

- Confirm main.go builds.
- Confirm gateway_client.go definitions.
- Confirm mcp_server.go definitions.
- Remove duplicate structures only when their ownership is clear.
- Add compile-time interface checks where useful.

### Phase 2: MCP Transport

- Replace the StartMCPStdio blocker.
- Test MCP initialize.
- Test tools/list.
- Test tools/call for each existing tool.

### Phase 3: Gateway Contract

- Document gateway endpoints or RPC methods.
- Implement HTTPGateway.
- Add timeouts and context cancellation.
- Add authentication handling.
- Add mock gateway tests.

### Phase 4: Operational Tools

Only after the transport and gateway are stable, add new tools such as:

- node discovery;
- node health;
- task dispatch;
- sandbox execution;
- web browsing;
- file operations.

Every new tool must have:

- an input structure;
- an output structure;
- json and jsonschema tags;
- one handler;
- one registration;
- validation;
- error handling;
- tests.

## Common Mistakes to Avoid

### Duplicate declarations

Bad:

    type ExecuteResult struct { ... }

when ExecuteResult already exists in gateway_client.go.

Correct:

- Reuse the existing type.
- Modify the owner file only if the structure itself must change.

### Wrong gateway receiver

Bad:

    s.gateway.Execute(...)

when Execute is not part of the current Gateway interface.

Correct:

- Inspect the interface.
- Add the method to the interface and implementation only as an intentional
  architecture change.
- Update all implementations and tests.

### Fake MCP success

Bad:

    select {}

This only blocks. It does not implement MCP transport.

Correct:

- Connect the MCP server to the SDK stdio transport.
- Test actual JSON-RPC requests.

### Unverified assumptions

Do not assume:

- that a route exists;
- that an endpoint is HTTP rather than RPC;
- that a tool is available;
- that a language is supported;
- that a method exists on Gateway;
- that a build passing means MCP runtime works.

## Required AI Handoff Response

After reading this file, report exactly:

    Handoff read.
    Go version: <version>
    MCP SDK version: <version>
    Build status: <pass or fail>
    Test status: <pass or fail>
    StartMCPStdio status: <real transport or temporary blocker>
    Gateway status: <mock, partial, or real>
    Core file to modify next: <file>
    Proposed next task: <task>