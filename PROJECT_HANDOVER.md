# Omninode Project Handover

## Handover contract

This document is the engineering continuation contract. A new contributor or AI must be able to identify the repository, reconstruct the design, verify the environment, locate the implementation, and choose the next safe action without relying on private conversation history.

For a full reconstruction prompt, read `docs/AI_ONBOARDING.md`. For exact file responsibilities, read `docs/REPOSITORY_MAP.md`. For commands and recovery, read `docs/OPERATIONS_RUNBOOK.md`.

## Identity

Repository: `ZooL-OhKi/omninode`

Branch: `feature/browse-rpc-mqtt`

Last implementation checkpoint before this documentation organization: `325eee3`

Last documentation checkpoint before this organization: `eb678f9`

The documentation-only organization change must not alter Python or Go behavior.

## Philosophy

Omninode is a distributed AI execution fabric, not a remote shell. Remote intelligence expresses intent; the gateway coordinates; MQTT transports; local policy authorizes; the node executes only explicit capabilities.

The design optimizes for local autonomy, least privilege, auditability, deterministic denial, and incremental proof. A worker is autonomous inside a boundary, never above it.

## Verified baseline

Previously verified locally:

```text
Python pytest: 15 passed, 1 warning
Python compileall: passed
go test ./...: passed
go vet ./...: passed
git diff --check: passed
git push: succeeded for feature/browse-rpc-mqtt
```

The warning was a Starlette/AnyIO deprecation warning.

## Implemented areas

- FastAPI gateway and MQTT service scaffolding.
- Go gateway client and MCP-related code.
- Audit and policy modules.
- Workspace confinement and atomic local writes.
- Allowlisted command executor.
- Autonomous work-loop scaffolding.
- Browser runtime policy scaffolding.
- Task envelope validation.
- Detailed project documentation and AI onboarding guides.

## Not proven yet

Do not claim production readiness until these are demonstrated:

1. Gateway publishes a real task to MQTT.
2. A local Go node subscribes to its own task topic.
3. The node validates and executes `workspace.write`.
4. The node publishes a response with matching correlation and task IDs.
5. The gateway/MCP client returns the real result under concurrency.
6. Duplicate delivery is idempotent.
7. Network transport uses TLS and topic ACLs.
8. Cloud deployment has health checks and rollback.

## Immediate next action

Implement one local vertical slice only:

```text
MCP or HTTP
  -> FastAPI task creation
  -> MQTT publish
  -> node-specific Go subscriber
  -> local validation
  -> workspace.write in temporary workspace
  -> MQTT correlated response
  -> real MCP/HTTP result
```

Before coding, inspect the actual interfaces in `node1-gateway/mqtt_service.py`, `node1-gateway/main.py`, `omniclient/main.go`, and `omniclient/gateway_client.go`. Do not create a second protocol or assume names from documentation are already wired.

## Required safety constraints

- no arbitrary shell strings;
- no public broker during loopback development;
- no Desktop-wide write by default;
- no credentials or personal browser profiles;
- no anti-bot evasion;
- no force-push or destructive reset;
- no claim of operational success without a real result.

## Pull procedure

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
```

If local changes exist, preserve them and inspect before pulling.

## AI continuation prompt

```text
You are the next Principal Distributed Systems Architect and Expert AI Systems Engineer for Omninode.

Start by reading, in order:
1. docs/AI_ONBOARDING.md
2. PROJECT_HANDOVER.md
3. docs/REPOSITORY_MAP.md
4. ARCHITECTURE.md
5. SECURITY.md
6. docs/OPERATIONS_RUNBOOK.md
7. ROADMAP.md
8. INDEX.md

Omninode is a distributed AI execution fabric, not a remote shell. Its philosophy is local autonomy, explicit capabilities, least privilege, auditability, deterministic failure, and incremental proof. A remote AI can request work, but the local node is the final authority over its filesystem, processes, browser, and credentials.

Repository: ZooL-OhKi/omninode
Branch: feature/browse-rpc-mqtt
Implementation checkpoint: 325eee3
Documentation checkpoint before this organization: eb678f9

Your first job is not to rewrite the project. Reconstruct the current system from the repository. Inspect actual code and identify:
- current FastAPI endpoints;
- MQTT broker/client library and topic names;
- gateway request/reply state;
- Go subscriber or node runtime;
- task DTOs and correlation fields;
- policy and workspace enforcement;
- how MCP dispatch maps to gateway calls.

Then implement the smallest real vertical slice:
MCP/HTTP dispatch -> FastAPI -> MQTT task topic -> local omniclient subscriber -> capability validation -> workspace.write -> correlated MQTT response -> real result.

Use only structured tasks with schema_version, task_id, goal_id, agent_id, node_id, capability, deadline, and payload. Preserve existing interfaces unless a migration is documented. Use a loopback broker and temporary workspace first. Do not implement arbitrary shell execution, credential access, browser anti-detection, CAPTCHA bypass, public broker exposure, or silent privilege elevation.

Before editing, report the current call graph and the smallest missing link. After editing, report exact files, commands, results, limitations, and the next milestone. Do not claim success based only on unit tests; prove one real task result.
```

## Definition of done

The next milestone is complete when an MCP or HTTP request creates one real file in an authorized temporary workspace through the complete gateway/MQTT/local-node path and returns its actual result, while unauthorized paths and capabilities are blocked.