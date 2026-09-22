# Omninode Project Handover

## Handover purpose

This document is the authoritative continuation point for the next human or AI engineer. It records what is known, what was verified, what remains incomplete, and how to proceed without repeating unsafe or redundant work.

## Repository identity

Repository: `ZooL-OhKi/omninode`

Active branch: `feature/browse-rpc-mqtt`

Last published implementation commit before this documentation update: `325eee3`

The branch was rebased onto the remote history and pushed successfully. Do not force-push over it.

## Verified state

The following checks passed in the local working copy:

```text
Python pytest: 15 passed, 1 warning
Python compileall: passed
go test ./...: passed
go vet ./...: passed
git diff --check: passed
```

The warning is a Starlette/AnyIO deprecation warning and did not fail the suite.

## What has been implemented

The branch contains:

- FastAPI gateway changes.
- MQTT service changes.
- Go gateway client changes.
- MCP-related Go changes and tests.
- Audit and policy modules.
- Allowlisted command executor.
- Workspace manager.
- Autonomous work-loop scaffolding.
- Browser runtime policy scaffolding.
- Local workspace executor.
- MQTT task protocol validation.
- Detailed project documentation.

## What is not yet proven

Do not claim the project is production-ready yet. The following are not proven by the unit tests above:

1. A real broker delivers a task from gateway to a local Go node.
2. The Go node performs the capability-bound operation.
3. The node publishes a correlated response.
4. The gateway maps the response back to the correct HTTP/MCP request under concurrency.
5. Duplicate delivery is idempotent.
6. A network deployment is protected with TLS and topic ACLs.
7. Oracle deployment and rollback are automated.

## Immediate continuation task

Implement and run one local vertical slice:

```text
POST or MCP dispatch_task
  -> gateway task creation
  -> MQTT publish to node task topic
  -> local node subscription
  -> task validation
  -> workspace.write executor
  -> MQTT response
  -> gateway status/result
```

Use a temporary workspace under the repository or an explicitly configured runtime directory. Do not write to the real Desktop until the capability and approval model is verified.

## Required implementation rules

- Reuse existing MQTT service and gateway client interfaces.
- Do not create a second competing protocol.
- Do not accept arbitrary shell text.
- Do not expose the broker publicly during local development.
- Keep task payloads structured and versioned.
- Include `task_id`, `goal_id`, `agent_id`, `node_id`, capability, and deadline.
- Record allow and deny decisions.
- Return explicit statuses: `queued`, `running`, `completed`, `failed`, `blocked`, or `expired`.
- Preserve idempotency when adding retries.

## Safe local synchronization

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
```

If the working tree contains intentional local changes, stop and inspect them before pulling. Do not use `reset --hard` to solve ordinary synchronization issues.

## Recommended execution order

1. Read this file, `README.md`, `ARCHITECTURE.md`, and `SECURITY.md`.
2. Inspect `node1-gateway/mqtt_service.py`.
3. Inspect `omniclient/gateway_client.go` and `omniclient/main.go`.
4. Identify the existing topic, DTO, and request/reply interfaces.
5. Implement the smallest real node-side subscriber.
6. Run one local `workspace.write` operation.
7. Add status retrieval and idempotency.
8. Configure TLS and ACLs.
9. Only then consider cloud deployment and dashboard work.

## Definition of done for the next milestone

The next milestone is complete when a real MCP task creates one file in an authorized temporary workspace, returns the actual path and byte count, and rejects an unauthorized path or capability without touching the host.

## AI continuation prompt

Paste the following prompt into a new AI session:

```text
You are the next Principal Distributed Systems Architect and AI Systems Engineer for Omninode.

Omninode is a distributed AI execution fabric, not a remote shell. Its philosophy is local autonomy with explicit capabilities, least privilege, observable execution, deterministic failure, and incremental delivery. A remote AI may request work, but the local node is the final authority over its filesystem, processes, browser, and credentials.

Repository: ZooL-OhKi/omninode
Branch: feature/browse-rpc-mqtt
Last implementation commit: 325eee3

Read these files before changing anything:
1. PROJECT_HANDOVER.md
2. README.md
3. ARCHITECTURE.md
4. SECURITY.md
5. ROADMAP.md
6. INDEX.md

Then inspect:
- node1-gateway/main.py
- node1-gateway/mqtt_service.py
- node1-gateway/policy_engine.py
- node1-gateway/audit.py
- node1-gateway/local_executor.py
- node1-gateway/mqtt_task_protocol.py
- node1-gateway/workspace_manager.py
- omniclient/main.go
- omniclient/gateway_client.go

Current verified checks:
- Python: 15 tests passed, one deprecation warning.
- compileall passed.
- Go tests passed.
- go vet passed.
- git diff --check passed.

The immediate goal is not a broad rewrite. Implement one real local vertical slice:
MCP or HTTP dispatch -> FastAPI gateway -> MQTT task topic -> local omniclient subscriber -> capability validation -> workspace.write -> MQTT correlated response -> gateway/MCP result.

Use structured JSON tasks with schema version, task_id, goal_id, agent_id, node_id, capability, deadline, and payload. Preserve existing interfaces and topic names unless you document a migration. Use MQTT request/reply correlation, idempotency, bounded deadlines, and explicit statuses.

The only initial capability should be workspace.write. It must use a registered workspace, relative paths, path resolution, traversal and symlink protection, file-size limits, atomic writes, and audit records. Do not implement arbitrary shell execution, credential access, browser anti-detection, CAPTCHA bypass, or public broker exposure.

Use a loopback broker for the first operational run. Do not claim production readiness until the real end-to-end path has executed. After implementation, report:
- files changed;
- protocol and topic decisions;
- security decisions;
- commands run;
- exact results;
- unresolved risks;
- next milestone.

Never commit or push without explicit approval. Never use reset --hard or force-push to hide synchronization problems.
```