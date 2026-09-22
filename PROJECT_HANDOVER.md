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

## Stato architetturale verificato

Omninode adotta un'architettura ibrida composta da un gateway Python/FastAPI e da un client/daemon locale in Go (`omniclient`), con comunicazione MQTT Request-Reply tra gateway e worker. Il gateway usa task pendenti correlati, eventi di sincronizzazione, strutture protette da lock e cleanup nei percorsi di completamento e timeout.

Il sistema è progettato per ospitare AI autonome residenti h24 sui nodi Oracle, capaci di operare sulle risorse locali secondo capability, policy e limiti definiti dal runtime. L'accesso a filesystem, processi, rete e browser non deve essere illimitato: deve essere controllato da default-deny, least privilege, workspace isolati, isolamento dei segreti, audit e approvazioni per azioni ad alto rischio.

Per il browser, la direzione iniziale è Chromium standard con Playwright/CDP, profili isolati e protezione dell'interfaccia CDP. Un fork personalizzato di Chromium non è previsto in questa fase.

I test Go verificano il contratto HTTP del client tramite `httptest.NewServer`, senza dipendenze di rete esterne. I test Python verificano attualmente autenticazione, assenza di nodi online e alcuni controlli iniziali del gateway. La compilazione Python, l'import dell'applicazione, `go test ./...` e `go vet ./...` risultano verificati localmente.

La copertura MQTT end-to-end, inclusi broker locale di test, concorrenza, risposte tardive, duplicati, riconnessioni e riavvio dei worker, deve ancora essere completata. Anche il race detector Go non è stato eseguito nell'ambiente Windows corrente perché CGO/GCC non sono disponibili.

La baseline è quindi affidabile per il percorso HTTP e per i primi controlli del gateway, ma non deve ancora essere descritta come completamente validata per l'autonomia operativa h24 in produzione.
