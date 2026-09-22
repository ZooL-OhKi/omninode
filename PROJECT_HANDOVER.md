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

## The actual gap

The remaining critical gap is not documentation. It is evidence that a real task travels through the complete runtime:

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

## Next action

Follow Phase 1 in `NEXT_STEPS.md`. Before editing code:

1. inspect `node1-gateway/main.py`;
2. inspect `node1-gateway/mqtt_service.py`;
3. inspect `omniclient/main.go`;
4. inspect `omniclient/gateway_client.go`;
5. trace actual topics, DTOs, and pending-response handling;
6. identify the smallest missing edge;
7. implement only that edge;
8. run one real task against a temporary workspace;
9. record exact evidence here.

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