# Omninode Security Model

## Core position

All remote task input is untrusted. Authentication identifies a caller; authorization is a separate decision. The local node is the final security boundary.

## Trust zones

```text
AI/MCP input -> gateway -> MQTT transport -> local node policy -> authorized resource
```

A broker may deliver a message. It cannot grant permission to execute it.

## Capability model

Capabilities must be explicit, narrow, scoped to agent/goal/node/resource, time-limited, budget-limited, revocable, and auditable. Default is deny.

Initial capability: `workspace.write` only.

It does not imply:

- arbitrary shell execution;
- arbitrary file reads;
- credential access;
- Desktop-wide access;
- browser control;
- account creation;
- network access.

## Workspace confinement

Use registered workspace IDs and relative paths. Resolve paths and verify containment after resolution. Reject:

- absolute paths;
- `..` traversal;
- symlink escapes;
- `.ssh`, `.env`, key, token, credential, and secret locations;
- excessive file size or count;
- unregistered workspace roots.

Use atomic writes. Audit action, identity, resource, decision, policy version, and bounded result metadata without storing unnecessary secrets or file content.

## Command execution

Do not execute arbitrary shell text from an AI. Future process capabilities must use argv allowlists, `shell=false`, minimal environment, confined cwd, timeout, output limits, resource limits, and audit.

## MQTT

Loopback unauthenticated MQTT is permitted only for local development while inaccessible from the network. Network operation requires TLS/mTLS, per-node identity, ACLs, unique client IDs, non-retained executable tasks, bounded QoS, and credential rotation.

Recommended topic permissions:

```text
gateway:
  write omninode/v1/nodes/+/tasks
  read  omninode/v1/nodes/+/responses

node-local:
  read  omninode/v1/nodes/node-local/tasks
  write omninode/v1/nodes/node-local/responses
  write omninode/v1/nodes/node-local/heartbeat
```

Never expose an anonymous administrative broker publicly.

## Browser

Use isolated contexts, ephemeral profiles, domain allowlists, bounded transfers, and human handoff for CAPTCHA, MFA, payments, credentials, account creation, and anti-bot friction.

Forbidden: fingerprint spoofing, WebDriver masking, Canvas/WebGL/Audio spoofing, synthetic biometric motion, proxy rotation for evasion, CAPTCHA bypass, and personal profile reuse.

## Secrets

Never commit keys, passwords, MQTT credentials, private certificates, cookies, personal profiles, `.env`, `venv`, caches, or generated binaries. Rotate anything exposed in source or terminal output.

## Audit

Audit records should include audit ID, UTC timestamp, task ID, goal ID, agent ID, node ID, action, resource, policy version, decision, reason, and bounded result metadata.

## Security acceptance

The local vertical slice is acceptable only when:

- valid task succeeds;
- wrong node is blocked;
- unsupported capability is blocked;
- expired task is not executed;
- traversal and symlink escapes are blocked;
- duplicate delivery is controlled;
- another node's topic cannot be read or written;
- actual result is returned to the caller.