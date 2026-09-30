# Handover progetto Omninode

## Branch di lavoro

`feature/browse-rpc-mqtt`

## Obiettivo corrente

Completare la validazione end-to-end del fabric MCP -> Gateway -> MQTT mTLS -> Worker locale -> Chrome CDP, quindi implementare Ops CLI con approvazione umana persistente.

## Commit architetturali recenti

- `44e244c`: base CDP connect e snapshot WS iniziale.
- `bf50285`: WS hardening, CDP AX snapshot/click e gateway MCP iniziale.
- `c97fda1`: integrazione entrypoint Gateway e worker.
- `7266b14`: dashboard SSE, mTLS nel gateway, heartbeat e routing dinamico.

## Codice rilevante

### Worker Go

- `web_agent.go`: connessione al Chrome reale su CDP 9222.
- `cdp_agent.go`: AX tree, ref, click CDP e registro sessioni.
- `ws_server.go`: WS locale senza shell libera.
- `heartbeat.go`: heartbeat periodico dei nodi.
- `main.go`: bootstrap browser, WS e MQTT.
- `mqtt_client.go`: deve essere presente e allineato al contratto in `ARCHITECTURE.md`.

### Gateway Python

- `main.py`: dashboard, SSE, listener MQTT mTLS, approval endpoint e MCP bridge.
- `mcp_gateway.py`: implementazione MCP precedente; evitare due app/bridge in concorrenza. Consolidare in un solo gateway prima di produzione.
- `static/index.html`: dashboard mobile per alert e nodi.

## Rischi da risolvere

1. **Non testato:** eseguire build Go/Python e test in ambiente reale.
2. **MCP duplicato:** il branch contiene sia `mcp_gateway.py` sia codice MCP in `main.py`; scegliere un'implementazione unica e testarla contro il connector reale.
3. **Auth dashboard:** SSE e `/api/v1/approve` devono essere protetti da Cloudflare Access e CSRF prima della produzione.
4. **Persistenza:** task e approvazioni attualmente non sono persistenti.
5. **Node expiry:** un heartbeat vecchio non viene ancora marcato offline automaticamente.
6. **Concurrency:** con Chrome context condiviso bisogna evitare due agenti che agiscono sulla stessa tab.
7. **Segreti:** non committare token, CA private o chiavi client.

## Primo ciclo di lavoro consigliato

1. `git checkout feature/browse-rpc-mqtt && git pull`.
2. Verificare `go.mod`, eseguire `go mod tidy && go build ./...`.
3. Creare/validare `mqtt_client.go`, compilare e verificare connessione mTLS.
4. Eseguire `pip install -r node1-gateway/requirements.txt`, avviare FastAPI e testare `/health`/dashboard.
5. Configurare Mosquitto mTLS e osservare heartbeat.
6. Configurare Cloudflare Tunnel/Access in staging.
7. Solo dopo, aggiungere runner Terraform/OCI Human-in-the-loop.
