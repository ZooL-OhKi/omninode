# Omninode project handover

## Mission

Omninode hosts autonomous AI residents continuously on Oracle servers. The resident AI is intended to plan, execute, inspect, repair, and document work directly using the resources of its node: files, code, processes, browser sessions, and approved local tools. Omninode is not only a passive collection of remote commands.

Runtime controls remain mandatory: identity, capabilities, workspace restrictions, network policy, secret isolation, resource budgets, audit logging, and approval for destructive or high-risk actions.

## Verified baseline

- Python gateway exposes authenticated `POST /api/v1/browse`.
- MQTT service has synchronous Request-Reply dispatch with `PendingTask`, `threading.Event`, locking, timeout handling, and cleanup in `finally`.
- Go gateway client has deterministic local HTTP contract coverage.
- Python tests cover API-key rejection and no-online-node handling and pass locally.
- Repository ignore rules exclude venvs, Python caches, Go binaries, secrets, logs, databases, and local artifacts.
- `httpx2` is required by the installed Starlette test client and is included in the test dependencies.
- Python test coverage is still incomplete; broker-backed integration tests are not yet implemented.

## Verified architectural position

Omninode is a distributed computational fabric designed to host autonomous and persistent AI residents 24/7 on Oracle Cloud servers. The goal is to move beyond passive agents that receive individual commands, providing resident AIs with an operational environment in which they can plan, execute, verify, correct, and document work directly on node resources within runtime capabilities and policies.

The gateway uses synchronous MQTT Request-Reply with correlated tasks, `PendingTask`, `threading.Event`, structures protected by `RLock`, timeout handling, and cleanup on success and failure. Current routing selects an online node with the lowest reported `load`; this is deterministic routing and is not yet proven optimal load balancing.

`omniclient` implements the HTTP client and MCP integration. The Browse HTTP contract is tested offline with `httptest.NewServer`, without external network dependencies. Depending on deployment, the Go component can operate as a local fabric component or MCP interface; it should not be described only as an end-user device client.

The initial browser direction is standard Chromium with Playwright and/or CDP, isolated profiles per agent or task, protected CDP, domain allowlists, and auditable actions. A custom Chromium fork is not planned in this phase. CAPTCHA, MFA, payments, and other high-risk actions require pause or authorized handoff; anti-abuse protections must not be bypassed.

The security model is default deny and least privilege, with explicit capabilities, isolated workspaces, controlled filesystem/process/network access, separated secret handling, audit logs, and approval for destructive or high-risk actions. Cryptographic in-memory secret isolation remains a requirement to implement and verify; it is not a guarantee demonstrated by the current baseline.

The Go HTTP contract tests, `go test ./...`, `go vet ./...`, Python compilation, gateway import, and initial Python tests pass locally. MQTT broker-backed end-to-end coverage for concurrency, timeout cleanup, duplicate and late responses, reconnects, and worker restart remains to be completed. The Go race detector also needs an environment with CGO/GCC.

## Current phase

The reliability baseline is closed for HTTP and initial gateway tests. The next phase is MQTT reliability. Add an isolated local broker test environment and cover concurrency, timeouts, cleanup, duplicate and late responses, malformed payloads, offline nodes, reconnects, and worker restarts. Never use the Oracle production broker for tests.

## Browser direction

Start with standard Chromium, Playwright/CDP, isolated profiles, protected CDP, domain allowlists, controlled downloads/uploads, and auditable actions. Do not fork Chromium initially. CAPTCHA and MFA require pause or authorized handoff; anti-abuse controls must not be bypassed.

## Security and repository rules

Use default deny and least privilege. Restrict files to explicit workspaces. Do not expose unrestricted shell execution. Keep secrets out of Git. Do not commit generated binaries, virtual environments, logs, databases, or local state. Review `SECURITY.md` before adding capabilities.

## Validation

```powershell
Set-Location A:\omninode\node1-gateway
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\python.exe -m compileall .

Set-Location A:\omninode\omniclient
gofmt -l .
go test ./...
go test -race ./...
go vet ./...

Set-Location A:\omninode
git diff --check
git status --short
git diff --stat
```

`pytest` currently reports passing initial tests after installing `httpx2`. If the race detector cannot run because CGO/GCC is unavailable, record that limitation rather than treating it as a functional test failure. No commit or push should occur without review of the complete diff.
