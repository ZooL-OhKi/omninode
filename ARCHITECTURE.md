# Architettura Omninode

## Topologia

```text
MCP connector / LLM
  | HTTPS JSON-RPC
  v
Cloudflare Access + Tunnel (plini.net)
  |
  v
Oracle A: FastAPI Gateway
  |-- /                 Dashboard Bento Box (SSE)
  |-- /api/v1/stream    Event stream dashboard
  |-- /api/v1/approve   Decisione human-in-the-loop
  `-- /mcp              Ingresso MCP
  |
  | MQTT mTLS (TCP 8883)
  v
Oracle B: Mosquitto
  |
  +-- omninode/nodes/{node}/cmd/{task}
  +-- omninode/nodes/{node}/result/{task}
  +-- omninode/nodes/{node}/heartbeat
  +-- omninode/alerts/approval
  `-- omninode/approvals/in
  |
  v
Worker Go locali (Ryzen / Surface)
  |-- Chrome reale via CDP su 127.0.0.1:9222
  |-- Playwright-Go + CDP raw
  `-- WebSocket locale opzionale su 127.0.0.1:8080
```

## Gateway

`node1-gateway/main.py` mantiene in memoria:

- `active_nodes`: stato ricavato dagli heartbeat.
- `agent_routing`: mappa agente -> nodo, ricavata da `supported_agents` nell'heartbeat.
- `pending_mcp_requests`: Future in attesa di un risultato MQTT.
- `sse_clients`: code asincrone per dashboard connesse.

Il Gateway inoltra alert di approvazione e aggiornamenti nodi ai browser tramite Server-Sent Events.

## Worker

Il worker usa Chrome reale avviato localmente con remote debugging CDP. La sessione browser di default e' deliberatamente collegata al profilo Chrome reale quando occorrono sessioni utente esistenti. L'isolamento per agente non e' attivo di default: gli agenti devono quindi usare tab/sessioni separate e il worker deve serializzare le operazioni concorrenti sulla stessa sessione.

### Browser control

- `Accessibility.getFullAXTree` produce la base del snapshot.
- Gli elementi interattivi ricevono ref numerici temporanei, associati a `backendDOMNodeId`.
- `DOM.scrollIntoViewIfNeeded`, `DOM.getContentQuads` e `Input.dispatchMouseEvent` sono usati per il click.
- I ref vanno considerati invalidi dopo un nuovo snapshot o un re-render SPA.

## Contratti MQTT

### Command

Topic: `omninode/nodes/{node_id}/cmd/{task_id}`

```json
{"task_id":"...","agent_id":"agent_1","action":"web_snapshot","ref":null}
```

### Result

Topic: `omninode/nodes/{node_id}/result/{task_id}`

```json
{"task_id":"...","status":"success","output":"..."}
```

### Heartbeat

Topic: `omninode/nodes/{node_id}/heartbeat`

```json
{"node_id":"ryzen","status":"online","supported_agents":["agent_1","devops_bot"],"timestamp":"2026-09-30T10:00:00Z"}
```

### Approval

- Alert: `omninode/alerts/approval`
- Decisione: `omninode/approvals/in`

I payload devono contenere almeno `task_id`, `agent_id`, descrizione dell'operazione e decisione/risultato.

## MCP

Il Gateway espone `/mcp` via HTTPS. Il trasporto previsto e' JSON-RPC/Streamable HTTP; il codice corrente contiene una base MCP e deve essere validato con il connector specifico prima dell'uso. L'autenticazione applicativa usa un Bearer token (`MCP_SECRET`) dietro Cloudflare Access.

## Limitazioni note

- Il codice CDP/Playwright-Go deve essere compilato contro la versione effettiva del modulo prima del deploy.
- Il worker MQTT definitivo (`mqtt_client.go`) e l'handler delle approvazioni ops devono essere verificati/integrati prima del deployment di produzione.
- Gli state store del gateway sono in memoria: un riavvio perde routing, richieste pendenti e SSE; gli heartbeat ripopolano il routing. Per task di approvazione serve persistenza (SQLite/Postgres) nello Step 5.
- Il Gateway non deve usare fallback silenziosi su un nodo: se non esiste routing vivo per l'agente, deve restituire un errore esplicito.
