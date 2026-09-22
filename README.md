# Omninode

Omninode is a distributed AI execution fabric. It connects external AI systems, MCP clients, a FastAPI gateway, MQTT-connected nodes, and local capability-bound executors.

The project is designed around a simple principle: an AI should be able to request useful work across trusted devices, but no remote model should receive unrestricted control of a host. Every operation must pass through explicit identity, capability, workspace, policy, deadline, and audit checks.

## Project philosophy

Omninode is not a remote shell and not a collection of obedient agents. It is a controlled fabric in which autonomous workers retain local authority boundaries while cooperating through a common protocol.

The design priorities are:

1. Local autonomy: a node decides locally whether an operation is permitted.
2. Least privilege: capabilities are narrow, explicit, temporary, and auditable.
3. Transport independence: MQTT carries messages; policy remains in the node executor.
4. Observable execution: every task has an identity, lifecycle, result, and audit trail.
5. Safe failure: invalid, expired, duplicated, or unauthorized work is rejected deterministically.
6. Incremental delivery: first make one real end-to-end path work, then add persistence, cloud deployment, and richer tools.

## Current branch and status

Active branch: `feature/browse-rpc-mqtt`

Current published commit at the time of this handover: `325eee3`

Validated locally before the documentation update:

- Python gateway tests: 15 passed, 1 warning.
- Python bytecode compilation: passed.
- Go tests: passed.
- `go vet ./...`: passed.
- `git diff --check`: passed.
- No commit or push should be forced over remote history.

The repository is not yet production-ready. The most important unfinished work is the real MQTT end-to-end path from an MCP dispatch to a local `omniclient` executor and back.

## Architecture at a glance

```text
External AI / MCP host
        |
        v
omniclient MCP server
        |
        v
Gateway client / FastAPI gateway
        |
        v
MQTT broker
        |
        v
Local omniclient node
        |
        v
Capability-bound executor
        |
        v
Authorized workspace or local resource
```

MQTT is a transport and coordination layer. It is not the authorization boundary. The local node must validate the complete task before touching the filesystem, starting a process, or controlling a browser.

## Implemented building blocks

The current branch contains or modifies:

- FastAPI gateway endpoints and gateway-side MQTT integration.
- Thread-safe MQTT request/reply support.
- Go `omniclient` gateway client and MCP-related code.
- Audit, policy, command-execution, workspace, and autonomous work-loop modules.
- Browser runtime policy scaffolding with human-handoff requirements for friction events.
- A local workspace executor supporting constrained atomic writes.
- Task validation for node identity, UUIDs, capability, task type, and deadlines.

## Immediate operational goal

Make this path work with a local broker and a temporary workspace:

```text
MCP dispatch_task
  -> gateway accepts task
  -> gateway publishes MQTT task
  -> local node receives task
  -> local node validates capability and workspace
  -> executor creates one authorized file
  -> local node publishes correlated response
  -> gateway/MCP returns the real result
```

The first real capability should remain `workspace.write`. Do not begin with arbitrary shell commands, Desktop-wide access, browser automation, or public cloud exposure.

## Local synchronization

After documentation or code is published remotely:

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
```

Do not use `git reset --hard` or `git push --force` unless an explicit recovery decision has been made and the affected commits are backed up.

## Recommended next actions

1. Pull this branch locally.
2. Inspect the actual MQTT interfaces in `node1-gateway/mqtt_service.py` and `omniclient/gateway_client.go`.
3. Implement the real local-node subscriber and dispatcher without changing the security model.
4. Use a broker on loopback only for the first operational run.
5. Send one `workspace.write` task to a temporary workspace.
6. Add persistence and retry only after the end-to-end result is real and observable.
7. Configure TLS and topic ACLs before connecting nodes over a network.

## Non-goals

Omninode must not implement anti-bot evasion, fingerprint spoofing, CAPTCHA bypass, unrestricted remote shell, credential harvesting, silent account creation, or uncontrolled access to personal profiles.

For the complete recovery context, read `PROJECT_HANDOVER.md`. For the task sequence, read `ROADMAP.md`. For security rules, read `SECURITY.md`. For file ownership and navigation, read `INDEX.md`.