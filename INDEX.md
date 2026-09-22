# Omninode Index

This is the compact navigation map. For complete onboarding use `docs/AI_ONBOARDING.md`.

## Read first

1. `docs/AI_ONBOARDING.md`
2. `PROJECT_HANDOVER.md`
3. `docs/REPOSITORY_MAP.md`
4. `ARCHITECTURE.md`
5. `SECURITY.md`
6. `docs/OPERATIONS_RUNBOOK.md`
7. `ROADMAP.md`

## Top-level files

- `README.md`: mission, philosophy, status, and immediate objective.
- `ARCHITECTURE.md`: boundaries, DTOs, topics, lifecycle, and invariants.
- `PROJECT_HANDOVER.md`: continuation point and verified state.
- `ROADMAP.md`: ordered milestones and acceptance criteria.
- `SECURITY.md`: threat model, capability rules, secrets, and forbidden behavior.
- `INDEX.md`: this map.

## Python gateway

Directory: `node1-gateway/`

- `main.py`: FastAPI application.
- `mqtt_service.py`: MQTT connection and request/reply layer.
- `audit.py`: audit record and sink behavior.
- `policy_engine.py`: capability decisions.
- `workspace_manager.py`: safe workspace paths and operations.
- `local_executor.py`: bounded atomic workspace write.
- `mqtt_task_protocol.py`: task envelope and deadline validation.
- `command_executor.py`: bounded allowlist process execution.
- `work_loop.py`: autonomous goal orchestration.
- `browser_runtime.py`: browser-policy/runtime scaffolding.

## Go client

Directory: `omniclient/`

- `main.go`: entry point and runtime wiring.
- `gateway_client.go`: gateway communication and task client behavior.
- `mcp_server_test.go`: MCP test coverage.
- `go.mod`, `go.sum`: dependencies.

## First symbols to trace

```text
dispatch_task
publish
subscribe
correlation
task_id
goal_id
workspace.write
validate_task
authorize
execute
heartbeat
```

Before changing a protocol, trace existing implementations and preserve topic names and DTOs.

## Never commit

- virtual environments;
- Python caches;
- compiled binaries;
- secrets, tokens, passwords, cookies, private keys, or `.env` files;
- temporary operator scripts unless deliberately maintained.