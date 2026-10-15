# GEMINI HANDOVER - Omninode Phase 2.5

## RUOLO E OBIETTIVO

Agisci come Principal Distributed Systems Engineer e Core Maintainer del repository
`https://github.com/ZooL-OhKi/omninode`, branch attivo `feature/phase-2.5-autonomy`.

Hai accesso diretto al repository GitHub e puoi leggere, creare e modificare i file.
Hai anche accesso al disco `A:` tramite Google Drive (il repo locale e in `A:\omninode`).

Il tuo obiettivo immediato e completare la **Phase 2.5 - Self-Hosting Autonomy Bootstrap**,
che e code-complete e test-green sul branch, poi procedere con la Phase 3 e il backlog
Swarm Fabric v4.0.

## STATO ATTUALE (aggiornato)

### Test verdi

- pytest: **59 passed, 1 skipped, 0 failed** (node1-gateway, Windows).
- go vet: **clean**. go test: **ok** (github.com/ZooL-OhKi/omniclient).
- git diff --check: **clean**.

### File creati o modificati (con commit)

| File | Commit | Cosa contiene |
|------|--------|---------------|
| node1-gateway/autonomy_core.py | e3791cf | RepoWorkspace (list/read/write/rollback, PROTECTED_PATHS, symlink+traversal denial, filtro segreti, redazione, snapshot) e VerificationExecutor (preset statici, shell=False, output 16000 char, verify_all fail-fast) |
| node1-gateway/work_loop.py | 26181de | SelfHostingWorkLoop (READ_CONTEXT -> GENERATE -> WRITE -> VERIFY -> SELF_HEAL max 3 -> COMMIT/ROLLBACK) e PerplexityHelper (urllib, PERPLEXITY_API_KEY/PERPLEXITY_MODEL) |
| node1-gateway/autonomy_api.py | a4edd90 | POST /api/v1/autonomy/run-step, POST /api/v1/autonomy/goals, GET /api/v1/autonomy/goals/{id}; capability 15 min, stato su tasks.db |
| node1-gateway/autonomy_app.py | a4edd90 | Wrapper: uvicorn autonomy_app:app, main.py non toccato |
| node1-gateway/test_autonomy.py | a4edd90 | ~40 test su workspace, preset, loop, helper |
| node1-gateway/test_autonomy_api.py | a4edd90 | 5 test sugli endpoint (FastAPI richiesto) |
| node1-gateway/test_main.py | 882c487, 5a426f8 | Riscritto per endpoint reali (/api/v1/nodes, /mcp), MQTT mockato |
| omniclient/cdp_agent.go | 56c3ce2 | Import playwright rinominato in github.com/mxschmitt/playwright-go |
| omniclient/web_agent.go | b8025f6 | Stesso import rinominato |
| omniclient/mqtt_client.go | e3b658a | Rimossi publishHeartbeat e startHeartbeatLoop duplicati (restano in heartbeat.go) |
| omniclient/ops_terraform.go | e3b658a | Rimosso publishRes duplicato (resta in mqtt_client.go) |
| omniclient/main.go | e3b658a | StartWSServer(8080) chiamato senza assegnazione |
| omniclient/go.mod, go.sum | aaf5970 | Aggiunte mxschmitt/playwright-go v0.6201.1, modernc.org/sqlite v1.60.1 e transitive |
| docs/PHASE_2_5_AUTONOMY.md | 957c88b, 18eae72 | Stato reale, test verdi, coda task |
| PROJECT_HANDOVER.md | 18eae72 | Baseline Phase 2.5, 7 problemi noti, validazione |
| NEXT_STEPS.md | 18eae72 | 6 task alta priorita, Phase 3, backlog Swarm v4.0 |

## TASK AD ALTA PRIORITA (da fare subito)

### 1. Correggere requirements.txt

`node1-gateway/requirements.txt` contiene `aiomqtt==2.4.2`, versione inesistente su PyPI.
Sostituire con `aiomqtt==2.4.0` (quella installata e testata in locale).

### 2. Rimuovere .env dal repo

`node1-gateway/.env` e tracciato in git. Ruotare ogni credenziale contenuta, poi:

```powershell
git rm --cached node1-gateway/.env
git commit -m "chore: stop tracking .env"
```

Per cancellarlo dalla storia serve `git filter-repo`.

### 3. Rimuovere il default di MCP_SECRET

In `node1-gateway/main.py`, riga 13:

```python
MCP_SECRET = os.getenv("MCP_SECRET", "super-secret-mcp-token")
```

Sostituire con:

```python
MCP_SECRET = os.environ["MCP_SECRET"]
```

(fail fast se la variabile manca).

### 4. Autenticare /api/v1/approve

In `node1-gateway/main.py`, aggiungere `dependencies=[Depends(verify_mcp_auth)]` al decorator
`@app.post("/api/v1/approve")`.

### 5. Correggere workspace_manager.py

- Spostare il controllo `is_symlink()` PRIMA di `resolve()` (oggi non puo mai scattare).
- Usare scrittura atomica (`.tmp` + `os.replace`) come in `local_executor.py`.

### 6. Rimuovere o allineare i vecchi executor

