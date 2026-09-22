# Omninode project index

## Purpose

Omninode hosts autonomous AI residents on always-on Oracle servers. The resident AI is the operator of its environment: it can plan and execute work using node resources, files, code, processes, browser sessions, and local tools within explicit runtime capabilities and security policies.

## Read first

1. `README.md` — mission and quick orientation.
2. `PROJECT_HANDOVER.md` — current state and continuation procedure.
3. `ARCHITECTURE.md` — components and data flow.
4. `SECURITY.md` — capabilities, isolation, secrets, browser and high-risk actions.
5. `ROADMAP.md` — ordered engineering work.

## Components

- `omniclient/`: Go HTTP gateway client and MCP server integration.
- `node1-gateway/`: FastAPI HTTP gateway and MQTT task dispatcher.
- MQTT broker: request/reply transport.
- Oracle nodes: resident AI workers.
- Browser runtime: planned controlled web capability.

## Current flow

1. A client calls the authenticated gateway.
2. The gateway validates the request and selects an online node.
3. The gateway publishes a task over MQTT with correlation data.
4. A worker executes the task and publishes a result.
5. The gateway resolves the pending task, cleans it up, and returns the result.

## Current baseline

- Synchronous MQTT Request-Reply exists in `mqtt_service.py`.
- `POST /api/v1/browse` exists in `main.py`.
- The gateway uses `x-omninode-key` and `OMNINODE_API_KEY`.
- The Go Browse client is covered by a local `httptest.NewServer` test.
- Go formatting, tests, and vet pass locally.
- Python gateway tests pass locally after installing `httpx2`.
- Python compilation and import pass locally.
- MQTT broker-backed integration tests and `go test -race ./...` remain pending.

## Before changing code

```powershell
Set-Location A:\omninode
Get-Content .\README.md
Get-Content .\PROJECT_HANDOVER.md
Get-Content .\ARCHITECTURE.md
Get-Content .\SECURITY.md
Get-Content .\ROADMAP.md
git status --short
git diff --stat
```

Do not discard local changes. Do not commit or push without explicit approval.

## Immediate next work

- Add broker-backed MQTT integration tests.
- Version the RPC request/response schema.
- Test late replies, duplicate replies, timeout cleanup, reconnects, and concurrent tasks.
- Define capability and policy objects.
- Design the browser runtime using standard Chromium, Playwright/CDP, isolated profiles, and protected CDP.
- Add controlled filesystem and sandbox services before exposing arbitrary execution.
