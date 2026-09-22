# Omninode security model

## Core principles

- Default deny.
- Least privilege.
- Explicit capability grants.
- Isolated workspaces.
- No implicit secret inheritance.
- Network egress denied by default for sandboxed execution.
- Every consequential action auditable.
- High-risk and destructive actions require an approval policy or explicit human confirmation.

## Agent capabilities

Capabilities should be assigned to an agent, node, task, and tool scope. A capability should specify the permitted operation, resource, path/domain, duration, and budget. Capabilities should expire and should not silently expand because a task failed.

## Filesystem

File operations must be restricted to configured workspaces. Deny path traversal, host root access, secret stores, device files, Docker sockets, SSH keys, and unrelated service data. Log reads and writes when they affect protected or shared workspaces. Prefer snapshots, patches, and rollback for important changes.

## Processes and sandbox

Do not expose unrestricted shell execution. Future sandbox execution must use an isolated runtime with CPU, memory, process, filesystem, output, and time limits. Network access is denied unless a narrowly scoped allowlist grants it. Secrets and host credentials must not be inherited.

## Browser

Use isolated Chromium profiles per agent or task. Protect Playwright/CDP endpoints on localhost or an authenticated private network. Apply domain allowlists and control downloads, uploads, cookies, storage, and credentials. Keep browser actions auditable.

CAPTCHA and MFA should cause a pause, a human handoff, or an authorized service flow. Omninode must not bypass anti-abuse protections. Account creation and automated web actions must comply with the target service's rules, applicable law, and rate limits.

## Network and secrets

Use authenticated MQTT connections and TLS where available. Keep API keys, broker credentials, cookies, and cloud credentials outside source control. Inject secrets only into the smallest process scope that needs them. Rotate credentials and record access events without logging secret values.

## Audit and response

Record agent ID, task ID, tool, node, timestamps, policy decision, resource, result, and error code. Provide liveness and readiness signals separately. Use circuit breakers and rate limits to prevent runaway loops. Preserve enough evidence to reconstruct autonomous actions without storing sensitive content unnecessarily.

## Security testing

Test malformed inputs, path traversal, unauthorized headers, duplicate and late MQTT replies, broker reconnects, browser session isolation, output limits, sandbox escape attempts, secret leakage, and policy bypasses before enabling higher-risk capabilities.
