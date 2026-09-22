# Omninode Roadmap

The roadmap is execution-first. Every phase must leave the system in a more observable and recoverable state.

## Phase 0 — Baseline and documentation

Status: complete.

- repository and branch identified;
- FastAPI gateway and Go client present;
- MQTT scaffolding present;
- policy, audit, workspace, executor, browser, and work-loop modules present;
- local checks previously passed;
- detailed handover, repository map, onboarding guide, and operations runbook available.

## Phase 1 — Real local vertical slice

Status: next.

Implement exactly one operation:

```text
MCP/HTTP -> FastAPI -> MQTT -> local omniclient -> policy -> workspace.write -> MQTT response
```

Acceptance:

- broker runs on loopback;
- one node subscribes only to its own task topic;
- task has identity, deadline, capability, and structured payload;
- file is actually created in a temporary registered workspace;
- response contains matching IDs and real metadata;
- invalid node, capability, deadline, traversal, and workspace are rejected;
- no shell string is executed.

## Phase 2 — Reliable task lifecycle

Status: planned.

- `202 Accepted` for queued work;
- status endpoint by goal ID;
- queued/running/completed/failed/blocked/expired states;
- idempotency and duplicate handling;
- bounded retry and deadline-aware backoff;
- SQLite task history if needed;
- audit retention and cleanup.

## Phase 3 — Secure network fabric

Status: planned.

- TLS or mTLS;
- per-node identity;
- topic ACLs;
- secret rotation;
- isolated broker listeners;
- monitoring and alerting.

## Phase 4 — Multi-node orchestration

Status: planned.

- registration and heartbeat TTL;
- capability advertisement;
- capacity and availability;
- routing and backpressure;
- cancellation and node drain;
- deterministic retry ownership.

## Phase 5 — MCP productization

Status: planned.

- stable schemas;
- progress and error semantics;
- supported-host configuration;
- compatibility matrix;
- operator documentation.

## Phase 6 — Browser capability

Status: planned and constrained.

- isolated ephemeral contexts;
- domain allowlists;
- bounded uploads/downloads;
- human handoff for friction;
- no anti-detection or bypass features.

## Phase 7 — Cloud deployment

Status: blocked until Phase 3.

- Oracle staging;
- packaging;
- protected GitHub Actions;
- secrets management;
- health checks;
- rollback;
- resource budgets.

## Phase 8 — Operator experience

Status: later.

- dashboard;
- task timeline;
- node health;
- audit viewer;
- approval UI;
- cancellation.

## Sequencing rule

Do not prioritize dashboard, broad autonomy, browser automation, or cloud deployment over the first real local task result.