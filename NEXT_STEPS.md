# Next Steps - OmniNode

## Stato attuale (Phase 2.5)

Phase 2.5 - Self-Hosting Autonomy Bootstrap e code-complete e test-green sul branch feature/phase-2.5-autonomy (non mergiato).

- pytest: 59 passed, 1 skipped, 0 failed.
- go vet: clean. go test: ok.
- git diff --check: clean.

## Priorita Alta (immediato)

### 1. Correggere requirements.txt

**Stato**: da fare
**Sforzo**: 5 minuti

- [ ] Sostituire aiomqtt==2.4.2 (inesistente) con aiomqtt==2.4.0.

### 2. Rimuovere .env dal repo

**Stato**: da fare
**Sforzo**: 30 minuti + rotazione credenziali

- [ ] git rm --cached node1-gateway/.env
- [ ] Ruotare ogni credenziale contenuta nel file.
- [ ] Rimuovere il file dalla storia git (git filter-repo).

### 3. Rimuovere il default di MCP_SECRET

**Stato**: da fare
**Sforzo**: 10 minuti

- [ ] In main.py: MCP_SECRET = os.environ["MCP_SECRET"] (fail fast se manca).

### 4. Autenticare /api/v1/approve

**Stato**: da fare
**Sforzo**: 30 minuti

- [ ] Aggiungere Depends(verify_mcp_auth) all'endpoint.

### 5. Correggere workspace_manager.py

**Stato**: da fare
**Sforzo**: 1 ora

- [ ] Spostare il controllo is_symlink() prima di resolve().
- [ ] Usare scrittura atomica (.tmp + os.replace) come in local_executor.py.

### 6. Rimuovere o allineare i vecchi executor

**Stato**: da fare
**Sforzo**: 1 ora

- [ ] command_executor.py e test_executor.py permettono python/go con argomenti liberi (arbitrary code execution).
- [ ] Eliminarli o sostituirli con VerificationExecutor (preset statici).

## Priorita Media (Phase 3)

### 7. Schema RPC versionato

- [ ] Definire schema_version 1, task_id, goal_id, agent_id, node_id, task_type, capability, created_at, deadline_at, payload.
- [ ] Codici errore espliciti e versionati.

### 8. Audit Transparency Log

- [ ] Ed25519-signed entries.
- [ ] Merkle tree chaining.
- [ ] Endpoint di verifica pubblicazione.

### 9. Tool MCP Go

- [ ] omninode_workspace_list / read / write / rollback.
- [ ] omninode_command_verify.
- [ ] omninode_autonomy_step.
- [ ] Dispatch MQTT locale per workspace.* e command.run.

### 10. Migrazione topic MQTT

- [ ] Da omninode/nodes/... a omninode/v1/nodes/{node_id}/tasks|responses|heartbeat.
- [ ] MQTT over WSS (porta 443).

## Backlog Swarm Fabric v4.0

- [ ] lifecycle_windows.go: usare golang.org/x/sys/windows Job Objects con handle reale (windows.OpenProcess), mai PID come handle.
- [ ] spatial_pruner.js isElementCovered(): campionare centro e punti interni (2px), verificare width/height > 0 e visibility, non gli angoli esterni esatti.
- [ ] TLS end-to-end, multi-sessione browser, monitoring Prometheus, rate limiting.

## Milestone

| Milestone | Stato | Contenuto |
|-----------|-------|-----------|
| Phase 2.5 | completata sul branch | autonomia self-hosting, workspace confinato, verification preset, loop atomico |
| Phase 3 | da fare | schema RPC, audit log, tool MCP Go |
| Swarm v4.0 | da fare | topic per nodo, Job Objects, spatial pruner, TLS |
