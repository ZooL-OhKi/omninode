# Omninode Architecture

## Purpose

Omninode is a distributed fabric for AI-assisted and autonomous work across trusted nodes. It separates intent, coordination, transport, authorization, and execution so that no remote request automatically becomes host authority.

## Component model

### AI and MCP host

The AI chooses a typed tool and submits structured input. It must receive a structured result, not a claim that work happened.

### Go `omniclient`

`omniclient` is the lightweight integration surface. It exposes MCP-facing operations and participates in gateway/node communication. It must not turn model text into arbitrary shell commands.

### FastAPI gateway

The gateway exposes HTTP, validates request shape, tracks nodes and tasks, and publishes MQTT work. It is a coordinator, not the final authority over a local filesystem.

### MQTT broker

MQTT transports tasks, responses, heartbeats, and events. Recommended topics:

```text
omninode/v1/nodes/{node_id}/tasks
omninode/v1/nodes/{node_id}/responses
omninode/v1/nodes/{node_id}/heartbeat
omninode/v1/nodes/{node_id}/events
```

A node subscribes only to its own task topic. Executable task messages are never retained.

### Local node executor

The node validates the task again and dispatches only named capabilities. The first capability is `workspace.write`.

## Canonical task envelope

```json
{
  "schema_version": 1,
  "task_id": "uuid",
  "goal_id": "uuid",
  "agent_id": "agent-id",
  "node_id": "node-local",
  "task_type": "workspace.write",
  "capability": "workspace.write",
  "created_at": "2026-09-22T13:00:00Z",
  "deadline_at": "2026-09-22T13:05:00Z",
  "payload": {
    "workspace_id": "temporary",
    "path": "hello.txt",
    "content": "hello"
  }
}
```

Response envelope:

```json
{
  "schema_version": 1,
  "task_id": "uuid",
  "goal_id": "uuid",
  "node_id": "node-local",
  "status": "completed",
  "data": {
    "path": "hello.txt",
    "bytes_written": 5
  },
  "error": null
}
```

## Lifecycle

```text
created -> validated -> queued -> dispatched -> running
                                             |        |
                                             v        v
                                         completed  failed
                                             |
                                         blocked/expired
```

Every transition must be attributable to a task, goal, agent, node, timestamp, decision, and audit record.

## Request/reply

Use MQTT 5 response-topic and correlation-data properties when supported by the client library. Keep `task_id` and `goal_id` in the JSON body for diagnostics and compatibility.

The gateway needs a thread-safe pending map keyed by correlation ID. It must reject malformed, late, unknown, or wrong-node replies. QoS 1 is acceptable only when task execution is idempotent.

## Node execution boundary

The local executor must verify:

- node identity;
- agent and goal identity;
- capability;
- registered workspace;
- normalized relative path;
- symlink containment;
- size and time budgets;
- approval and deadline policy.

Transport delivery never bypasses these checks.

## Browser boundary

Browser support is an independent capability and must use isolated contexts, ephemeral profiles by default, domain allowlists, bounded transfers, and human handoff for CAPTCHA, MFA, payment, credential requests, account creation, or anti-bot friction.

No fingerprint spoofing, WebDriver masking, Canvas/WebGL/Audio spoofing, synthetic biometrics, evasion proxy rotation, CAPTCHA bypass, or personal browser-profile reuse.

## Deployment phases

1. Loopback local vertical slice.
2. Reliable task lifecycle and idempotency.
3. TLS and per-node topic ACLs.
4. Multi-node health, routing, capacity, and cancellation.
5. Cloud deployment and protected CI/CD.
6. Browser and dashboard capabilities.

Do not reverse this order.