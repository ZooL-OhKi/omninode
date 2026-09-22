# Omninode Index

## Start here

1. `docs/AI_ONBOARDING.md` — prompt and reconstruction workflow.
2. `PROJECT_HANDOVER.md` — current truth and immediate gap.
3. `NEXT_STEPS.md` — detailed phase-by-phase execution plan.
4. `docs/REPOSITORY_MAP.md` — file ownership and trace strategy.
5. `ARCHITECTURE.md` — protocol and component model.
6. `SECURITY.md` — guardrails and threat boundaries.
7. `docs/OPERATIONS_RUNBOOK.md` — pull, validate, operate, recover.
8. `ROADMAP.md` — compact phase overview.

## Implementation map

### Python gateway: `node1-gateway/`

- `main.py`: FastAPI routes and runtime wiring.
- `mqtt_service.py`: MQTT connection, publish/subscribe, correlation, and pending requests.
- `audit.py`: thread-safe audit.
- `policy_engine.py`: capability authorization.
- `workspace_manager.py`: workspace registration and path confinement.
- `local_executor.py`: bounded `workspace.write`.
- `mqtt_task_protocol.py`: envelope validation.
- `command_executor.py`: allowlisted process execution.
- `work_loop.py`: bounded autonomous orchestration.
- `browser_runtime.py`: bounded browser capability scaffolding.

### Go client: `omniclient/`

- `main.go`: entry point and modes.
- `gateway_client.go`: gateway/MQTT client behavior.
- `mcp_server_test.go`: MCP tests.
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

## Source hygiene

Never treat these as source: `venv/`, `__pycache__/`, `.pytest_cache/`, binaries, secrets, backups, or temporary scripts.