# Omninode roadmap

## Phase 1: baseline and handover

- Keep README, INDEX, handover, architecture, security, and roadmap consistent.
- Preserve the tested Go HTTP client and Python gateway baseline.
- Remove generated binaries and keep secrets out of Git.

## Phase 2: RPC and MQTT reliability

- Version request and response schemas.
- Define stable task states and error codes.
- Add a local broker-backed integration environment.
- Test concurrent tasks, timeouts, cleanup, duplicate and late responses, malformed payloads, offline nodes, reconnects, and worker restarts.
- Run the Go race detector where applicable.

## Phase 3: capabilities and policy

- Define agent, node, task, and tool identities.
- Implement default-deny capability checks.
- Add workspace, network, process, secret, and resource policies.
- Add audit events and correlation across HTTP, MQTT, worker, browser, and filesystem actions.

## Phase 4: browser runtime

- Start with standard Chromium.
- Integrate Playwright/CDP with isolated profiles.
- Protect CDP and define domain allowlists.
- Add controlled downloads/uploads and browser action logs.
- Support pause and human handoff for CAPTCHA, MFA, payments, and other high-risk flows.
- Reconsider a custom Chromium build only if standard Chromium cannot satisfy a demonstrated requirement.

## Phase 5: filesystem and sandbox

- Add scoped workspace listing, reading, writing, and patching.
- Add rollback or snapshot support where practical.
- Build a resource-limited sandbox with network deny-by-default.
- Test isolation, output limits, timeouts, and cleanup.

## Phase 6: MCP tools

- Add node health and diagnostics.
- Add controlled workspace tools.
- Implement `run_sandbox_code` only after the sandbox and policy layers are verified.
- Add approved process and service operations.
- Classify every tool by risk and required approval.

## Phase 7: operations

- Add metrics, tracing, alerting, readiness and liveness checks.
- Define backup and recovery procedures.
- Add staged deployment and rollback.
- Add policy review and security testing for autonomous operation.
