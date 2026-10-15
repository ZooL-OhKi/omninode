# Phase 2.5 - Self-Hosting Autonomy Bootstrap (status)

Branch: feature/phase-2.5-autonomy (from feature/browse-rpc-mqtt). Not merged.

## Delivered (node1-gateway/)

- autonomy_core.py: RepoWorkspace (list/read/write/rollback, PROTECTED_PATHS, symlink and traversal denial,
  secret/ignored path filtering, redaction, snapshots) and VerificationExecutor (static presets, shell=False,
  16000-char output cap, verify_all fail-fast, sensitive env vars stripped).
- work_loop.py: SelfHostingWorkLoop and PerplexityHelper (urllib only). Legacy AutonomousWorkLoop untouched.
- autonomy_api.py: POST /api/v1/autonomy/run-step, POST /api/v1/autonomy/goals, GET /api/v1/autonomy/goals/{id}.
- autonomy_app.py: wires the router into main.app without editing main.py. Run: uvicorn autonomy_app:app
- test_autonomy.py, test_autonomy_api.py, test_main.py (rewritten for existing endpoints, MQTT mocked).

## Delivered (omniclient/)

- cdp_agent.go, web_agent.go: playwright import renamed to github.com/mxschmitt/playwright-go.
- mqtt_client.go: removed duplicate publishHeartbeat and startHeartbeatLoop (kept in heartbeat.go).
- ops_terraform.go: removed duplicate publishRes (kept in mqtt_client.go).
- main.go: StartWSServer(8080) called without assignment (function returns nothing).
- go.mod / go.sum: added mxschmitt/playwright-go v0.6201.1, modernc.org/sqlite v1.60.1 and transitive deps.

## Verification status (all green)

- Python: 59 passed, 1 skipped, 0 failed (pytest -q, real repo, Windows).
- Go: go vet clean, go test ok (github.com/ZooL-OhKi/omniclient 1.233s).
- git diff --check: clean.
- The 1 skipped test is pre-existing and unrelated to Phase 2.5.

## Not delivered

- Go MCP tools omninode_workspace_*, omninode_command_verify, omninode_autonomy_step and local dispatch in omniclient.
- MQTT dispatch for workspace.* / command.run on node-local. The endpoints run the loop in-process on the gateway.
- requirements.txt still pins aiomqtt==2.4.2 (nonexistent); local install used 2.4.0. Fix in a separate commit.
- MQTT topics are still omninode/nodes/... in main.py, not omninode/v1/nodes/{node_id}/...
- node1-gateway/.env is still tracked; rotate credentials and remove from history.
- MCP_SECRET still has a hard-coded default in main.py.

## Ordered queue for the next tasks

Human-only (security files are protected from autonomous edits):
1. Fix requirements.txt: aiomqtt==2.4.0.
2. Remove node1-gateway/.env from the repo and git history, rotate every credential it contained.
3. Remove the hard-coded default MCP_SECRET in main.py and require it from the environment.
4. Authenticate POST /api/v1/approve.
5. In workspace_manager.py: move the symlink check before resolve() and use atomic writes.
6. Delete or align the two legacy executors (command_executor.py, test_executor.py).

Autonomous candidates (after the Go side exists and verify_all is green):
7. Run the Phase 2.5 test suite in CI and gate merges on it.
8. Phase 3 groundwork: versioned RPC schema and error codes (schema_version 1 envelope).
9. Audit Transparency Log: Ed25519-signed entries chained in a Merkle tree.
10. Swarm Fabric v4.0 backlog, with three mandatory fixes:
   - keep per-node topics omninode/v1/nodes/{node_id}/tasks|responses|heartbeat over MQTT over WSS (443);
   - lifecycle_windows.go: use golang.org/x/sys/windows Job Objects with a real handle, never a PID;
   - spatial_pruner.js isElementCovered(): sample centre and inner points, not exact outer corners.
