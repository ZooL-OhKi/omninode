# Omninode Security Model

## Security position

Omninode treats every remote request as untrusted input. Authentication identifies a caller; it does not grant permission to perform arbitrary work. Authorization is capability-based and must be re-evaluated at the node that owns the resource.

## Trust zones

```text
Untrusted AI / MCP input
        |
        v
Gateway validation and routing
        |
        v
MQTT transport
        |
        v
Local node policy boundary
        |
        v
Registered workspace or explicitly approved resource
```

The local node is the final authority. The gateway, broker, and remote AI cannot bypass local policy.

## Capability rules

Capabilities must be:

- explicit;
- narrow;
- bound to agent, goal, node, and resource;
- time-limited;
- budget-limited;
- revocable;
- auditable;
- default-deny.

The first capability is `workspace.write`. It must not imply shell execution, reading arbitrary files, credential access, browser control, or access to the real Desktop.

## Workspace rules

Every filesystem operation must use a registered workspace ID. Paths must be relative to that workspace. Resolve the path and verify containment after resolution. Reject:

- absolute paths;
- `..` traversal;
- symlink escapes;
- `.ssh`, `.env`, secrets, key, token, and credential paths;
- oversized files;
- excessive file counts;
- paths outside the registered root.

Use atomic temporary-file replacement for writes. Record the workspace, relative path, actor, goal, task, decision, and result without logging file secrets or content unnecessarily.

## Command execution

The default is no arbitrary command execution. If a future capability permits a process, it must use an explicit argv allowlist, `shell=false`, bounded environment, confined working directory, timeout, output budget, and audit record. Never accept a shell command string from an AI as an executable instruction.

## MQTT security

Local development may use a loopback broker without TLS only while the broker is inaccessible from the network. Any network deployment must use:

- TLS;
- per-client authentication or mTLS;
- topic ACLs;
- unique client IDs;
- non-retained executable task messages;
- QoS selected together with application idempotency;
- credential rotation;
- broker monitoring.

Recommended authorization:

```text
gateway:
  write omninode/v1/nodes/+/tasks
  read  omninode/v1/nodes/+/responses

node-local:
  read  omninode/v1/nodes/node-local/tasks
  write omninode/v1/nodes/node-local/responses
  write omninode/v1/nodes/node-local/heartbeat
```

Never use anonymous public access or a shared administrator account for production.

## Browser security

Browser sessions must be isolated and ephemeral by default. Use explicit domain allowlists, bounded file transfers, capability checks, and human handoff for CAPTCHA, MFA, payment, credentials, account creation, or anti-bot challenges.

Forbidden behavior includes fingerprint spoofing, WebDriver masking, Canvas/WebGL/Audio spoofing, synthetic biometric movement, proxy rotation for evasion, CAPTCHA bypass, and use of personal browser profiles.

## Secrets

Never commit:

- API keys;
- passwords;
- MQTT credentials;
- private keys;
- certificates with private material;
- cookies;
- personal browser profiles;
- `.env` files;
- local virtual environments.

Use environment variables or an external secret store and rotate any secret that appears in a terminal transcript or source file.

## Audit requirements

Audit records should include:

- audit ID;
- UTC timestamp;
- agent ID;
- goal ID;
- task ID;
- node ID;
- action;
- resource;
- policy version;
- allow/deny decision;
- reason;
- bounded result metadata.

Do not store secrets or unnecessary payload content in audit logs.

## Incident response

If a credential or private key is exposed:

1. revoke or rotate it immediately;
2. inspect broker and gateway logs;
3. invalidate affected capabilities;
4. preserve the relevant audit records;
5. remove the secret from future commits;
6. review the scope of any task executed with that credential.

## Security acceptance criteria

A milestone is not secure merely because unit tests pass. The operational acceptance test must demonstrate that:

- a valid task succeeds;
- an invalid capability is blocked;
- an expired task is not executed;
- traversal and symlink escapes are blocked;
- duplicate delivery does not create uncontrolled side effects;
- the broker cannot be used to reach another node’s task topic;
- the actual result is returned to the requesting agent.