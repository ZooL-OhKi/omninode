# omniclient - OmniNode Client (Go)

## Panoramica

omniclient è il componente client di OmniNode, implementato in Go. Fornisce un server MCP locale che espone tool per automazione browser (`browser_*`) e operazioni infrastrutturali (`ops_*`).

## Architettura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         omniclient (Go)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  MCP Server  │  │  CDP Agent   │  │  Web Agent   │              │
│  │  :8080       │  │  :9222       │  │  HTTP        │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│         └─────────────────┴──────────────────┘                       │
│                           │                                          │
│         ┌─────────────────┴──────────────────┐                       │
│  ┌──────▼───────┐                    ┌───────▼────────┐             │
│  │  Gateway     │                    │  MQTT          │             │
│  │  Client      │                    │  Client        │             │
│  │  (HTTP)      │                    │  (Pub/Sub)     │             │
│  └──────┬───────┘                    └───────┬────────┘             │
│         │                                     │                      │
│         └─────────────────┬───────────────────┘                      │
│                           │                                          │
│                  ┌────────▼────────┐                                │
│                  │  WS Server      │                                │
│                  │  :8081          │                                │
│                  └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Setup Worker

### Prerequisiti

- Go 1.21+
- Chrome/Chromium 114+ (con `--remote-debugging-port=9222`)
- Broker MQTT (Mosquitto, EMQX)
- node1-gateway raggiungibile

### Installazione

```bash
git clone https://github.com/ZooL-OhKi/omninode.git
cd omninode/omniclient
go mod download
go build -ldflags="-s -w" -o omniclient .
```

### Configurazione (config.yaml)

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

### Avvio

```bash
./omniclient
nohup ./omniclient > /var/log/omni/omniclient.log 2>&1 &
sudo systemctl start omninode-client
```

### Verifica

```bash
curl http://localhost:8080/health
curl http://localhost:8080/tools
tail -f /var/log/omni/omniclient.log
```

## Tool MCP

| Tool | Input | Output | Descrizione |
|------|-------|--------|-------------|
| `browser_navigate` | `{url: string}` | `{success: bool, title: string}` | Naviga a URL |
| `browser_click` | `{selector: string}` | `{success: bool}` | Click elemento |
| `browser_type` | `{selector: string, text: string}` | `{success: bool}` | Digita testo |
| `browser_screenshot` | `{full_page: bool}` | `{screenshot: base64}` | Screenshot |
| `ops_terraform_plan` | `{directory: string, vars: object}` | `{output: string}` | Terraform plan |
| `ops_terraform_apply` | `{directory: string, vars: object}` | `{output: string}` | Terraform apply |

## Sicurezza

### Hardening

```bash
go build -ldflags="-s -w" -o omniclient .
useradd -r -s /bin/false omniclient
chown -R omniclient:omniclient /opt/omniclient
sudo -u omniclient /opt/omniclient/omniclient
ufw deny from any to any port 8080
ufw allow from 127.0.0.1 to any port 8080
```

### Best Practice

1. Mai esporre CDP su rete pubblica: Solo localhost:9222
2. Usare auth token MCP: Configurare `mcp_auth_token` in produzione
3. Limitare permessi utente: omniclient non deve avere accesso root
4. Audit logging: Abilitare log per tutte le operazioni
5. TLS per MQTT: Usare mqtts:// con certificati client

## Troubleshooting

### MCP server non risponde

```bash
ps aux | grep omniclient
netstat -tlnp | grep 8080
tail -100 /var/log/omni/omniclient.log | grep ERROR
systemctl restart omninode-client
```

### CDP non connesso

```bash
curl http://localhost:9222/json/version
pkill chrome
google-chrome --remote-debugging-port=9222 --user-data-dir=/opt/chrome-profiles/omni &
curl http://localhost:9222/json/version
```

### MQTT disconnesso

```bash
systemctl status mosquitto
mosquitto_sub -u omniclient -P ${MQTT_PASSWORD} -t "omni/#" -v
journalctl -u mosquitto | tail -50
```

### Gateway irraggiungibile

```bash
curl http://gateway:8000/health
ping gateway
grep "gateway" /var/log/omni/omniclient.log | grep ERROR
```

## Test

```bash
go test -v ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
go test -race ./...
go test -bench=. -benchmem ./...
```

## Dipendenze

| Pacchetto | Versione | Scopo |
|-----------|----------|-------|
| mcp-go | v0.1.0 | MCP server |
| gorilla/websocket | v1.5.0 | WebSocket |
| paho.mqtt.golang | v1.4.0 | MQTT client |
| chromedp | v0.9.0 | CDP client |
| zap | v1.25.0 | Logging |
| yaml.v3 | v3.0.1 | Config YAML |

## Risorse

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architettura dettagliata
- [MCP_SETUP.md](MCP_SETUP.md) - Config MCP per Claude Desktop
- [HANDOFF.md](HANDOFF.md) - Stato componenti
- [MCP Specification](https://modelcontextprotocol.io/)
- [Chromedp Documentation](https://pkg.go.dev/github.com/chromedp/chromedp)