`command_executor.py` (classe TestExecutor) e `test_executor.py` (classe CommandExecutor)
permettono `python` e `go` con argomenti liberi = arbitrary code execution.
Eliminarli o sostituirli con `VerificationExecutor` (preset statici).

## REGOLE DI SICUREZZA NON NEGOZIABILI

1. **Mai toccare** questi file (protetti, L4):
   - `SECURITY.md`
   - `node1-gateway/policy_engine.py`
   - `node1-gateway/workspace_manager.py`

   (eccezione: il task 5 sopra richiede di correggere workspace_manager.py; farlo solo con
   approvazione esplicita dell'utente e con commit separato).

2. **Zero Arbitrary Shell**: `command.run` accetta SOLO preset statici da `VERIFICATION_PRESETS`
   (python_compile, python_tests, go_vet, go_tests, git_diff_check, verify_all), sempre `shell=False`.

3. **Source Hygiene**: escludere da lettura/scansione `.git/`, `venv/`, `.venv/`, `__pycache__/`,
   `.pytest_cache/`, `.env*`, `*.pem`, `*.key`, `*.p12`, `*.db`, `*.sqlite*`, `*.exe`.
   Rifiutare path assoluti, `..` traversal, symlink escape.

4. **Idempotenza e Rollback**: ogni scrittura su file esistente salva un backup prima della
   modifica atomica e lo ripristina se verify_all fallisce dopo max 3 tentativi.

5. **Nessun commit/push senza revisione del diff completo** (`git diff --stat`, `git diff`).

## ISTRUZIONI OPERATIVE (A: via Google Drive)

Il repo locale e in `A:\omninode`. Tutti i comandi sono PowerShell.

### Setup iniziale

```powershell
Set-Location A:\omninode
git status --short
git fetch origin
git checkout feature/phase-2.5-autonomy
git pull

Set-Location A:\omninode\node1-gateway
python -m venv venv
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest httpx
```

### Verifica baseline (da fare prima di ogni modifica)

```powershell
Set-Location A:\omninode\node1-gateway
python -m compileall -q .
pytest -q

Set-Location A:\omninode\omniclient
go vet ./...
go test ./...

Set-Location A:\omninode
git diff --check
git status --short
```

### Avviare il gateway con gli endpoint autonomy

```powershell
Set-Location A:\omninode\node1-gateway
$env:MCP_SECRET = "scegli-un-segreto-lungo"
$env:MQTT_BROKER = "localhost"
uvicorn autonomy_app:app --host 127.0.0.1 --port 8000
```

### Testare un autonomy step (external driver mode)

```powershell
$h = @{ Authorization = "Bearer scegli-un-segreto-lungo" }
$body = @{ target_file = "docs/_prova.md"; content = "prova`n" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/autonomy/run-step -Headers $h -ContentType "application/json" -Body $body
```

La chiamata esegue verify_all sul repo reale (puo richiedere minuti). Se status e "committed",
il file esiste. Se e "rolled_back", il file e stato rimosso e nella risposta c'e il report dei test.

### Testare il blocco dei file protetti

```powershell
$body = @{ target_file = "SECURITY.md"; content = "x" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/autonomy/run-step -Headers $h -ContentType "application/json" -Body $body
```

Deve rispondere status = "rejected".

### Modalita API Autonoma (PerplexityHelper)

```powershell
$env:PERPLEXITY_API_KEY = "pplx-..."
$env:PERPLEXITY_MODEL = "sonar-reasoning-pro"
```

Poi usare `POST /api/v1/autonomy/goals` con `prompt` invece di `content`.

## CODA DEI TASK AUTONOMI (dopo i 6 task alta priorita)

1. CI: eseguire la suite Phase 2.5 e bloccare il merge se rossa.
2. Phase 3: schema RPC versionato (schema_version 1, task_id, goal_id, agent_id, node_id,
   task_type, capability, created_at, deadline_at, payload) + codici errore.
3. Audit Transparency Log: Ed25519-signed entries, Merkle tree.
4. Tool MCP Go: omninode_workspace_list/read/write/rollback, omninode_command_verify,
   omninode_autonomy_step + dispatch MQTT locale.
5. Migrazione topic: omninode/nodes/... -> omninode/v1/nodes/{node_id}/tasks|responses|heartbeat,
   MQTT over WSS (443).
6. Swarm Fabric v4.0 backlog, con 3 correzioni obbligatorie:
   - lifecycle_windows.go: golang.org/x/sys/windows Job Objects con handle reale (windows.OpenProcess), mai PID;
   - spatial_pruner.js isElementCovered(): centro + punti interni 2px, width/height > 0, visibility;
   - topic per nodo, non flat omni/swarm/*.

## VALIDAZIONE FINALE (prima del merge)

```powershell
Set-Location A:\omninode\node1-gateway
pytest -q
python -m compileall -q .

Set-Location A:\omninode\omniclient
go vet ./...
go test ./...

Set-Location A:\omninode
git diff --check
git status --short
```

Merge solo se tutto verde:

```powershell
git checkout feature/browse-rpc-mqtt
git merge --no-ff feature/phase-2.5-autonomy
git push
```
