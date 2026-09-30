# AI Onboarding - OmniNode

## Regole per AI Assistant

### Cosa Fare

1. **Leggere prima ARCHITECTURE.md**: Comprendere topologia client-gateway prima di modificare codice
2. **Testare ogni modifica**: Eseguire `go test ./...` (Go) o `pytest` (Python) prima di commit
3. **Mantenere backward compatibility**: Non rompere API MCP esistenti senza major version bump
4. **Documentare cambiamenti**: Aggiornare file .md rilevanti se si modifica comportamento
5. **Seguire convenzioni**: Nomi file snake_case (Python), camelCase (Go), commenti in inglese

### Cosa Non Fare

1. **Non modificare config di default** senza esplicita richiesta
2. **Non introdurre dipendenze** senza approvazione (controllare requirements.txt, go.mod)
3. **Non disabilitare security** (policy_engine, audit) anche per testing
4. **Non commitare secret** (.env, chiavi API) - usare env var o vault
5. **Non ignorare test falliti**: Fixare prima di procedere

## Architettura (Breve)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         omniclient (Go)                              │
│  MCP Server (:8080) → CDP Agent (:9222) → Chrome                    │
│                      → Gateway Client (HTTP) → node1-gateway        │
│                      → MQTT Client (Pub/Sub) → Mosquitto            │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓ HTTP + MQTT
┌─────────────────────────────────────────────────────────────────────┐
│                      node1-gateway (Python)                          │
│  FastAPI (:8000) → MQTT Service → Task Store → Policy Engine        │
│                              → Browser Runtime → Chrome CDP          │
│                              → Audit Logger → JSONL file             │
└─────────────────────────────────────────────────────────────────────┘
```

**Flusso tipico (browser_navigate)**:
1. MCP Client (Claude Desktop) → `browser_navigate(url="https://example.com")`
2. mcp_server.go → gateway_client.go → HTTP POST /browser/navigate
3. node1-gateway → mqtt_service.py → topic `omni/browser/request`
4. browser_runtime.py → esegue navigazione su Chrome CDP
5. browser_runtime.py → mqtt_service.py → topic `omni/browser/result`
6. gateway_client.go → mcp_server.go → MCP Client (response)

## Convenzioni di Codice

### Go (omniclient/)

```go
// Package comment per ogni file
package main

// Funzioni: UpperCamelCase per exported, lowerCamelCase per private
func NewMCPServer(config Config) *MCPServer { ... }
func (s *MCPServer) handleNavigate(ctx context.Context, req NavigateRequest) (*NavigateResponse, error) { ... }

// Struct: UpperCamelCase
type NavigateRequest struct {
    URL       string `json:"url"`
    TimeoutMs int    `json:"timeout_ms"`
}

// Errori: wrapping con fmt.Errorf("%w")
if err != nil {
    return nil, fmt.Errorf("navigate to %s: %w", req.URL, err)
}

// Test: file *_test.go, funzione TestXxx(t *testing.T)
func TestMCPServer_Navigate(t *testing.T) {
    // ...
}
```

### Python (node1-gateway/)

```python
# Docstring per ogni modulo
"""MQTT service for async task messaging."""

# Funzioni: snake_case, type hints obbligatori
def publish_task(topic: str, payload: dict) -> None:
    """Publish task to MQTT topic."""
    ...

# Classi: UpperCamelCase, docstring per metodi pubblici
class BrowserRuntime:
    """Remote browser automation via CDP."""
    
    async def navigate(self, url: str, timeout_ms: int = 30000) -> dict:
        """Navigate to URL and return result."""
        ...

# Eccezioni: wrapping con raise ... from
try:
    ...
except Exception as e:
    raise RuntimeError(f"navigate failed: {e}") from e

# Test: file test_*.py, funzione test_xxx()
def test_browser_runtime_navigate():
    # ...
```

## Tool MCP Disponibili

| Tool | Input | Output | Descrizione |
|------|-------|--------|-------------|
| `browser_navigate` | `{url: string}` | `{success: bool, title: string}` | Naviga a URL |
| `browser_click` | `{selector: string}` | `{success: bool}` | Click elemento |
| `browser_type` | `{selector: string, text: string}` | `{success: bool}` | Digita testo |
| `browser_screenshot` | `{full_page: bool}` | `{screenshot: base64}` | Screenshot |
| `ops_terraform_plan` | `{directory: string, vars: object}` | `{output: string}` | Terraform plan |
| `ops_terraform_apply` | `{directory: string, vars: object}` | `{output: string}` | Terraform apply |

## Comandi Utili

```bash
# Build omniclient
cd omniclient && go build -o omniclient .

# Test omniclient
cd omniclient && go test -v ./...

# Build node1-gateway (venv)
cd node1-gateway && source venv/bin/activate && pip install -r requirements.txt

# Test node1-gateway
cd node1-gateway && pytest -v

# Avvio locale (4 terminal)
# Terminal 1: Mosquitto
mosquitto -c /etc/mosquitto/mosquitto.conf

# Terminal 2: Chrome
google-chrome --remote-debugging-port=9222

# Terminal 3: Gateway
cd node1-gateway && uvicorn main:app --reload

# Terminal 4: omniclient
cd omniclient && ./omniclient
```

## Debug

### Problemi Comuni

**MCP server non risponde**:
```bash
curl http://localhost:8080/health
# Se fallisce: controllare log omniclient.log
tail -f /var/log/omni/omniclient.log
```

**Gateway non riceve task MQTT**:
```bash
# Sottoscrivi topic
mosquitto_sub -t "omni/#" -v

# Pubblica test
mosquitto_pub -t "omni/browser/request" -m '{"task_id":"test"}'
```

**Chrome CDP non connesso**:
```bash
curl http://localhost:9222/json/version
# Se fallisce: riavviare Chrome
pkill chrome && google-chrome --remote-debugging-port=9222
```

## Risorse

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Topologia dettagliata
- [BUILD.md](../BUILD.md) - Istruzioni build
- [SECURITY.md](../SECURITY.md) - Principi sicurezza
- [MCP Specification](https://modelcontextprotocol.io/)
