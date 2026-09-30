# Repository Map - OmniNode

## Struttura Repository

```
omninode/
├── README.md                    # Panoramica progetto
├── ARCHITECTURE.md              # Architettura dettagliata
├── SECURITY.md                  # Principi sicurezza
├── BUILD.md                     # Istruzioni build
├── NEXT_STEPS.md                # Priorità sviluppo
├── ROADMAP.md                   # Stato implementazione
├── INDEX.md                     # Indice documentazione
├── PROJECT_HANDOVER.md          # Handover progetto
│
├── docs/
│   ├── AI_ONBOARDING.md         # Onboarding AI assistant
│   ├── OPERATIONS_RUNBOOK.md    # Runbook operativo
│   └── REPOSITORY_MAP.md        # Questa mappa
│
├── node1-gateway/
│   ├── main.py                  # FastAPI app
│   ├── mqtt_service.py          # Servizio MQTT
│   ├── task_store.py            # Store task
│   ├── policy_engine.py         # Motore policy
│   ├── browser_runtime.py       # Runtime browser
│   ├── audit.py                 # Audit logging
│   ├── workspace_manager.py     # Gestione workspace
│   ├── command_executor.py      # Esecutore comandi
│   ├── local_executor.py        # Esecutore locale
│   ├── work_loop.py             # Loop lavoro
│   ├── .env.example             # Template env
│   ├── requirements.txt         # Dipendenze Python
│   └── test_*.py                # Test
│
├── omniclient/
│   ├── main.go                  # Entry point
│   ├── mcp_server.go            # Server MCP
│   ├── cdp_agent.go             # CDP agent
│   ├── web_agent.go             # Web agent
│   ├── ops_terraform.go         # Terraform ops
│   ├── gateway_client.go        # Client gateway
│   ├── mqtt_client.go           # Client MQTT
│   ├── ws_server.go             # Server WebSocket
│   ├── heartbeat.go             # Health check
│   ├── go.mod                   # Dipendenze Go
│   ├── go.sum                   # Checksum Go
│   ├── wails.json               # Config Wails
│   ├── test_mcp_client.py       # Test MCP
│   ├── mcp_server_test.go       # Test MCP server
│   ├── README.md                # Setup omniclient
│   ├── HANDOFF.md               # Handoff componenti
│   ├── MCP_SETUP.md             # Config MCP
│   └── frontend/                # UI Wails (opzionale)
│
└── .github/
    └── workflows/
        └── ci.yml               # CI pipeline
```

## Dipendenze

### node1-gateway (Python)

```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
paho-mqtt>=1.6.0
websockets>=11.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

**Dipendenze di Sistema**: Python 3.11+, Chrome 114+, Mosquitto

### omniclient (Go)

```go
require (
    github.com/mark3labs/mcp-go v0.1.0
    github.com/gorilla/websocket v1.5.0
    github.com/eclipse/paho.mqtt.golang v1.4.0
    github.com/chromedp/cdproto v0.0.0-20230802225258-3d75c27a330d
    github.com/chromedp/chromedp v0.9.0
    go.uber.org/zap v1.25.0
    gopkg.in/yaml.v3 v3.0.1
)
```

**Dipendenze di Sistema**: Go 1.21+, Chrome 114+

## Invarianti

### Codice

1. Nessun secret hardcoded: Usare sempre env var o vault
2. Type hints obbligatori (Python): `def func(arg: str) -> None:`
3. Error wrapping (Go): `fmt.Errorf("context: %w", err)`
4. Test coverage minimo: 70% per nuovi file

### Architettura

1. CDP solo localhost: Chrome deve essere su localhost:9222
2. MQTT QoS 1: Almeno una consegna garantita
3. Task ID univoci: UUID v4, mai riutilizzare
4. Audit append-only: Mai modificare/eliminare log

### Sicurezza

1. HTTPS in produzione: Mai HTTP per gateway
2. MQTT over TLS: mqtts:// con certificati client
3. Firewall localhost: CDP e MCP solo su 127.0.0.1
4. Policy enforcement: Ogni richiesta browser passa dal policy engine

## Flussi Dati

### Browser Navigation

```
MCP Client → mcp_server.go → gateway_client.go → HTTP POST /browser/navigate
    ↓
node1-gateway/main.py → mqtt_service.py → omni/browser/request
    ↓
browser_runtime.py → Chrome CDP
    ↓
mqtt_service.py → omni/browser/result
    ↓
gateway_client.go → mcp_server.go → MCP Client
```

### Terraform Plan

```
MCP Client → mcp_server.go → ops_terraform.go → exec.Command("terraform", "plan")
    ↓
ops_terraform.go → parsing stdout/stderr
    ↓
mcp_server.go → MCP Client (output)
```

### Heartbeat

```
omniclient/heartbeat.go → HTTP GET /health (gateway)
    ↓
node1-gateway/main.py → 200 OK
    ↓
heartbeat.go → log + retry (se fallisce)
```

## Punti di Estensibilità

### Nuovi Tool MCP

1. Aggiungere handler in `mcp_server.go`
2. Registrare tool in `NewMCPServer()`
3. Aggiornare documentazione in `MCP_SETUP.md`

### Nuovi Endpoint Gateway

1. Aggiungere route in `main.py`
2. Aggiungere test in `test_main.py`
3. Aggiornare `ARCHITECTURE.md` con contratto API

### Nuovi Topic MQTT

1. Definire topic in `mqtt_task_protocol.py`
2. Implementare publisher/subscriber in `mqtt_service.py` e `mqtt_client.go`
3. Aggiornare `ARCHITECTURE.md` con tabella topic

## Script Utili

```bash
# scripts/build.sh
cd omniclient && go build -o omniclient .
cd node1-gateway && pip install -r requirements.txt

# scripts/test.sh
cd omniclient && go test -v ./...
cd node1-gateway && pytest -v

# scripts/deploy.sh
scp omniclient/omniclient user@gateway:/opt/omni/
scp -r node1-gateway/* user@gateway:/opt/gateway/
ssh user@gateway "systemctl restart omninode-gateway"

# scripts/backup.sh
sqlite3 /var/lib/omni/tasks.db ".backup /backup/tasks-$(date +%Y%m%d).db"
tar -czf /backup/audit-$(date +%Y%m%d).tar.gz /var/log/omni/audit.jsonl
```

## Risorse Esterne

- [MCP Specification](https://modelcontextprotocol.io/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Go Documentation](https://go.dev/doc/)
- [Paho MQTT Go](https://github.com/eclipse/paho.mqtt.golang)
- [Chromedp](https://github.com/chromedp/chromedp)
