# Repository Map

## Top-level layout

```text
omninode/
├── .github/                       CI/CD configuration
├── node1-gateway/                 Python FastAPI gateway and policy runtime
├── omniclient/                    Go MCP/gateway/node client
├── README.md                      project entry point
├── ARCHITECTURE.md                architecture and protocol
├── PROJECT_HANDOVER.md            current continuation contract
├── ROADMAP.md                     ordered milestones
├── SECURITY.md                    security model
├── INDEX.md                       compact index
└── docs/
    ├── AI_ONBOARDING.md           AI reconstruction prompt and workflow
    ├── REPOSITORY_MAP.md          this file
    └── OPERATIONS_RUNBOOK.md      synchronization, runtime, validation, recovery
```

## Python ownership

### `node1-gateway/main.py`

FastAPI application, routes, startup/shutdown wiring, and API-level validation. Do not put filesystem execution directly in routes.

### `node1-gateway/mqtt_service.py`

MQTT connection lifecycle, subscriptions, publish operations, pending request/reply coordination, timeouts, and correlation. This is the first file to inspect for the missing vertical-slice edge.

### `node1-gateway/policy_engine.py`

Capability decision logic. Default deny. It must validate actor, goal, capability, resource, workspace, deadline, and budget.

### `node1-gateway/audit.py`

Thread-safe audit events and sinks. Audit decisions without leaking secrets.

### `node1-gateway/workspace_manager.py`

Workspace registration and path confinement. Responsible for traversal, absolute paths, symlinks, sensitive paths, atomic operations, and bounded resources.

### `node1-gateway/local_executor.py`

First concrete operation: constrained `workspace.write`. It is not a general-purpose shell executor.

### `node1-gateway/mqtt_task_protocol.py`

Task identity, schema, deadlines, and envelope validation.

### `node1-gateway/command_executor.py`

Separate bounded process executor. Keep it allowlisted and independent from workspace writes.

### `node1-gateway/work_loop.py`

Goal orchestration and iteration budgets. It should call policy and executors rather than bypassing them.

### `node1-gateway/browser_runtime.py`

Browser capability scaffolding and safety policy. Human handoff is required for friction events.

## Go ownership

### `omniclient/main.go`

Process entry point, configuration, mode selection, and runtime wiring.

### `omniclient/gateway_client.go`

Gateway communication, MQTT-related client behavior, request/reply, and DTO conversion. Inspect before creating another transport layer.

### `omniclient/mcp_server_test.go`

MCP behavior tests. The production MCP registration may be in another Go file; search symbols rather than assuming this test is the implementation.

## Configuration ownership

Environment variables and local runtime configuration should be documented without committing secrets. Search for `MQTT_`, `OMNINODE_`, broker URLs, node IDs, API keys, and workspace roots.

## Trace strategy

Start at the public operation:

```text
dispatch_task
```

Then follow:

```text
HTTP/MCP -> gateway client -> gateway route -> mqtt_service.publish
         -> node subscriber -> validate_task -> policy -> executor
         -> response publish -> pending map -> HTTP/MCP result
```

If a link cannot be found in code, mark it missing instead of inventing it.

## Files never to treat as source

- `venv/`;
- `__pycache__/`;
- `.pytest_cache/`;
- generated binaries;
- local secrets;
- temporary scripts;
- backup directories.