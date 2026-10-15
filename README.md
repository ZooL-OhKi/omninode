# OmniNode

Sistema distribuito per l'automazione browser e operazioni infrastrutturali tramite MCP (Model Context Protocol).

## Panoramica

OmniNode è un'architettura client-gateway che espone capacità di automazione browser (CDP) e operazioni infrastrutturali (Terraform) attraverso un server MCP locale. Il sistema è composto da due componenti principali:

- **omniclient (Go)**: Server MCP locale che esegue su macchina client, espone tool `browser_*` e `ops_*`, gestisce Chrome DevTools Protocol (CDP) locale e comunica con il gateway
- **node1-gateway (Python/FastAPI)**: Gateway centrale che gestisce MQTT, task store, policy engine, audit logging e browser runtime remoto

## Architettura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (omniclient)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  MCP Server │  │  CDP Agent  │  │ Web Agent   │  │ Ops Terraform│ │
│  │  (mcp_      │  │  (cdp_      │  │ (web_       │  │ (ops_       │ │
│  │   server.go)│  │   agent.go) │  │  agent.go)  │  │  terraform. │ │
│  │             │  │             │  │             │  │   go)       │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │         │
│         └────────────────┴────────────────┴────────────────┘         │
│                              │                                        │
│                    ┌─────────▼─────────┐                             │
│                    │  Gateway Client   │                             │
│                    │  (gateway_        │                             │
│                    │   client.go)      │                             │
│                    └─────────┬─────────┘                             │
│                              │ HTTP/gRPC                            │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GATEWAY (node1-gateway)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  FastAPI    │  │  MQTT       │  │  Task       │  │  Policy     │ │
│  │  (main.py)  │  │  Service    │  │  Store      │  │  Engine     │ │
│  │             │  │  (mqtt_     │  │  (task_     │  │  (policy_   │ │
│  │             │  │   service.  │  │   store.py) │  │   engine.   │ │
│  │             │  │   py)       │  │             │  │   py)       │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │         │
│         └────────────────┴────────────────┴────────────────┘         │
│                              │                                        │
│                    ┌─────────▼─────────┐                             │
│                    │  Browser Runtime  │                             │
│                    │  (browser_        │                             │
│                    │   runtime.py)     │                             │
│                    └───────────────────┘                             │
│                              │                                        │
│                    ┌─────────▼─────────┐                             │
│                    │  Audit Logger     │                             │
│                    │  (audit.py)       │                             │
│                    └───────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Componenti

### omniclient (Go)

- **mcp_server.go**: Server MCP che espone tool `browser_navigate`, `browser_click`, `browser_type`, `browser_screenshot`, `ops_terraform_plan`, `ops_terraform_apply`
- **cdp_agent.go**: Agente Chrome DevTools Protocol per automazione browser locale (porta 9222)
- **web_agent.go**: Agente per navigazione e scraping web
- **ops_terraform.go**: Esecutore comandi Terraform per operazioni infrastrutturali
- **gateway_client.go**: Client HTTP/gRPC verso il gateway
- **mqtt_client.go**: Client MQTT per pub/sub asincrono
- **ws_server.go**: Server WebSocket per connessioni bidirezionali
- **heartbeat.go**: Health check periodici verso il gateway

### node1-gateway (Python)

- **main.py**: Applicazione FastAPI con endpoint REST e WebSocket
- **mqtt_service.py**: Servizio MQTT per messaggistica asincrona task/results
- **task_store.py**: Store in-memory per task in esecuzione
- **policy_engine.py**: Motore policy per autorizzazioni e limiti
- **browser_runtime.py**: Runtime browser remoto con gestione sessioni
- **audit.py**: Audit logging per tracciabilità operazioni
- **workspace_manager.py**: Gestione workspace e contesti multi-tenant

## Avvio Rapido

### Prerequisiti

- Go 1.21+
- Python 3.11+
- Chrome/Chromium con debug remoto abilitato (`--remote-debugging-port=9222`)
- Broker MQTT (es. Mosquitto, EMQX)
- Terraform CLI (per ops_*)

### Build

```bash
# omniclient (Go)
cd omniclient
go mod download
go build -o omniclient .

# node1-gateway (Python)
cd node1-gateway
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Configurazione

**omniclient** (`config.yaml` o env):
```yaml
gateway_url: http://localhost:8000
mqtt_broker: localhost:1883
cdp_port: 9222
mcp_port: 8080
```

**node1-gateway** (`.env`):
```
MQTT_BROKER=localhost:1883
CDP_REMOTE_URL=http://localhost:9222
AUDIT_LOG_PATH=/var/log/omni/audit.jsonl
```

### Avvio

```bash
# Terminal 1: Gateway
cd node1-gateway
uvicorn main:app --reload --port 8000

# Terminal 2: Chrome con CDP
google-chrome --remote-debugging-port=9222

# Terminal 3: omniclient
cd omniclient
./omniclient
```

### Verifica

```bash
# Test MCP server
curl http://localhost:8080/health

# Test gateway
curl http://localhost:8000/health

# Test MQTT
mosquitto_sub -t "omni/#" -v
```

## Documentazione

- [ARCHITECTURE.md](ARCHITECTURE.md) - Topologia dettagliata, flussi, contratti
- [SECURITY.md](SECURITY.md) - Principi sicurezza, hardening, incident response
- [BUILD.md](BUILD.md) - Istruzioni build, test, configurazione
- [NEXT_STEPS.md](NEXT_STEPS.md) - Priorità e checklist sviluppo
- [ROADMAP.md](ROADMAP.md) - Stato implementazione e backlog
- [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md) - Onboarding per AI assistant
- [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md) - Runbook operativo
- [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) - Mappa repository
- [omniclient/README.md](omniclient/README.md) - Setup worker Go
- [omniclient/MCP_SETUP.md](omniclient/MCP_SETUP.md) - Config MCP per Claude Desktop

## License

MIT