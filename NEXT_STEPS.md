# Omninode Next Steps Execution Plan

## Status

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Real local vertical slice | **complete** ✅ |
| Phase 2 | Reliable task lifecycle | **next** (in progress) |
| Phase 3 | Secure network fabric | pending |
| Phase 4 | Multi-node orchestration | pending |
| Phase 5 | MCP productization | pending |
| Phase 6 | Browser capability | pending |
| Phase 7 | Oracle deployment and CI/CD | pending |
| Phase 8 | Operator experience | pending |

**Current focus:** Phase 2 — Reliable task lifecycle

## Purpose

This document turns the project handover into an ordered execution plan. It is intentionally concrete: every phase has prerequisites, atomic tasks, acceptance criteria, stop conditions, risks, and a definition of done.

The project objective is not to maximize features. The objective is to produce a trustworthy distributed AI execution fabric whose first real task can travel from an AI-facing interface to a local authorized executor and return an observable result.

## Current baseline

Branch: `feature/browse-rpc-mqtt`

Implementation checkpoint: `325eee3`

Documentation checkpoints:

- `eb678f9`: detailed architecture and handover documentation;
- `49352c5`: repository organization and AI reconstruction guides.

Previously verified:

- Python tests: 15 passed, one deprecation warning;
- Python compilation: passed;
- Go tests: passed;
- `go vet ./...`: passed;
- `git diff --check`: passed;
- branch push: succeeded.

These results validate code quality checks, not the complete distributed runtime. The highest-priority gap is the real MQTT path.

**Update (Phase 1 complete):** The real MQTT path has been validated end-to-end. See `PROJECT_HANDOVER.md` for evidence of the successful Phase 1 test.

## Operating principles

1. Implement one real vertical slice before expanding capabilities.
2. Preserve existing topic names and DTOs until the actual code has been traced.
3. Keep authorization local to the node that owns the resource.
4. Treat every retry and duplicate as a possible side effect.
5. Prefer explicit failure over silent fallback.
6. Keep development on loopback until network security is configured.
7. Update handover documentation after each meaningful milestone.
8. Never claim completion from mocks or unit tests alone.

## Phase 1 — Real local vertical slice ✅ COMPLETE

### Status

**COMPLETE** — This phase has been validated end-to-end. See `PROJECT_HANDOVER.md` for detailed evidence.

### Objective (achieved)

Prove this exact path with one local node and one temporary workspace:

```text
MCP or HTTP
  -> FastAPI gateway
  -> MQTT task publish
  -> node-specific omniclient subscriber
  -> task validation
  -> policy decision
  -> workspace.write
  -> MQTT response
  -> correlated gateway/MCP result
```

### Prerequisites (met)

- local checkout is synchronized;
- broker is available on loopback;
- Python virtual environment exists;
- Go toolchain is available;
- no uncommitted changes are being overwritten;
- workspace root is explicitly registered.

### Atomic tasks (completed)

1. Trace the current gateway route that creates or dispatches a goal.
2. Trace the current `mqtt_service.py` publish and pending-response interfaces.
3. Trace `omniclient/main.go` and `gateway_client.go` for actual runtime modes.
4. Write down current topic names and payload DTOs before editing.
5. Identify whether the Go process already subscribes to node task topics.
6. Add only the missing subscriber/dispatcher edge.
7. Validate `schema_version`, task ID, goal ID, agent ID, node ID, capability, deadline, and payload.
8. Route `workspace.write` to the existing safe executor.
9. Publish a response containing matching task and goal IDs.
10. Return the actual response through the existing gateway/MCP path.
11. Run one task against a temporary workspace.
12. Record the exact result in `PROJECT_HANDOVER.md`.

### Acceptance criteria (met)

- [x] a real file is created;
- [x] the path is relative to a registered workspace;
- [x] the response contains actual byte count and path;
- [x] invalid node and capability are rejected;
- [x] expired task is not executed;
- [x] traversal and absolute paths are rejected;
- [x] duplicate delivery does not create uncontrolled side effects;
- [x] no arbitrary shell command is involved;
- [x] the broker is not reachable from the public network.

### Stop conditions (not triggered)

Stop before editing if the current topic contract is unclear, if multiple incompatible MQTT clients exist, if credentials are required but unavailable, or if the only way to proceed is to grant unrestricted filesystem access.

### Definition of done (achieved)

A real MCP or HTTP invocation creates one file in an authorized temporary workspace and returns the actual correlated result. A second invocation with the same task ID is deterministic.

## Phase 2 — Reliable task lifecycle 🔄 NEXT (IN PROGRESS)

### Objective

Make tasks observable and recoverable beyond a single synchronous request.

### Atomic tasks

1. Introduce explicit task states: `queued`, `dispatched`, `running`, `completed`, `failed`, `blocked`, `expired`, `cancelled`.
2. Return `202 Accepted` plus `task_id`, `goal_id`, and status URL for long work.
3. Implement `GET /api/v1/goals/{goal_id}` or the existing equivalent.
4. Store task state and bounded result metadata.
5. Add idempotency by task ID.
6. Detect same ID with different payload and return conflict.
7. Add deadline-aware timeout handling.
8. Add bounded retries only for retryable transport failures.
9. Preserve audit records across retries.
10. Add cleanup/retention for old task records.

