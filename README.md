# Omninode

Omninode e' un control plane per agenti AI distribuiti: i connector MCP remoti chiamano il Gateway su Oracle Cloud, il Gateway instrada i task tramite MQTT mTLS ai worker locali e i worker eseguono browser automation CDP oppure tool operativi controllati.

> Stato del branch `feature/browse-rpc-mqtt`: gli Step 1-6 sono stati implementati a livello di codice. La compilazione e i test end-to-end su Oracle/Mosquitto/Chrome reale restano obbligatori prima dell'uso in produzione.

## Architettura

```text
LLM / MCP Connector
        |
        | HTTPS /mcp
        v
Oracle A: FastAPI Gateway + Cloudflare Tunnel
        |
        | MQTT mTLS :8883
        v
Oracle B: Mosquitto
        |
        +-------------------------------+
        |                               |
        v                               v
Windows Ryzen worker                 Surface worker
Go + Chrome reale CDP                Go + Chrome reale CDP
```

- **Oracle A:** dashboard Bento Box, endpoint MCP, SSE e routing dinamico basato su heartbeat.
- **Oracle B:** broker MQTT con autenticazione reciproca TLS e ACL per nodo.
- **Worker locali:** connessioni esclusivamente in uscita, browser Chrome reale via CDP locale e WebSocket locale opzionale.

## Componenti

| Percorso | Responsabilita' |
|---|---|
| `node1-gateway/` | Gateway FastAPI, dashboard, SSE, bridge MQTT e instradamento MCP |
| `omniclient/` | Worker Go, browser CDP, snapshot AX tree, click tramite input CDP, MQTT e heartbeat |
| `docs/` | Documentazione aggiuntiva del progetto |

## Flussi principali

### Browser automation

1. Il connector chiama `/mcp` sul Gateway.
2. Il Gateway seleziona un worker da `agent_id -> node_id` e pubblica un task MQTT.
3. Il worker recupera una `WebSession`, estrae l'Accessibility Tree con CDP e restituisce un testo compatto; i ref sono validi solo fino al prossimo snapshot.
4. I click usano `Input.dispatchMouseEvent`, non `element.click()`.

### Human-in-the-loop

Le operazioni distruttive devono pubblicare `pending_approval`, generare un alert MQTT e attendere una decisione umana della dashboard. Nessun tool deve eseguire shell arbitraria.

## Avvio locale del worker

1. Avvia Chrome con debugging locale, ad esempio:
   ```powershell
   chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\omninode-chrome
   ```
2. Configura le variabili richieste:
   ```powershell
   $env:OMNI_WS_TOKEN = "token-lungo-almeno-32-caratteri"
   $env:OMNI_WS_ORIGINS = "http://127.0.0.1:8080"
   $env:OMNI_NODE_ID = "ryzen"
   $env:OMNI_MQTT_BROKER = "tls://oracle-b.plini.net:8883"
   $env:OMNI_MQTT_CA = "certs/ca.crt"
   $env:OMNI_MQTT_CERT = "certs/client.crt"
   $env:OMNI_MQTT_KEY = "certs/client.key"
   ```
3. Compila e avvia:
   ```powershell
   cd omniclient
   go mod tidy
   go build ./...
   go run .
   ```

## Avvio Gateway

Sul nodo Oracle A configura `MQTT_BROKER`, `MQTT_CA`, `MQTT_CERT`, `MQTT_KEY`, `MCP_SECRET`, `OMNI_BIND=127.0.0.1` e `OMNI_PORT=8000`, quindi:

```bash
cd node1-gateway
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Il gateway deve essere esposto tramite Cloudflare Tunnel, non direttamente su Internet. Vedi `ARCHITECTURE.md` e `SECURITY.md`.

## Stato e prossimi passi

Consulta `NEXT_STEPS.md` per checklist di build, test MQTT, configurazione Mosquitto, Cloudflare Access e Step 5 (Ops CLI con approvazione umana).