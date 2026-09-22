# Omninode Architecture

## 1. Mission

Omninode is a distributed fabric for AI-assisted and autonomous work across trusted nodes. A remote AI can request work, but execution authority remains local to the node that owns the resource.

The architecture separates four concerns:

1. Intent: an AI or MCP client expresses a goal.
2. Coordination: the gateway validates and routes a task.
3. Transport: MQTT delivers the task and response.
4. Execution: the local node applies policy and performs the authorized operation.

This separation is intentional. MQTT delivery must never imply authorization.

## 2. Components

### External AI and MCP host

The AI-facing layer chooses a tool and submits structured input. It must receive a structured result rather than an assertion that work was performed.

### Go `omniclient`

`omniclient` has two roles:

- expose MCP tools such as node discovery and task dispatch;
- act as a lightweight node-side client that can communicate with the gateway or broker.

The Go client must not convert arbitrary model text into shell commands. It should pass structured tasks to a capability-aware executor.

### FastAPI gateway

The gateway provides HTTP APIs, tracks node state, validates request shape, and dispatches tasks through MQTT. It should return `202 Accepted` for work that is not completed within the request lifetime and expose a status lookup by goal or task ID.

The gateway is not the final authority over a local filesystem. It may route a task, but the node must authorize it again.

### MQTT broker

MQTT provides asynchronous delivery, heartbeat propagation, and request/reply coordination. Recommended topic shape:

```text
omninode/v1/nodes/{node_id}/tasks
omninode/v1/nodes/{node_id}/responses
omninode/v1/nodes/{node_id}/heartbeat
omninode/v1/nodes/{node_id}/events
```

A node subscribes only to its own task topic. A gateway subscribes only to authorized response topics.

### Local executor

The executor performs only named capabilities. The first capability is `workspace.write`, which accepts a registered workspace ID, a relative path, and bounded content. It must use atomic replacement and reject traversal, absolute paths, sensitive locations, oversized content, and symlink escapes.

## 3. Task lifecycle

```text
created
  -> validated
  -> queued
  -> dispatched
  -> running
  -> completed | failed | blocked | expired
```

Every transition should carry a task ID, goal ID, node ID, agent ID, timestamp, and audit record.

A task must include:

- schema version;
- task ID and goal ID;
- agent ID;
- target node ID;
- task type;
- capability;
- creation time;
- absolute deadline;
- structured payload.

## 4. MQTT request/reply

Use MQTT 5 request/reply properties where the client library supports them:

- response topic identifies the response destination;
- correlation data contains the request correlation identifier;
- the JSON body still contains `task_id` and `goal_id` for diagnostics and compatibility.

The gateway must maintain a thread-safe pending-request map keyed by correlation ID. A response must be rejected or quarantined if it has no matching pending request, wrong node identity, malformed JSON, or an expired deadline.

QoS 1 is appropriate for task delivery when the application implements idempotency. Retained messages must not be used for executable tasks.

## 5. Idempotency

The node must maintain a bounded result cache or persistent task record. For the same task ID:

- same payload: return the original result;
- different payload: return a conflict;
- expired task: do not execute;
- already running task: return an in-progress state.

Retries must be bounded and use deadline-aware backoff. Authorization failures are not retryable.

## 6. Security boundaries

The local node is the final security boundary. It must validate:

- authenticated node identity;
- agent and goal identity;
- capability;
- workspace registration;
- relative path containment after resolution;
- symlink behavior;
- content and output budgets;
- deadline and approval policy.

No component may turn an arbitrary `path`, `command`, or browser instruction into unrestricted host access.

## 7. Browser runtime

Browser execution is a separate capability. Use isolated browser contexts, ephemeral profiles by default, explicit domain allowlists, bounded uploads/downloads, and human handoff for CAPTCHA, MFA, payment, credential requests, account creation, or anti-bot friction.

Do not implement fingerprint spoofing, `navigator.webdriver` masking, WebGL or Canvas spoofing, movement biometrics, CAPTCHA bypass, proxy rotation for evasion, or use of personal browser profiles.

## 8. Operational phases

### Phase A: local vertical slice

Run broker, gateway, and one local node on loopback. Prove one authorized `workspace.write` operation.

### Phase B: reliable task lifecycle

Add `202` goal submission, status retrieval, idempotency, deadline handling, and persistence.

### Phase C: secured network fabric

Add TLS, per-node identity, topic ACLs, credential rotation, and network restrictions.

### Phase D: multi-node and cloud

Deploy only after the local vertical slice is observable and recoverable. Add health, heartbeats, capacity, and rollout controls.

## 9. Architectural invariants

- Transport does not grant authority.
- Every task is attributable.
- Every write is confined to a registered workspace.
- Deny is the default.
- Expired work is not executed.
- Remote models cannot silently elevate capabilities.
- Production deployment follows, rather than precedes, a working local vertical slice.