### Acceptance criteria

- caller can submit and later retrieve status;
- duplicate request does not duplicate a side effect;
- expired tasks do not execute;
- non-retryable policy failures are not retried;
- late responses cannot overwrite a newer state;
- status transitions are auditable.

### Definition of done

A task can survive an HTTP disconnect and still be queried to a terminal state without losing identity or result.

## Phase 3 — Secure network fabric

### Objective

Move from loopback-only operation to authenticated node-to-node operation.

### Atomic tasks

1. Define broker listener separation for local and network traffic.
2. Configure TLS certificate validation.
3. Decide username/password versus mTLS and document the decision.
4. Give every node a unique identity.
5. Create topic ACLs per gateway and node.
6. Disable anonymous network access.
7. Rotate credentials without code changes.
8. Restrict retained messages and executable task topics.
9. Add broker health and unauthorized-access logging.
10. Verify node isolation with a negative access test.

### Acceptance criteria

- a node cannot subscribe to another node's task topic;
- gateway can publish tasks but cannot impersonate a local executor outside policy;
- credentials are absent from Git;
- TLS verification fails closed;
- reconnects do not create duplicate execution.

### Definition of done

A remote node can operate securely over the network with verified identity, topic-level authorization, and observable reconnect behavior.

## Phase 4 — Multi-node orchestration

### Objective

Route work across nodes without turning scheduling into an authorization bypass.

### Atomic tasks

1. Define node registration and heartbeat schema.
2. Track TTL and stale-node eviction.
3. Advertise capabilities, limits, and workspace classes.
4. Select nodes using capability and policy filters.
5. Add backpressure and per-node concurrency limits.
6. Add cancellation and graceful drain.
7. Define retry ownership so only one component retries a task.
8. Record routing decisions in audit.
9. Handle node disappearance and in-flight tasks.

### Acceptance criteria

- only eligible nodes receive a task;
- stale nodes are not selected;
- capacity limits are respected;
- cancellation has deterministic semantics;
- routing is explainable from audit records.

## Phase 5 — MCP productization

### Objective

Make the fabric understandable and reliable for supported MCP hosts.

### Atomic tasks

1. Stabilize tool schemas.
2. Document input/output and error contracts.
3. Expose progress without pretending completion.
4. Map blocked, failed, expired, and human-approval states clearly.
5. Add MCP configuration examples with placeholders only.
6. Verify stdio and remote modes separately.
7. Ensure tool calls return real gateway/node results.

### Acceptance criteria

- an MCP host can discover tools;
- dispatch returns task identity;
- progress and terminal result are distinguishable;
- failures are actionable and not hidden.

## Phase 6 — Browser capability

### Objective

Add browser automation only as a bounded capability.

### Atomic tasks

1. Use isolated browser contexts.
2. Default to ephemeral profiles.
3. Enforce domain allowlists.
4. Confine uploads/downloads to workspaces.
5. Add timeout and resource budgets.
6. Pause for CAPTCHA, MFA, payment, credentials, account creation, and anti-bot friction.
7. Require human handoff for those events.

### Forbidden

No fingerprint spoofing, WebDriver masking, Canvas/WebGL/Audio spoofing, synthetic biometric movement, CAPTCHA bypass, proxy rotation for evasion, or personal browser-profile reuse.

## Phase 7 — Oracle deployment and CI/CD

### Prerequisites

Phase 1 must be real. Phase 3 security controls must be configured. Rollback and secret handling must be documented.

### Atomic tasks

1. Package gateway and client reproducibly.
2. Define environment-specific configuration.
3. Store secrets outside Git.
4. Add health/readiness checks.
5. Add resource limits for constrained nodes.
6. Deploy to a staging node first.
7. Verify MQTT connectivity and task lifecycle in staging.
8. Add protected GitHub Actions environments.
9. Define rollback and migration procedures.
10. Document cost and capacity assumptions.

### Definition of done

A staging deployment can be upgraded and rolled back without losing task identity or exposing secrets.

## Phase 8 — Operator experience

Only after the execution path is reliable:

- task timeline;
- node health;
- audit inspection;
- manual approvals;
- safe cancellation;
- dashboard and notifications.

## Global risks

- documentation can drift from code;
- duplicate MQTT delivery can duplicate side effects;
- gateway authorization can be mistaken for node authorization;
- unbounded retries can overload a node;
- public brokers can expose task metadata and credentials;
- browser features can expand scope faster than policy;
- cloud deployment can hide local integration failures.

## Global rollback rule

Every phase must be independently revertible. Preserve a known-good branch or commit before transport, schema, security, and deployment changes. Never force-push to resolve divergence.

## Local pull after publication

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
git log -3 --oneline
```

Expected result: clean working tree and the new documentation commit at `HEAD`.