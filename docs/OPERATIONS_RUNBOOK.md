# Omninode Operations Runbook

## Scope

This runbook covers safe repository synchronization, local validation, the first loopback runtime, and recovery from common Git/rebase states.

## Synchronize local checkout

```powershell
Set-Location A:\omninode
git fetch origin
git pull --ff-only origin feature/browse-rpc-mqtt
git status --short
git log -3 --oneline
```

Expected result: clean status, current branch tracking `origin/feature/browse-rpc-mqtt`, and no untracked temporary script unless intentionally maintained.

Never solve ordinary divergence with `reset --hard` or force-push.

## Validate code

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

A command must be considered passed only when its exit code is zero. Deprecation warnings are not failures unless the project policy changes.

## Local runtime sequence

Do not expose the broker publicly for the first run.

1. Start a loopback broker.
2. Start FastAPI on `127.0.0.1`.
3. Start one node client with a stable node ID.
4. Register a temporary workspace.
5. Dispatch one structured `workspace.write` task.
6. Confirm the file and correlated response.
7. Stop services and inspect audit output.

Keep credentials in environment variables. Do not put them in commands that will be committed or shared.

## Operational acceptance

A real vertical slice must prove:

- task publication;
- node-specific subscription;
- validation and policy decision;
- real file write in an authorized temporary workspace;
- response publication;
- response correlation;
- rejection of unauthorized path/capability;
- bounded timeout behavior.

## Git recovery

### Rebase in progress

```powershell
git status
git diff --name-only --diff-filter=U
```

Resolve only the listed files, stage them, and continue:

```powershell
git add <resolved-files>
git -c core.editor=true rebase --continue
```

Abort safely if necessary:

```powershell
git rebase --abort
```

### Non-fast-forward push

```powershell
git fetch origin
git branch backup/before-rebase
git rebase origin/feature/browse-rpc-mqtt
git diff --check
git push -u origin feature/browse-rpc-mqtt
```

Never force-push without an explicit recovery decision.

## Failure diagnosis

### Gateway starts but task never completes

Inspect broker connectivity, exact topic names, node subscription, node ID, deadline, pending-request map, and response correlation. Do not increase timeouts blindly.

### Node receives but blocks task

Inspect policy decision, workspace registration, path normalization, capability spelling, agent/goal identity, and audit records.

### File is not created

Inspect executor dispatch, workspace root, relative path, symlink checks, and atomic replace errors. Do not widen path permissions as a quick fix.

### Response is lost

Inspect response topic, correlation data, task ID, pending map lifetime, QoS, and duplicate handling.

### Pull conflicts

Preserve a backup branch, inspect conflict files, resolve intentionally, run validation, then push normally.

## Production gate

Before any network or Oracle deployment:

- TLS/mTLS configured;
- per-node credentials and ACLs configured;
- anonymous access disabled;
- secrets outside Git;
- health and rollback defined;
- real local vertical slice proven;
- audit and failure handling observable.