# Omninode

Omninode is a distributed AI execution fabric: external AI systems express structured intent, trusted gateways coordinate work, MQTT carries messages, and local nodes execute only explicitly authorized capabilities.

The project is built around one principle:

> Remote intelligence may request work; local policy decides whether work may happen.

Omninode is therefore not a remote shell and not a collection of blindly obedient agents. It is a cooperative fabric with local autonomy, least privilege, observable execution, deterministic failure, and gradual delivery.

## Current status

Active branch: `feature/browse-rpc-mqtt`

Latest documentation checkpoint before this update: `eb678f9`

Current state:

- Python gateway present.
- Go `omniclient` present.
- MQTT service and request/reply scaffolding present.
- Capability, audit, workspace, executor, browser-policy, and work-loop modules present.
- Documentation and AI handover guides are being consolidated.
- Local unit and language checks previously passed.
- The real MQTT vertical slice is the next operational milestone.

Do not describe the system as production-ready until a real task has traversed gateway → MQTT → local node → executor → correlated response.

## Philosophy

Omninode favors:

- local authority over remote control;
- explicit capabilities over implicit trust;
- structured tasks over shell strings;
- auditability over invisible automation;
- safe denial over unsafe convenience;
- a small real vertical slice over a broad mock system;
- documented decisions over repeated rediscovery.

Autonomy means that workers can decide and coordinate within their granted boundaries. It does not mean bypassing security, hiding activity, evading anti-bot systems, or accessing a host without authorization.

## System flow

```text
AI / MCP host
    |
    v
Go omniclient MCP interface
    |
    v
FastAPI gateway
    |
    v
MQTT broker
    |
    v
Node-specific omniclient subscriber
    |
    v
Policy + capability + workspace checks
    |
    v
Local executor
    |
    v
Authorized resource
```

MQTT is a transport and coordination mechanism. It is not the final authorization boundary. The local node must validate identity, capability, workspace, path, deadline, and budget before performing work.

## First useful capability

The first operational capability is `workspace.write`:

- caller supplies a registered `workspace_id`;
- path is relative to that workspace;
- traversal, absolute paths, symlink escape, sensitive directories, and oversized content are rejected;
- write is atomic;
- result reports task identity and bounded metadata;
- every decision is auditable.

Do not begin with arbitrary shell execution, real Desktop-wide access, credentials, personal browser profiles, or browser anti-detection.

## Repository guides

Read in this order:

1. `docs/AI_ONBOARDING.md` — complete prompt and reconstruction procedure for a new AI.
2. `PROJECT_HANDOVER.md` — current engineering state and immediate continuation task.
3. `docs/REPOSITORY_MAP.md` — file ownership and call-graph navigation.
4. `ARCHITECTURE.md` — component boundaries and protocol model.
5. `SECURITY.md` — non-negotiable guardrails.
6. `docs/OPERATIONS_RUNBOOK.md` — synchronization, validation, local runtime, and recovery.
7. `ROADMAP.md` — ordered milestones.
8. `INDEX.md` — compact navigation index.

## Immediate milestone

Implement and demonstrate one local vertical slice:

```text
MCP/HTTP dispatch
  -> FastAPI creates a structured task
  -> MQTT publishes to one node topic
  -> local omniclient receives it
  -> local policy validates it
  -> workspace.write creates one temporary file
  -> node publishes correlated response
  -> gateway/MCP returns the real result
```

Use a loopback broker and a temporary workspace first. Add persistence, TLS, network ACLs, cloud deployment, scheduling, and dashboards only after this path is real and observable.

## Synchronization

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
```

Never use `git reset --hard` or `git push --force` to hide an ordinary synchronization problem.

## Non-goals

The project must not implement unrestricted remote shell, credential harvesting, fingerprint spoofing, WebDriver masking, CAPTCHA bypass, synthetic biometric interaction, proxy rotation for evasion, silent account creation, or unauthorized access to personal profiles.