# Omninode project handover

## Mission

Omninode is intended to host autonomous AI residents continuously on Oracle servers. The AI resident should be able to plan, execute, inspect, repair, and document work directly using the resources of its node. It is not intended to be only a remote tool endpoint that waits for another AI to issue one command at a time.

The autonomy boundary is enforced by the runtime: identity, capabilities, workspace restrictions, network policy, secret isolation, resource limits, audit logs, and approval gates for destructive or high-risk operations.

## Current implementation

### Python gateway

`node1-gateway/mqtt_service.py` implements synchronous Request-Reply dispatch using `PendingTask`, `threading.Event`, a lock-protected pending-task map, timeout handling, and cleanup in `finally`.

`node1-gateway/main.py` exposes authenticated `POST /api/v1/browse`. It selects an online node with the lowest reported load, dispatches through the MQTT service in a threadpool, and maps unavailable nodes/publish errors to 503, timeouts to 504, and worker/upstream errors to 502.

Runtime dependencies are in `node1-gateway/requirements.txt`. Python compilation and importing `main` have been verified. If pytest reports `no tests ran`, that means no Python tests are currently discovered; it is not evidence of functional test coverage.

### Go client

`omniclient/gateway_client.go` implements the internal HTTP client. `omniclient/main.go` integrates the MCP-facing server. `omniclient/mcp_server_test.go` must remain deterministic and use `httptest.NewServer`, with no external network calls.

## RPC contract direction

The RPC contract should be versioned. A request should carry a task identifier, task type, target node, creation/deadline information, and payload. A response should carry the task identifier, status, node identifier, result or structured error, and timestamps.

Recommended states are `accepted`, `running`, `completed`, `failed`, `cancelled`, and `expired`. Error responses should include a stable code, human-readable message, and retryable flag. Late and duplicate responses must be harmless.

## Browser direction

Do not fork Chromium initially. Start with standard Chromium, Playwright and/or CDP, isolated profiles per agent/task, protected CDP, domain allowlists, controlled downloads/uploads, and auditable browser actions. Human intervention may be required for CAPTCHA, MFA, payments, account creation, or other high-risk flows. Anti-abuse protections must not be bypassed.

## Security direction

Use default deny and least privilege. Capabilities should be assigned per agent and task. Filesystem access should be scoped to explicit workspaces. Secrets must not be inherited by arbitrary processes. Network egress should be denied by default for sandboxed execution. Destructive operations require an approval policy or an equivalent explicit control. Every meaningful action should be auditable.

## Next milestones

1. Add an MQTT broker-backed integration test environment.
2. Test timeout cleanup, concurrent correlations, duplicate replies, late replies, reconnects, offline nodes, and malformed payloads.
3. Version and validate the RPC schemas.
4. Add capability, policy, audit, and resource-budget primitives.
5. Build the browser runtime on standard Chromium before considering any custom browser build.
6. Add controlled filesystem operations.
7. Implement a resource-limited sandbox and only then consider `run_sandbox_code`.
8. Add MCP tools incrementally, with risk classification and tests.

## Handoff procedure

Before changing code:

```powershell
Set-Location A:\omninode
git status --short
git diff --stat
Get-Content .\README.md
Get-Content .\ARCHITECTURE.md
Get-Content .\SECURITY.md
Get-Content .\ROADMAP.md
```

Validate Go:

```powershell
Set-Location A:\omninode\omniclient
gofmt -l .
go test ./...
go vet ./...
```

Validate Python:

```powershell
Set-Location A:\omninode\node1-gateway
& .\venv\Scripts\python.exe -m compileall .
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\python.exe -c "import main; print('main import OK')"
```

Never add generated binaries. Do not commit or push without explicit approval.
