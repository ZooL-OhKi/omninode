# Indice - OmniNode

## Documentazione Root

| File | Descrizione |
|------|-------------|
| [README.md](README.md) | Panoramica, architettura, avvio rapido |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Topologia dettagliata, flussi, contratti |
| [SECURITY.md](SECURITY.md) | Principi sicurezza, hardening, incident response |
| [BUILD.md](BUILD.md) | Build, test, configurazione, deployment |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Priorità sviluppo (alta/media/bassa) |
| [ROADMAP.md](ROADMAP.md) | Implementato, in progress, backlog |
| [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md) | Stato progetto, rischi, prossimi passi |

## Documentazione docs/

| File | Descrizione |
|------|-------------|
| [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md) | Onboarding per AI assistant (regole, architettura, convenzioni) |
| [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md) | Runbook operativo (preflight, avvio, incidenti, shutdown) |
| [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) | Mappa repository, dipendenze, invarianti |

## Documentazione omniclient/

| File | Descrizione |
|------|-------------|
| [omniclient/README.md](omniclient/README.md) | Setup worker Go, tool MCP, sicurezza |
| [omniclient/HANDOFF.md](omniclient/HANDOFF.md) | Stato componenti, dipendenze, configurazione |
| [omniclient/MCP_SETUP.md](omniclient/MCP_SETUP.md) | Config MCP per Claude Desktop, tool disponibili |

## Codice

### node1-gateway/ (Python)

| File | Descrizione |
|------|-------------|
| [node1-gateway/main.py](node1-gateway/main.py) | FastAPI app, endpoint REST + WebSocket |
| [node1-gateway/mqtt_service.py](node1-gateway/mqtt_service.py) | Servizio MQTT pub/sub |
| [node1-gateway/task_store.py](node1-gateway/task_store.py) | Store in-memory per task |
| [node1-gateway/policy_engine.py](node1-gateway/policy_engine.py) | Motore policy e autorizzazioni |
| [node1-gateway/browser_runtime.py](node1-gateway/browser_runtime.py) | Runtime browser remoto |
| [node1-gateway/audit.py](node1-gateway/audit.py) | Audit logging JSONL |
| [node1-gateway/workspace_manager.py](node1-gateway/workspace_manager.py) | Gestione workspace multi-tenant |

### omniclient/ (Go)

| File | Descrizione |
|------|-------------|
| [omniclient/main.go](omniclient/main.go) | Entry point, inizializzazione |
| [omniclient/mcp_server.go](omniclient/mcp_server.go) | Server MCP, tool browser_* e ops_* |
| [omniclient/cdp_agent.go](omniclient/cdp_agent.go) | Chrome DevTools Protocol agent |
| [omniclient/web_agent.go](omniclient/web_agent.go) | Navigazione e scraping web |
| [omniclient/ops_terraform.go](omniclient/ops_terraform.go) | Esecutore comandi Terraform |
| [omniclient/gateway_client.go](omniclient/gateway_client.go) | Client HTTP verso gateway |
| [omniclient/mqtt_client.go](omniclient/mqtt_client.go) | Client MQTT pub/sub |
| [omniclient/ws_server.go](omniclient/ws_server.go) | Server WebSocket locale |
| [omniclient/heartbeat.go](omniclient/heartbeat.go) | Health check periodici |

## Test

| File | Descrizione |
|------|-------------|
| [node1-gateway/test_main.py](node1-gateway/test_main.py) | Test FastAPI app |
| [node1-gateway/test_mqtt_service.py](node1-gateway/test_mqtt_service.py) | Test MQTT service |
| [node1-gateway/test_browser_runtime.py](node1-gateway/test_browser_runtime.py) | Test browser automation |
| [omniclient/mcp_server_test.go](omniclient/mcp_server_test.go) | Test MCP server |
| [omniclient/test_mcp_client.py](omniclient/test_mcp_client.py) | Test client MCP (Python) |

## Configurazione

| File | Descrizione |
|------|-------------|
| [node1-gateway/.env.example](node1-gateway/.env.example) | Template variabili ambiente gateway |
| [node1-gateway/requirements.txt](node1-gateway/requirements.txt) | Dipendenze Python gateway |
| [omniclient/go.mod](omniclient/go.mod) | Dipendenze Go omniclient |
| [omniclient/wails.json](omniclient/wails.json) | Config Wails (UI opzionale) |

## Risorse Esterne

- [MCP Specification](https://modelcontextprotocol.io/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Go Documentation](https://go.dev/doc/)
