# MCP Setup - omniclient

## Configurazione Claude Desktop

### 1. Installazione MCP Client

Claude Desktop supporta nativamente MCP. Per configurare omniclient:

**macOS**:
```bash
mkdir -p ~/Library/Application\ Support/Claude/MCP
```

**Linux**:
```bash
mkdir -p ~/.config/Claude/MCP
```

**Windows**:
```bash
mkdir %APPDATA%\Claude\MCP
```

### 2. Configurazione MCP Server

Creare file `mcp_config.json`:

```json
{
  "mcpServers": {
    "omniclient": {
      "command": "/opt/omniclient/omniclient",
      "args": ["-config", "/opt/omniclient/config.yaml"],
      "env": {
        "MQTT_PASSWORD": "secret123",
        "MCP_AUTH_TOKEN": "omni_mcp_token_12345",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### 3. Verifica Connessione

```bash
# Health check
curl http://localhost:8080/health
# Expected: {"status":"ok","mcp_server":"running"}

# Lista tool
curl http://localhost:8080/tools
# Expected: lista tool browser_* e ops_*
```

## Tool Disponibili

### browser_navigate

Naviga a un URL con Chrome CDP.

**Esempio**:
```json
{
  "tool": "browser_navigate",
  "arguments": {
    "url": "https://example.com",
    "timeout_ms": 30000
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "title": "Example Domain",
  "final_url": "https://example.com/"
}
```

### browser_click

Click su un elemento (CSS selector).

**Esempio**:
```json
{
  "tool": "browser_click",
  "arguments": {
    "selector": "#submit-button",
    "timeout_ms": 5000
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "element_text": "Submit"
}
```

### browser_type

Digita testo in un input field.

**Esempio**:
```json
{
  "tool": "browser_type",
  "arguments": {
    "selector": "#username",
    "text": "mario.rossi",
    "clear_first": true
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "characters_typed": 11
}
```

### browser_screenshot

Screenshot della pagina.

**Esempio**:
```json
{
  "tool": "browser_screenshot",
  "arguments": {
    "full_page": true,
    "format": "png"
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAA...",
  "width": 1920,
  "height": 1080
}
```

### ops_terraform_plan

Esegue `terraform plan`.

**Esempio**:
```json
{
  "tool": "ops_terraform_plan",
  "arguments": {
    "directory": "/path/to/infra",
    "vars": {"environment": "prod"},
    "timeout_seconds": 300
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "output": "Plan: 2 to add, 0 to change, 0 to destroy.",
  "exit_code": 0
}
```

### ops_terraform_apply

Esegue `terraform apply`.

**Esempio**:
```json
{
  "tool": "ops_terraform_apply",
  "arguments": {
    "directory": "/path/to/infra",
    "vars": {"environment": "prod"},
    "auto_approve": false,
    "timeout_seconds": 600
  }
}
```

**Risposta**:
```json
{
  "success": true,
  "output": "Apply complete! Resources: 2 added.",
  "exit_code": 0
}
```

## Verifica Setup

### 1. Test Connessione

```bash
# Health gateway
curl http://localhost:8000/health

# Health omniclient
curl http://localhost:8080/health

# MQTT broker
mosquitto_sub -t "omni/#" -v
```

### 2. Test Tool MCP

```bash
# browser_navigate
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool":"browser_navigate","arguments":{"url":"https://example.com"}}'

# ops_terraform_plan
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool":"ops_terraform_plan","arguments":{"directory":"/tmp/test-infra"}}'
```

### 3. Test Claude Desktop

1. Aprire Claude Desktop
2. Creare nuovo chat
3. Usare prompt: "Naviga su https://example.com e fai screenshot"
4. Verificare che Claude usi tool browser_navigate e browser_screenshot

## Troubleshooting

### MCP server non risponde

```bash
ps aux | grep omniclient
netstat -tlnp | grep 8080
tail -100 /var/log/omni/omniclient.log | grep ERROR
systemctl restart omninode-client
```

### Tool non disponibili

```bash
curl http://localhost:8080/tools
systemctl restart omninode-client
```

### Claude non usa MCP

1. Verificare mcp_config.json in ~/Library/Application Support/Claude/MCP/
2. Riavviare Claude Desktop
3. Controllare log Claude: ~/Library/Logs/Claude/

### Gateway irraggiungibile

```bash
curl http://gateway:8000/health
grep "gateway" /var/log/omni/omniclient.log | grep ERROR
systemctl restart omninode-gateway
```

## Risorse

- [README.md](README.md) - Setup omniclient
- [HANDOFF.md](HANDOFF.md) - Stato componenti
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architettura dettagliata
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Desktop Docs](https://claude.ai/docs)
