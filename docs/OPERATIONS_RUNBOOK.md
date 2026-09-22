# Omninode Operations Runbook

## Purpose

Use this runbook to synchronize, inspect, validate, operate, and recover Omninode without relying on conversation history.

## Pull the latest branch

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
git log -3 --oneline
```

If the working tree is not clean, stop and inspect local changes. Do not use destructive reset commands as a shortcut.

## Read before operating

```text
docs/AI_ONBOARDING.md
PROJECT_HANDOVER.md
NEXT_STEPS.md
docs/REPOSITORY_MAP.md
ARCHITECTURE.md
SECURITY.md
```

## Validation baseline

```powershell
Set-Location A:\omninode\node1-gateway
& ".\venv\Scripts\python.exe" -m pytest -q
& ".\venv\Scripts\python.exe" -m compileall .

Set-Location ..\omniclient
gofmt -d .
go test ./...
go vet ./...

Set-Location ..
git diff --check
```

Treat a command as passed only if its exit code is zero. Warnings must be reported, not silently ignored.

## Phase 1 runtime procedure

Use only loopback for the first real task.

1. Confirm broker process and listener.
2. Start FastAPI on `127.0.0.1`.
3. Start one node client with a stable node ID.
4. Create/register a temporary workspace.
5. Submit one structured `workspace.write` task.
6. Observe publish, receipt, policy decision, execution, and response.
7. Verify the actual file and byte count.
8. Submit an invalid path and confirm denial.
9. Stop services cleanly.
10. Update `PROJECT_HANDOVER.md` with exact evidence.

## Evidence required

Record:

- commit SHA;
- broker address and security mode;
- node ID;
- task ID and goal ID;
- workspace ID;
- request and response status;
- created path and byte count;
- audit IDs;
- rejection results;
- commands and exit codes.

Do not record secrets or full sensitive payloads.

## Troubleshooting matrix

### No gateway publish

Inspect route binding, API authentication, request validation, gateway MQTT connection, and publish return code.

### No node receipt

Inspect exact topic, node ID, subscription timing, broker ACL, QoS, and retained-message behavior.

### Node blocks task

Inspect task schema, deadline, capability, agent/goal identity, workspace registration, normalized path, and policy/audit output.

### File missing

Inspect executor dispatch, workspace root, parent directory creation, atomic temporary file, replacement error, and process permissions.

### Response missing

Inspect response topic, correlation data, task ID, pending map, response timeout, and duplicate handling.

### Task executes twice

Inspect QoS, redelivery, task cache, acknowledgment timing, and whether the executor is idempotent.

## Rebase and push recovery

```powershell
git status
git diff --name-only --diff-filter=U
```

For a rebase conflict, resolve only listed files, stage them, and continue:

```powershell
git add <resolved-file>
git -c core.editor=true rebase --continue
```

For non-fast-forward:

```powershell
git fetch origin
git branch backup/before-rebase
git rebase origin/feature/browse-rpc-mqtt
git diff --check
git push -u origin feature/browse-rpc-mqtt
```

Never force-push by default.

## Production gate

Before Oracle or public network deployment:

- Phase 1 evidence exists;
- TLS/mTLS is configured;
- ACLs isolate node topics;
- anonymous access is disabled;
- credentials are externalized and rotatable;
- readiness and rollback exist;
- task state and audit are observable.