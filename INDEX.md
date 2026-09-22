# Omninode Repository Index

This file is the navigation map for humans and new AI contributors.

## Start here

Read files in this order:

1. `README.md` — project mission, current status, and immediate operational objective.
2. `PROJECT_HANDOVER.md` — exact continuation point, verified commands, unresolved work, and recovery instructions.
3. `ARCHITECTURE.md` — component boundaries, MQTT flow, lifecycle, and invariants.
4. `SECURITY.md` — non-negotiable security rules.
5. `ROADMAP.md` — ordered implementation plan.

## Python gateway

Directory: `node1-gateway/`

Important files:

- `main.py`: FastAPI application and HTTP-facing behavior.
- `mqtt_service.py`: broker connection, publish/subscribe, and request/reply coordination.
- `audit.py`: audit records and sinks.
- `policy_engine.py`: capability and authorization decisions.
- `command_executor.py`: bounded allowlisted process execution.
- `workspace_manager.py`: path confinement, snapshots, diffs, and workspace operations.
- `local_executor.py`: constrained local workspace write implementation.
- `mqtt_task_protocol.py`: task identity and deadline validation.
- `work_loop.py`: autonomous goal orchestration.
- `browser_runtime.py`: browser policy/runtime scaffolding.

Python tests include gateway tests, MQTT tests, executor tests, workspace/work-loop tests, and browser policy tests.

## Go client

Directory: `omniclient/`

Important files:

- `main.go`: client entry point and runtime wiring.
- `gateway_client.go`: gateway HTTP/MQTT client behavior.
- `mcp_server_test.go`: MCP-related test coverage.
- `go.mod` and `go.sum`: dependency declarations.

Before extending Go behavior, inspect existing interfaces rather than creating a second MQTT client or a second request/reply implementation.

## Configuration and runtime

Configuration must come from environment variables or local untracked configuration. Never commit credentials, private keys, `.env` files, virtual environments, caches, or compiled binaries.

The first runtime should use:

```text
broker: loopback only
node ID: explicit and stable
workspace: temporary registered directory
capability: workspace.write
transport: QoS 1, non-retained tasks
```

## Current continuation point

The last published implementation commit is `325eee3` on `feature/browse-rpc-mqtt`. The next engineering task is to make the real MQTT task path executable end-to-end with one local node.

## Search strategy for a new contributor

Search these symbols first:

- `dispatch_task`
- `publish`
- `subscribe`
- `correlation`
- `task_id`
- `goal_id`
- `workspace.write`
- `validate_task`
- `authorize`
- `execute`
- `heartbeat`

Trace the call graph before editing. Preserve existing topic names and DTOs unless a migration is explicitly documented.

## Exclusions

Do not include or inspect as source:

- `venv/`;
- `__pycache__/`;
- `.pytest_cache/`;
- generated binaries;
- secrets and credentials;
- temporary scripts such as `update_omninode_loop.ps1` unless deliberately promoted to a maintained tool.