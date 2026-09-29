# OmniClient

OmniClient è il worker headless del fabric Omninode, scritto in Go. Fornisce:
- Esecuzione di task computazionali su nodi remoti
- Integrazione MCP (Model Context Protocol) per agenti IA
- Heartbeat MQTT periodico verso il Gateway FastAPI
- Dashboard web "Bento Box" servita dal Gateway sulla porta 8000

## Prerequisites

- Go 1.21+
- Broker MQTT (es. Mosquitto) sulla porta 1883
- Gateway FastAPI in esecuzione su `http://127.0.0.1:8000`

## Build

```bash
cd omniclient
go build -o omniclient.exe .
```

Il binario risultante è un'applicazione CLI headless, senza dipendenze grafiche.

## Utilizzo

### Modalità MCP Stdio (per agenti IA)

```bash
./omniclient --mcp-stdio
```

Il server MCP comunica via stdin/stdout con agenti come Gemini Desktop, Claude Desktop, o Cursor IDE.

### Modalità Worker con Heartbeat MQTT

Il worker si connette al broker MQTT e invia heartbeat periodici al topic:
```
omninode/nodes/{node-id}/heartbeat
```

Il Gateway FastAPI ascolta questi heartbeat e aggiorna la dashboard Bento Box in tempo reale.

## Architettura

```
┌──────────────┐      MQTT       ┌─────────────────┐
│  OmniClient  │ ───────────────>│  Gateway FastAPI│
│  (headless)  │   heartbeat     │  (porta 8000)   │
└──────────────┘                 └────────┬────────┘
                                          │
                                          │ HTTP
                                          ▼
                                   ┌──────────────┐
                                   │ Dashboard    │
                                   │ Bento Box    │
                                   │ (web UI)     │
                                   └──────────────┘
```

### Componenti

| Componente | Descrizione |
|------------|-------------|
| `main.go` | Entry point CLI, gestisce `--mcp-stdio` e worker mode |
| `mcp_server.go` | Server MCP con tools: `restart_node`, `run_sandbox_code`, `browse_webpage`, `workspace.write` |
| `gateway_client.go` | Client HTTP verso il Gateway FastAPI |
| Gateway FastAPI | Serve la dashboard Bento Box e gestisce i task MQTT |

## Dashboard Bento Box

La dashboard è accessibile su `http://localhost:8000` e mostra:
- Stato dei nodi connessi (online/offline)
- Chat per inviare comandi in linguaggio naturale
- Lista dei nodi attivi con load %

### Endpoint API

| Endpoint | Descrizione |
|----------|-------------|
| `GET /` | Dashboard web (Bento Box) |
| `GET /health` | Health check del Gateway |
| `GET /api/v1/nodes` | Lista nodi attivi (richiede header `x-omninode-key`) |

## Testing

### Test del server MCP

```bash
# Stdio mode
./omniclient --mcp-stdio

# Test con client Python
python test_mcp_client.py --stdio
```

### Test della dashboard

1. Avvia il Gateway:
```bash
cd node1-gateway
python main.py
```

2. Apri `http://localhost:8000` nel browser.

3. Verifica che i nodi appaiano nella sezione "Active Nodes".

## Project Structure

```
omniclient/
├── main.go              # Entry point CLI headless
├── mcp_server.go        # Server MCP
├── gateway_client.go    # Client HTTP verso Gateway
├── go.mod               # Dipendenze Go
└── README.md            # Questa documentazione
```

## License

MIT
