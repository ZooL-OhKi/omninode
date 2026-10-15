# Phase 2.5 - Self-Hosting Autonomy Bootstrap (status)

Branch: feature/phase-2.5-autonomy (from feature/browse-rpc-mqtt). Not merged.

## Delivered (node1-gateway/)

- autonomy_core.py: RepoWorkspace (list/read/write/rollback, PROTECTED_PATHS, symlink and traversal denial,
  secret/ignored path filtering, redaction, snapshots) and VerificationExecutor (static presets, shell=False,
  16000-char output cap, verify_all fail-fast, sensitive env vars stripped).
- work_loop.py: SelfHostingWorkLoop and PerplexityHelper (urllib only). Legacy AutonomousWorkLoop untouched.
- autonomy_api.py: POST /api/v1/autonomy/run-step, POST /api/v1/autonomy/goals, GET /api/v1/autonomy/goals/{id}.
- autonomy_app.py: wires the router into main.app without editing main.py. Run: uvicorn autonomy_app:app
- test_autonomy.py, test_autonomy_api.py.

## Verification status (read this first)

- 43 tests passed in an isolated sandbox against copies of these files and minimal copies of audit.py,
  policy_engine.py and task_store.py. The 5 HTTP endpoint tests were NOT executed there (FastAPI missing).
- NOT run on the real repo: pytest (full suite), python -m compileall, go test, go vet, git diff --check.
- Run them before merging. Do not merge on red.

## Not delivered

- Go side: MCP tools omninode_workspace_*, omninode_command_verify, omninode_autonomy_step and local dispatch in
  omniclient. Not written because it cannot be compiled or tested from the authoring environment.
- MQTT dispatch for workspace.* / command.run on node-local. The endpoints run the loop in-process on the gateway.
- Updates to NEXT_STEPS.md and PROJECT_HANDOVER.md (both are stale: e.g. NEXT_STEPS says the task store is not
  persistent, but task_store.py uses SQLite).
- MQTT topics are still omninode/nodes/... in main.py, not omninode/v1/nodes/{node_id}/...

## Ordered queue for the next tasks

Human-only (security files are protected from autonomous edits):
1. Remove node1-gateway/.env from the repo and git history, rotate every credential it contained.
2. Remove the hard-coded default MCP_SECRET in main.py and require it from the environment.
3. Authenticate POST /api/v1/approve.
4. In workspace_manager.py: move the symlink check before resolve() (it can never trigger today) and use atomic writes.
5. Delete or align the two legacy executors (command_executor.py, test_executor.py): both allow python/go with free arguments.

Autonomous candidates (after the Go side exists and verify_all is green):
6. Run the Phase 2.5 test suite in CI and gate merges on it.
7. Phase 3 groundwork: versioned RPC schema and error codes (schema_version 1 envelope).
8. Audit Transparency Log: Ed25519-signed entries chained in a Merkle tree.
9. Swarm Fabric v4.0 backlog, with three mandatory fixes:
   - keep per-node topics omninode/v1/nodes/{node_id}/tasks|responses|heartbeat over MQTT over WSS (443), not flat omni/swarm/* topics;
   - lifecycle_windows.go: obtain a handle with windows.OpenProcess and use golang.org/x/sys/windows Job Objects
     (JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE), never pass a PID as a handle;
   - spatial_pruner.js isElementCovered(): sample the centre and inner points (2px offset), check width/height > 0 and visibility, not the exact outer corners.
