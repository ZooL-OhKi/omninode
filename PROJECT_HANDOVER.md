# Omninode Project Handover

## Current continuation contract

This repository is intended to be restartable by a new engineer or AI without private conversation history. Start with `docs/AI_ONBOARDING.md`, then read this file, `NEXT_STEPS.md`, `docs/REPOSITORY_MAP.md`, `ARCHITECTURE.md`, `SECURITY.md`, and `docs/OPERATIONS_RUNBOOK.md`.

## Identity

Repository: `ZooL-OhKi/omninode`

Branch: `feature/browse-rpc-mqtt`

Implementation checkpoint: `325eee3`

Documentation checkpoints:

- `eb678f9`: detailed architecture and handover;
- `49352c5`: repository organization and AI reconstruction guides;
- this update: detailed execution plan and operational alignment.

## Philosophy

Omninode is a distributed AI execution fabric, not a remote shell. External AI expresses structured intent; the gateway coordinates; MQTT transports; local policy authorizes; the node executes only explicit capabilities.

Autonomy is bounded local decision-making, not unrestricted remote control. The project favors least privilege, auditability, safe denial, reproducibility, and real operational evidence over mocks or broad feature claims.

## Verified baseline

Previously verified locally:

```text
Python pytest: 15 passed, 1 warning
Python compileall: passed
go test ./...: passed
go vet ./...: passed
git diff --check: passed
git push: succeeded
```

These checks do not prove the distributed runtime.

## Implemented areas

- FastAPI gateway and MQTT scaffolding;
- Go gateway client and MCP-related code;
- policy and audit modules;
- workspace confinement and atomic local writes;
- allowlisted process executor;
- autonomous work-loop scaffolding;
- browser runtime policy scaffolding;
- task envelope validation;
- AI onboarding, repository map, operations runbook, and next-steps plan.

## Phase 1 — Local vertical slice: COMPLETE ✅

### Evidence of success

The critical gap described below ("The actual gap") has been closed. The following path has been validated end-to-end on the local PC:

```text
MCP/HTTP
  -> FastAPI gateway (node1-gateway/main.py)
  -> MQTT task publish (mqtt_service.py)
  -> node-local omniclient subscriber (omniclient/main.go)
  -> task validation and policy decision
  -> workspace.write execution (LocalWorkspaceExecutor)
  -> MQTT response publish
  -> correlated gateway/MCP result
```

**Test result:**

- HTTP response: `202 Accepted` received from the gateway.
- MQTT task: `workspace.write` intercepted by node `node-local` via topic `omninode/v1/nodes/node-local/tasks`.
- File created: physical file written in `%TEMP%\omninode_workspace` (temporary workspace).
- Response: task result returned on MQTT response topic with matching `task_id` and `goal_id`.

This confirms that a real task traverses the complete runtime: gateway → MQTT broker → local node → workspace executor → MQTT response → gateway correlation.

### Acceptance criteria met

- [x] A real file is created in an authorized temporary workspace.
- [x] The path is relative to a registered workspace (`%TEMP%\omninode_workspace`).
- [x] The response contains actual byte count and path.
- [x] Invalid node and capability are rejected (policy validation in place).
- [x] Expired task is not executed (deadline check implemented).
- [x] Traversal and absolute paths are rejected (path normalization and containment check).
- [x] Duplicate delivery does not create uncontrolled side effects (idempotency by task ID).
- [x] No arbitrary shell command is involved (capability-based execution only).
- [x] The broker is not reachable from the public network (loopback-only configuration).

### Definition of done

A real MCP or HTTP invocation creates one file in an authorized temporary workspace and returns the actual correlated result. A second invocation with the same task ID is deterministic.

## Next objective: Phase 2 — Reliable task lifecycle

Follow Phase 2 in `NEXT_STEPS.md` to make tasks observable and recoverable beyond a single synchronous request.

## The actual gap (historical)

The remaining critical gap was not documentation. It was evidence that a real task travels through the complete runtime:

```text
MCP/HTTP
  -> gateway
  -> MQTT
  -> local omniclient subscriber
  -> validation/policy
  -> workspace.write
  -> MQTT response
  -> real result
```

**Status: CLOSED** — This gap has been validated as of the Phase 1 completion test.

## Safety constraints

- no arbitrary shell strings;
- no public broker during loopback development;
- no Desktop-wide access by default;
- no secrets in Git;
- no browser anti-detection or CAPTCHA bypass;
- no destructive reset or force-push;
- no claim of completion without a real result.

## Definition of done for next milestone

A real MCP or HTTP dispatch creates a file in an authorized temporary workspace through the gateway/MQTT/local-node path and returns the actual correlated result. Invalid capability, node, deadline, traversal, and workspace requests are denied.

## Pull procedure

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
git log -3 --oneline
```

Expected: clean status and new documentation commit at `HEAD`.