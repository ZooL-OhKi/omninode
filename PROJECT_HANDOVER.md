# Omninode project handover

## Mission

Omninode hosts autonomous AI residents continuously on Oracle servers. The resident AI is intended to plan, execute, inspect, repair, and document work directly using the resources of its node: files, code, processes, browser sessions, and approved local tools. Omninode is not only a passive collection of remote commands.

Runtime controls remain mandatory: identity, capabilities, workspace restrictions, network policy, secret isolation, resource budgets, audit logging, and approval for destructive or high-risk actions.

## Verified baseline

- Python gateway exposes authenticated `POST /api/v1/browse`.
- MQTT service has synchronous Request-Reply dispatch with `PendingTask`, `threading.Event`, locking, timeout handling, and cleanup in `finally`.
- Go gateway client has deterministic local HTTP contract coverage.
- Python tests now cover API-key rejection and no-online-node handling.
- Repository ignore rules exclude venvs, Python caches, Go binaries, secrets, logs, databases, and local artifacts.
- Python test coverage is still incomplete; broker-backed integration tests are not yet implemented.

## Current phase

The current phase is MQTT reliability. Add an isolated local broker test environment and cover concurrency, timeouts, cleanup, duplicate and late responses, malformed payloads, offline nodes, reconnects, and worker restarts. Never use the Oracle production broker for tests.

## Browser direction

Start with standard Chromium, Playwright/CDP, isolated profiles, protected CDP, domain allowlists, controlled downloads/uploads, and auditable actions. Do not fork Chromium initially. CAPTCHA and MFA require pause or authorized handoff; anti-abuse controls must not be bypassed.

## Security and repository rules

Use default deny and least privilege. Restrict files to explicit workspaces. Do not expose unrestricted shell execution. Keep secrets out of Git. Do not commit generated binaries, virtual environments, logs, databases, or local state. Review `SECURITY.md` before adding capabilities.

## Validation

```powershell
Set-Location A:\omninode\node1-gateway
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\python.exe -m compileall .

Set-Location A:\omninode\omniclient
gofmt -l .
go test ./...
go test -race ./...
go vet ./...

Set-Location A:\omninode
git diff --check
git status --short
git diff --stat
```

`pytest` must no longer report only `no tests ran`; if a test dependency or environment is missing, report it explicitly. No commit or push should occur without review of the complete diff.
