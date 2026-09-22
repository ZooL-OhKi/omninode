# Omninode Roadmap

The roadmap is deliberately execution-first. Each phase must produce a working, observable increment before the next phase begins.

## Phase 0 — Repository and safety baseline

Status: complete.

- FastAPI gateway exists.
- Go client exists.
- MQTT integration scaffolding exists.
- Policy, audit, workspace, executor, and work-loop modules exist.
- Branch `feature/browse-rpc-mqtt` is published.
- Unit checks pass.

## Phase 1 — Local operational vertical slice

Status: next.

Goal: perform one real authorized operation through the entire fabric.

Scope:

- start a broker on loopback;
- start the FastAPI gateway;
- start one local `omniclient` node;
- subscribe to the node-specific task topic;
- dispatch structured `workspace.write` task;
- validate task and capability locally;
- atomically create a file in a temporary workspace;
- publish a correlated response;
- expose the real result to MCP or HTTP.

Acceptance criteria:

- file is really created;
- result contains task and goal identity;
- invalid node, expired task, traversal, and unsupported capability are rejected;
- no arbitrary shell is executed;
- no public network exposure is required.

## Phase 2 — Reliable task lifecycle

Status: planned.

- `202 Accepted` goal submission;
- `GET /api/v1/goals/{goal_id}`;
- explicit queued/running/completed/failed/blocked/expired states;
- idempotency by task ID;
- duplicate delivery handling;
- bounded retry with deadline-aware backoff;
- durable task records, initially SQLite if needed;
- result and audit retention policy.

## Phase 3 — Secure network operation

Status: planned.

- MQTT TLS;
- per-node authentication or mTLS;
- topic ACLs;
- credential rotation;
- broker listener isolation;
- denial of anonymous public access;
- monitoring for unauthorized topic access.

## Phase 4 — Multi-node scheduling

Status: planned.

- node registration;
- heartbeats and TTL;
- capabilities advertisement;
- capacity and availability;
- routing policy;
- backpressure;
- cancellation;
- graceful node drain.

## Phase 5 — MCP productization

Status: planned.

- stable tool schemas;
- clear progress and error semantics;
- remote-agent configuration;
- operator documentation;
- compatibility testing with supported MCP hosts.

## Phase 6 — Browser capability

Status: planned and constrained.

- isolated browser contexts;
- domain allowlists;
- downloads/uploads bounded to workspaces;
- human handoff for CAPTCHA, MFA, payment, credentials, account creation, and anti-bot friction;
- no anti-detection or bypass features.

## Phase 7 — Cloud deployment

Status: planned after Phase 3.

- container or service packaging;
- Oracle staging deployment;
- secrets management;
- health checks;
- rollback;
- GitHub Actions with protected environments;
- resource budgets for constrained nodes.

## Phase 8 — Operator experience

Status: later.

- dashboard;
- task timeline;
- node health;
- audit inspection;
- manual approvals;
- safe cancellation.

## Explicit sequencing rule

Do not skip Phase 1 for dashboards, broad autonomy, browser automation, or cloud deployment. A working local vertical slice is the evidence base for every later decision.