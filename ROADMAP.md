# Omninode roadmap

## Completed baseline

- Documented the autonomous AI resident mission and architecture.
- Added the authenticated Python browse route.
- Added synchronous MQTT Request-Reply dispatch with pending-task cleanup.
- Added deterministic Go HTTP contract coverage using httptest.
- Added initial Python gateway tests for authentication and unavailable nodes.
- Hardened repository boundaries against virtual environments, binaries, secrets, caches, and local artifacts.

## Current phase: MQTT reliability

- Define and version request/response schemas.
- Add broker-backed integration tests in an isolated local environment.
- Cover concurrent tasks, timeout cleanup, duplicate responses, late responses, malformed payloads, offline nodes, reconnects, and worker restarts.
- Run the Go race detector.
- Add Python tests for every error mapping and route response contract.

## Next phases

1. Capability and policy enforcement.
2. Audit events, metrics, tracing, readiness, and liveness.
3. Standard Chromium browser runtime with isolated profiles and protected Playwright/CDP.
4. Controlled filesystem workspaces.
5. Resource-limited sandbox.
6. `run_sandbox_code` only after isolation and policy tests.
7. Additional MCP tools with explicit risk classification.
8. Approved system operations, staged deployment, rollback, backup, and recovery.

Do not implement unrestricted shell execution, CAPTCHA bypass, mass account creation, arbitrary host filesystem access, or a custom Chromium fork in the current phase.
