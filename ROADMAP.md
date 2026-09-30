# Roadmap Omninode

## Completato sul branch `feature/browse-rpc-mqtt`

- [x] Rimozione del canale Tampermonkey/DOM State-Overwrite dall'architettura prevista.
- [x] WebSocket locale ristretto a loopback, Origin allowlist e token; rimozione `exec`.
- [x] Connessione Chrome reale via CDP.
- [x] Snapshot AX tree CDP e click tramite input CDP.
- [x] Struttura sessioni browser e ref temporanei.
- [x] Base Gateway MCP/MQTT in FastAPI.
- [x] Dashboard SSE Bento Box e heartbeat/routing dinamico a livello di codice.

## In validazione

- [ ] Build reale di `playwright-go` e funzioni CDP sul target Windows/ARM.
- [ ] Worker MQTT mTLS completo, resilienza reconnect e deduplicazione task.
- [ ] Compatibilita' del trasporto MCP con connector scelto.
- [ ] Cloudflare Tunnel + Access con dashboard umana e `/mcp` M2M.
- [ ] Test end-to-end Chrome reale, Mosquitto e dashboard mobile.

## Pianificato

### Step 5 - Ops CLI e Human-in-the-loop

- [ ] Tool `ops.terraform` e `ops.oci` tipizzati.
- [ ] Allowlist di argomenti e runner senza shell.
- [ ] Stato persistente delle approvazioni, TTL e audit.
- [ ] Alert MQTT/SSE e decisione dashboard.

### Stabilita' e sicurezza

- [ ] Persistenza Postgres/SQLite per task, audit, routing e approvazioni.
- [ ] Expiry dei nodi e health checking.
- [ ] Rate limiting, CSRF e limiti SSE.
- [ ] Policy Mosquitto ACL e rotazione certificati.
- [ ] CI che esegue build Go, lint Python e test di contratto MQTT.

### Browser capabilities

- [ ] `web.goto`, `web.type`, `web.key`, `web.scroll`, screenshot controllati.
- [ ] Gestione iframe/shadow DOM e navigazioni SPA.
- [ ] Limiti per tab, sessioni e concorrenza multi-agente.
