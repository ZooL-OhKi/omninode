# Phase 2.5 - Self-Hosting Autonomy Bootstrap (status)

Implemented and unit-tested (43 tests, run outside the repo CI):
- autonomy_core.py: RepoWorkspace (list/read/write/rollback, PROTECTED_PATHS, symlink and traversal denial,
  secret/ignored path filtering, redaction, snapshots) and VerificationExecutor (static presets, shell=False,
  16000-char output cap, verify_all fail-fast).
- work_loop.py: SelfHostingWorkLoop and PerplexityHelper (urllib only). Legacy AutonomousWorkLoop untouched.
- autonomy_api.py: POST /api/v1/autonomy/run-step, POST /api/v1/autonomy/goals, GET /api/v1/autonomy/goals/{id}.
- autonomy_app.py: wires the router into main.app without editing main.py.

Not done yet: Go MCP tools and MQTT dispatch for workspace.* / command.run, NEXT_STEPS.md and PROJECT_HANDOVER.md updates,
MQTT topic migration to omninode/v1/nodes/{node_id}/...
