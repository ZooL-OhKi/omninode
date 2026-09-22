# Omninode Roadmap

See `NEXT_STEPS.md` for the detailed execution plan. This file provides the phase-level view.

## Phase 0 — Baseline and reconstruction

Status: complete.

Repository, branch, implementation checkpoint, documentation, security model, repository map, onboarding prompt, and operations runbook are available.

## Phase 1 — Real local vertical slice

Status: next.

MCP/HTTP → FastAPI → MQTT → local `omniclient` → policy → `workspace.write` → correlated response.

The first result must be a real file in a temporary registered workspace, not a mock.

## Phase 2 — Reliable task lifecycle

Status: planned.

202 responses, status endpoint, durable task identity, explicit states, deadlines, idempotency, bounded retries, duplicate control, and audit retention.

## Phase 3 — Secure network fabric

Status: planned.

TLS/mTLS, per-node identity, topic ACLs, credential rotation, anonymous-access denial, reconnect behavior, and unauthorized-access monitoring.

## Phase 4 — Multi-node orchestration

Status: planned.

Registration, heartbeats, capability advertisement, routing, backpressure, concurrency limits, cancellation, drain, and retry ownership.

## Phase 5 — MCP productization

Status: planned.

Stable schemas, progress semantics, configuration examples, supported-host compatibility, and real error propagation.

## Phase 6 — Browser capability

Status: planned and constrained.

Isolated contexts, ephemeral profiles, domain allowlists, bounded transfers, human handoff, and no evasion/bypass features.

## Phase 7 — Oracle deployment and CI/CD

Status: blocked until Phases 1 and 3 are complete.

Packaging, staging, secrets, health, rollback, protected workflows, and resource budgets.

## Phase 8 — Dashboard and operator experience

Status: later.

Timeline, node health, audit viewer, approvals, cancellation, and dashboard.

## Sequencing rule

Do not move to dashboards, broad autonomy, browser automation, or public cloud deployment until Phase 1 has produced a real end-to-end result and Phase 3 has established network security.