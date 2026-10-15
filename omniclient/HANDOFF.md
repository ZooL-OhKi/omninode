# Handoff - omniclient

## Stato Componenti

### Implementati (100%)

| Componente | File | Stato | Note |
|------------|------|-------|------|
| **MCP Server** | mcp_server.go | ✅ Completo | Tool browser_* e ops_* funzionanti |
| **CDP Agent** | cdp_agent.go | ✅ Completo | Chrome DevTools Protocol su :9222 |
| **Web Agent** | web_agent.go | ✅ Completo | Navigazione e scraping web |
| **Ops Terraform** | ops_terraform.go | ✅ Completo | Esecuzione comandi Terraform |
| **Gateway Client** | gateway_client.go | ✅ Completo | HTTP client verso node1-gateway |
| **MQTT Client** | mqtt_client.go | ✅ Completo | Pub/sub asincrono |
| **WS Server** | ws_server.go | ✅ Completo | WebSocket locale su :8081 |
| **Heartbeat** | heartbeat.go | ✅ Completo | Health check periodici |

### Parziali (50-80%)

| Componente | File | Stato | Lavoro Mancante |
|------------|------|-------|-----------------|
| **Autenticazione MCP** | mcp_server.go | 🔄 50% | Middleware JWT da implementare |
| **TLS MQTT** | mqtt_client.go | 🔄 30% | Supporto mqtts:// da aggiungere |
| **Retry Logic** | gateway_client.go | 🔄 60% | Exponential backoff parziale |

### Non Implementati (0%)

| Componente | File | Priorità | Sforzo |
|------------|------|----------|--------|
| **Circuit Breaker** | gateway_client.go | Media | 2-3 giorni |
| **Metrics Export** | main.go | Bassa | 3-5 giorni |
| **gRPC Client** | gateway_client.go | Bassa | 5-7 giorni |

## Dipendenze

### Runtime

| Dipendenza | Versione | Criticità | Fallback |
|------------|----------|-----------|----------|
| **Go** | 1.21+ | Alta | - |
| **Chrome CDP** | 114+ | Alta | Firefox Marionette (backlog) |
| **MQTT Broker** | 2.0+ | Media | EMQX, VerneMQ |
| **Gateway HTTP** | - | Alta | gRPC (backlog) |

### Go Modules

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

## Configurazione

### config.yaml

```yaml
gateway_url: http://localhost:8000
mqtt_broker: localhost:1883
mqtt_username: omniclient
mqtt_password: ${MQTT_PASSWORD}
cdp_port: 9222
cdp_timeout_ms: 30000
mcp_port: 8080
mcp_host: 127.0.0.1
log_level: info
heartbeat_interval_sec: 30
```

### Environment Variables

```bash
export MQTT_PASSWORD=secret123
export MCP_AUTH_TOKEN=omni_mcp_token_12345
export LOG_LEVEL=info
export GATEWAY_URL=http://localhost:8000
```

## Rischi

### Tecnici

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| **CDP instabile** | Media | Alto | Retry logic, timeout 30s |
| **MQTT message loss** | Bassa | Alto | QoS 1, persistenza task store (gateway) |
| **Gateway downtime** | Media | Alto | Circuit breaker, retry con backoff |
| **Memory leak** | Bassa | Medio | Restart automatico ogni 24h (cron) |

### Operativi

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| **Nessun monitoring** | Alta | Medio | Implementare Prometheus metrics (backlog) |
| **Config hardcoded** | Media | Alto | Usare sempre env var o vault |
| **Log non rotati** | Media | Basso | logrotate configurazione |

## Prossimi Passi

### Settimana 1-2

1. **Autenticazione MCP**
   - Implementare middleware JWT in mcp_server.go
   - Testare con Claude Desktop
   - Aggiornare MCP_SETUP.md

2. **TLS MQTT**
   - Aggiungere supporto mqtts:// in mqtt_client.go
   - Generare certificati TLS
   - Testare connessioni sicure

3. **Retry Logic Completa**
   - Implementare exponential backoff in gateway_client.go
   - Aggiungere circuit breaker
   - Testare scenari di fallimento

### Settimana 3-4

4. **Metrics Export**
   - Integrare go_prometheus_client
   - Esportare: request_count, latency, error_rate
   - Dashboard Grafana

5. **Test Coverage**
   - Completare unit test (target: 80%)
   - Aggiungere integration test
   - CI/CD pipeline

## Checklist Handover

- [ ] Tutti i file documentazione aggiornati
- [ ] Test coverage > 70%
- [ ] Autenticazione MCP implementata
- [ ] TLS MQTT configurato
- [ ] Retry logic completa
- [ ] Monitoring attivo
- [ ] Log rotazione configurata
- [ ] Backup e recovery testati

## Contatti

| Ruolo | Nome | Email | Slack |
|-------|------|-------|-------|
| **Go Developer** | [Da assegnare] | [TBD] | [TBD] |
| **Tech Lead** | [Da assegnare] | [TBD] | [TBD] |

## Appendice: Comandi Utili

```bash
# Build
go build -ldflags="-s -w" -o omniclient .

# Test
go test -v ./...
go test -race ./...
go test -coverprofile=coverage.out ./...

# Run
./omniclient -config config.yaml

# Debug
dlv debug .
```
