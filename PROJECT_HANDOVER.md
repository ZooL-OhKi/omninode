# Omninode project handover

## Mission

Omninode hosts autonomous AI residents continuously on Oracle servers. The resident AI is intended to plan, execute, inspect, repair, and document work directly using the resources of its node: files, code, processes, browser sessions, and approved local tools. Omninode is not only a passive collection of remote commands.

Runtime controls remain mandatory: identity, capabilities, workspace restrictions, network policy, secret isolation, resource budgets, audit logging, and approval for destructive or high-risk actions.

## Verified baseline (Phase 2.5)

- Python gateway exposes authenticated /mcp and public /api/v1/nodes; autonomy endpoints are wired via autonomy_app.py.
- autonomy_core.py provides RepoWorkspace (confined list/read/write/rollback with PROTECTED_PATHS, symlink and traversal denial, secret filtering, redaction, snapshots) and VerificationExecutor (static presets only, shell=False, 16000-char output cap, verify_all fail-fast).
- work_loop.py provides SelfHostingWorkLoop (READ_CONTEXT -> GENERATE_OR_REFINE_PATCH -> WORKSPACE_WRITE -> VERIFY_SUITE -> SELF_HEAL max 3 -> COMMIT_OR_ROLLBACK) and PerplexityHelper (urllib only, PERPLEXITY_API_KEY / PERPLEXITY_MODEL).
- autonomy_api.py exposes POST /api/v1/autonomy/run-step, POST /api/v1/autonomy/goals, GET /api/v1/autonomy/goals/{id}; capabilities are granted for 15 minutes and checked by PolicyEngine; state is persisted in tasks.db via task_store.
- omniclient builds and tests green: playwright import renamed to github.com/mxschmitt/playwright-go, duplicate declarations removed, StartWSServer call fixed, dependencies added to go.mod/go.sum.
- test_main.py rewritten for existing endpoints (/api/v1/nodes, /mcp with MQTT mocked).
- pytest: 59 passed, 1 skipped, 0 failed. go vet: clean. go test: ok. git diff --check: clean.

## Known issues (do not merge without fixing)

- requirements.txt pins aiomqtt==2.4.2, which does not exist on PyPI. Local install used 2.4.0.
- node1-gateway/.env is tracked in git. Rotate every credential it contains and remove the file from history.
- main.py has a hard-coded default MCP_SECRET ("super-secret-mcp-token"). Remove it and require the env var.
- POST /api/v1/approve is unauthenticated.
- workspace_manager.py checks is_symlink() after resolve(), so the check can never trigger; writes are not atomic.
- command_executor.py and test_executor.py allow python/go with free arguments (arbitrary code execution). The new autonomy path does not use them, but they must be removed or aligned.
- MQTT topics are still omninode/nodes/... in main.py, not omninode/v1/nodes/{node_id}/...

## Current phase

Phase 2.5 (Self-Hosting Autonomy Bootstrap) is code-complete and test-green on the feature branch. It is NOT merged into feature/browse-rpc-mqtt.

Next phase: fix the known issues above, then Phase 3 (versioned RPC schema, Audit Transparency Log with Ed25519/Merkle) and the Swarm Fabric v4.0 backlog.

## Validation

```powershell
Set-Location A:\omninode\node1-gateway
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\python.exe -m compileall .

Set-Location A:\omninode\omniclient
go vet ./...
go test ./...

Set-Location A:\omninode
git diff --check
git status --short
```

No commit or push should occur without review of the complete diff.
