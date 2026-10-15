# Architettura OmniNode

## Topologia

OmniNode adotta un'architettura client-gateway distribuita con separazione delle responsabilità:

```
┌──────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    omniclient (Go)                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │  MCP Server  │  │  CDP Agent   │  │  Web Agent   │          │  │
│  │  │  :8080       │  │  :9222       │  │  HTTP        │          │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │  │
│  │         │                 │                  │                   │  │
│  │         └─────────────────┴──────────────────┘                   │  │
│  │                           │                                       │  │
│  │                  ┌────────▼────────┐                             │  │
│  │                  │ Gateway Client  │                             │  │
│  │                  │ HTTP/gRPC       │                             │  │
│  │                  └────────┬────────┘                             │  │
│  │                           │                                       │  │
│  │                  ┌────────▼────────┐                             │  │
│  │                  │   MQTT Client   │                             │  │
│  │                  │   Pub/Sub       │                             │  │
│  │                  └────────┬────────┘                             │  │
│  └───────────────────────────┼───────────────────────────────────────┘  │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
                               │ HTTP/gRPC + MQTT
                               │
┌──────────────────────────────▼───────────────────────────────────────────┐
│                          GATEWAY LAYER                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                   node1-gateway (Python/FastAPI)                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  FastAPI     │  │  MQTT Service │  │  Task Store  │             │  │
│  │  │  :8000       │  │  :1883        │  │  In-Memory  │             │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │  │
│  │         │                 │                  │                      │  │
│  │         └─────────────────┴──────────────────┘                      │  │
│  │                           │                                         │  │
│  │         ┌─────────────────┴──────────────────┐                      │  │
│  │         │                                     │                     │  │
│  │  ┌──────▼───────┐                    ┌───────▼────────┐            │  │
│  │  │ Policy       │                    │  Browser       │            │  │
│  │  │ Engine       │                    │  Runtime       │            │  │
│  │  └──────┬───────┘                    └───────┬────────┘            │  │
│  │         │                                     │                     │  │
│  │         └─────────────────┬───────────────────┘                     │  │
│  │                           │                                         │  │
│  │                  ┌────────▼────────┐                               │  │
│  │                  │   Audit Logger  │                               │  │
│  │                  │   JSONL         │                               │  │
│  │                  └─────────────────┘                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Flussi Principali

### 1. Navigazione Browser (browser_navigate)

```
Client (MCP) → mcp_server.go → cdp_agent.go → Chrome CDP (:9222)
                    ↓
              gateway_client.go → HTTP POST /browser/navigate
                    ↓
              node1-gateway → mqtt_service.py → topic: omni/browser/request
                    ↓
              browser_runtime.py → esegue navigazione
                    ↓
              mqtt_service.py → topic: omni/browser/result
                    ↓
              gateway_client.go → mcp_server.go → MCP Client
```

**Contratto MQTT**:
```json
{
  "task_id": "uuid4",
  "action": "navigate",
  "url": "https://example.com",
  "timeout_ms": 30000,
  "workspace_id": "default"
}
```

### 2. Operazioni Terraform (ops_terraform_plan)

```
Client (MCP) → mcp_server.go → ops_terraform.go → terraform CLI
                    ↓
              ops_terraform.go → exec.Command("terraform", "plan")
                    ↓
              mcp_server.go → MCP Client (stdout/stderr)
```

**Contratto**:
```json
{
  "command": "plan",
  "directory": "/path/to/infra",
  "vars": {"environment": "prod"},
  "timeout_seconds": 300
}
```

### 3. Heartbeat e Health Check

```
omniclient → heartbeat.go → HTTP GET /health (gateway)
                    ↓
              gateway → 200 OK + metadata
                    ↓
              heartbeat.go → log + retry (max 3 tentativi)
```

## Contratti API

### MCP Tools (omniclient)

| Tool | Input | Output | Descrizione |
|------|-------|--------|-------------|
| `browser_navigate` | `{url: string}` | `{success: bool, title: string}` | Naviga a URL |
| `browser_click` | `{selector: string}` | `{success: bool}` | Click elemento |
| `browser_type` | `{selector: string, text: string}` | `{success: bool}` | Digita testo |
| `browser_screenshot` | `{full_page: bool}` | `{screenshot: base64}` | Screenshot |
| `ops_terraform_plan` | `{directory: string, vars: object}` | `{output: string}` | Terraform plan |
| `ops_terraform_apply` | `{directory: string, vars: object}` | `{output: string}` | Terraform apply |

### Gateway REST API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check gateway |
| `/browser/navigate` | POST | Richiesta navigazione browser |
| `/browser/screenshot` | POST | Richiesta screenshot |
| `/task/{task_id}/status` | GET | Stato task |
| `/audit/logs` | GET | Log audit (admin) |

### MQTT Topics

| Topic | Direzione | Payload |
|-------|-----------|---------|
| `omni/browser/request` | client→gateway | Task browser |
| `omni/browser/result` | gateway→client | Result browser |
| `omni/ops/request` | client→gateway | Task ops |
| `omni/ops/result` | gateway→client | Result ops |
| `omni/heartbeat` | client→gateway | Heartbeat |

## Limitazioni

### Performance

- **CDP locale**: Chrome deve essere eseguito con `--remote-debugging-port=9222`
- **MQTT**: Latenza tipica <100ms per messaggi piccoli (<10KB)
- **HTTP/gRPC**: Timeout default 30s per richieste sincrone

### Sicurezza

- **Nessuna autenticazione** abilitata di default (da configurare in produzione)
- **CDP** esposto su localhost:9222 (firewall richiesto)
- **MQTT** senza TLS di default (abilitare `mqtts://` in produzione)

### Scalabilità

- **Task store**: In-memory, non persistente (max ~1000 task concorrenti)
- **Browser runtime**: Single-instance (no multi-sessione parallela)
- **Gateway**: Single-node (no clustering nativo)

## Dipendenze Critiche

| Componente | Dipendenza | Versione Min | Criticità |
|------------|------------|--------------|-----------|
| omniclient | Go | 1.21 | Alta |
| omniclient | Chrome CDP | 114+ | Alta |
| node1-gateway | Python | 3.11 | Alta |
| node1-gateway | FastAPI | 0.100+ | Media |
| node1-gateway | paho-mqtt | 1.6+ | Media |
| ops_terraform | Terraform CLI | 1.5+ | Alta |

## Invarianti

1. **CDP sempre disponibile**: Chrome deve essere raggiungibile su localhost:9222
2. **MQTT broker attivo**: Gateway e client devono connettersi allo stesso broker
3. **Task ID univoci**: UUID v4 per ogni task, mai riutilizzare
4. **Audit immutabile**: Log audit sono append-only, mai modificare/eliminare
5. **Policy enforcement**: Ogni richiesta browser passa dal policy engine
