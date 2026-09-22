# Omninode

Omninode is a personal infrastructure for autonomous AI residents running continuously on Oracle servers. It is not merely a collection of agents waiting for small commands from another AI: each resident AI is intended to plan, execute, verify, correct, and document work directly on the node that hosts it.

## Mission

An Omninode resident can use the host node's CPU, memory, disk, network, browser, files, code, and local tools according to explicit capabilities and policies. The objective is to replace repetitive operational work while retaining infrastructure-level controls for identity, permissions, resource limits, auditing, and high-risk actions.

Autonomy does not mean unrestricted privilege. The runtime must enforce default-deny policies, least privilege, isolated workspaces, secret isolation, network controls, resource limits, and auditability.

## Current architecture

- `omniclient`: Go client and MCP-facing server.
- `node1-gateway`: FastAPI gateway translating authenticated HTTP calls into MQTT tasks.
- MQTT broker: transport between gateway and resident workers.
- Oracle nodes: persistent AI workers and their local resources.
- Browser runtime: planned capability based initially on standard Chromium with Playwright and/or CDP, isolated per agent or task.

The current implemented path includes synchronous Request-Reply over MQTT and `POST /api/v1/browse`. The gateway selects an online node with the lowest reported load and maps publish, timeout, and upstream failures to HTTP errors.

## Browser direction

The first implementation should use standard Chromium, isolated profiles, and Playwright/CDP rather than a custom Chromium fork. CDP must be protected on localhost or an authenticated private network. Domain allowlists, session isolation, download/upload controls, and audit logging are required.

CAPTCHA, MFA, payment, account creation, and other high-risk flows must be paused, delegated, or explicitly approved when required. Omninode must not bypass anti-abuse protections.

## Verification

Go:

```powershell
Set-Location A:\omninode\omniclient
gofmt -l .
go test ./...
go vet ./...
```

Python:

```powershell
Set-Location A:\omninode\node1-gateway
& .\venv\Scripts\python.exe -m compileall .
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\python.exe -c "import main; print('main import OK')"
```

At the current baseline, Python compilation and import are verified, but no Python tests are currently detected if pytest reports `no tests ran`.

## Roadmap

1. Version the RPC contract and error codes.
2. Add broker-backed MQTT end-to-end tests for concurrency, timeout, duplication, late replies, and reconnects.
3. Add capability and policy enforcement with audit events.
4. Build the browser runtime around isolated Chromium profiles and protected CDP.
5. Add controlled filesystem tools and a resource-limited sandbox.
6. Implement `run_sandbox_code` only after isolation and policy tests pass.
7. Add further MCP tools gradually, including node health, workspace operations, and approved system actions.

See `INDEX.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `SECURITY.md`, and `PROJECT_HANDOVER.md` for operational details.
