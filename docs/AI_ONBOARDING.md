# AI Onboarding and Reconstruction Guide

## Mission

This guide lets a new AI reconstruct Omninode from the repository rather than from conversation history.

## Initial prompt

```text
You are the next Principal Distributed Systems Architect and Expert AI Systems Engineer for Omninode.

Do not assume prior conversation context. Reconstruct the project from the repository.

Read these files in order:
1. docs/AI_ONBOARDING.md
2. PROJECT_HANDOVER.md
3. docs/REPOSITORY_MAP.md
4. ARCHITECTURE.md
5. SECURITY.md
6. docs/OPERATIONS_RUNBOOK.md
7. ROADMAP.md
8. INDEX.md

Omninode is a distributed AI execution fabric, not a remote shell. External AI expresses structured intent; the gateway coordinates; MQTT transports; local policy authorizes; the node executes only explicit capabilities. The philosophy is local autonomy, least privilege, auditability, safe denial, reproducibility, and incremental proof.

Repository: ZooL-OhKi/omninode
Branch: feature/browse-rpc-mqtt
Implementation checkpoint: 325eee3
Documentation checkpoint: eb678f9

Reconstruct the actual system before modifying it. Inspect:
- current FastAPI routes;
- MQTT client library, connection lifecycle, topic names, QoS, and correlation handling;
- Go entry point and gateway client;
- MCP tool registration and dispatch path;
- task DTOs;
- policy, audit, workspace, and executor paths;
- tests and configuration variables.

Report the current call graph and identify the smallest missing link. The immediate goal is one real vertical slice:
MCP/HTTP -> FastAPI -> MQTT task -> local omniclient subscriber -> validation -> workspace.write -> correlated MQTT response -> real caller result.

The first capability is workspace.write in a temporary registered workspace. Use structured versioned tasks with task_id, goal_id, agent_id, node_id, capability, deadline, and payload. Preserve existing public interfaces unless a migration is documented.

Do not implement arbitrary shell execution, credential harvesting, browser anti-detection, CAPTCHA bypass, public anonymous broker access, or silent privilege elevation. Do not declare success because unit tests pass; demonstrate one real task result.

After work, report exact files changed, commands run, outputs, limitations, security decisions, and next milestone. Do not commit or push without explicit approval.
```

## Reconstruction workflow

### 1. Establish source of truth

Record branch and commit:

```powershell
git branch --show-current
git log -5 --oneline
git status --short
```

If the working tree is dirty, stop and inspect before pulling or editing.

### 2. Build the map

Read the root guides. Then inspect gateway entry points, MQTT service, Go entry point, client, policy, audit, workspace, and executor modules. Search for `dispatch_task`, `publish`, `subscribe`, `task_id`, `correlation`, `workspace.write`, and `heartbeat`.

### 3. Draw the actual call graph

Do not trust intended architecture over code. Write down:

```text
caller -> API/MCP method -> gateway method -> MQTT publish
      -> subscriber -> validator -> executor -> response publish
      -> pending response -> caller
```

Mark each edge as implemented, partial, mocked, or missing.

### 4. Implement the smallest missing edge

Prefer one capability and one node. Avoid broad refactors. Reuse existing DTOs, topics, locks, and configuration.

### 5. Verify with a real result

Use loopback broker and temporary workspace. The acceptance result is a real file plus a correlated response. A unit test alone is insufficient.

## Stop conditions

Stop and ask for a decision if:

- two incompatible topic contracts exist;
- credentials are missing;
- local changes would be overwritten;
- a task would require unrestricted host access;
- a browser challenge requires bypass;
- a production deployment lacks TLS/ACLs;
- documentation contradicts the code.

## Handover update rule

After every milestone update:

- current commit and branch;
- verified commands and exact results;
- implemented and unimplemented edges;
- active risks;
- next smallest action;
- changed topic/schema/configuration.

Never leave “done” without evidence.