# Build - OmniNode

## Prerequisiti

### Sistema Operativo

- **Linux**: Ubuntu 22.04+, Debian 12+, RHEL 9+
- **macOS**: 13+ (Ventura o superiore)
- **Windows**: 11 (WSL2 consigliato)

### Dipendenze

| Software | Versione | Installazione (Ubuntu) |
|----------|----------|------------------------|
| Go | 1.21+ | `sudo apt install golang-go` |
| Python | 3.11+ | `sudo apt install python3.11 python3.11-venv` |
| Chrome | 114+ | `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb` |
| Git | 2.30+ | `sudo apt install git` |
| Make | 4.0+ | `sudo apt install make` |
| Docker | 24+ (opzionale) | `sudo apt install docker.io` |

### Dipendenze Opzionali

| Software | Scopo | Installazione |
|----------|-------|---------------|
| Mosquitto | Broker MQTT locale | `sudo apt install mosquitto` |
| Terraform | Testing ops_* | `wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip` |
| protoc | Compilazione proto (futuro) | `sudo apt install protobuf-compiler` |

## Build omniclient (Go)

### 1. Download Dipendenze

```bash
cd omniclient
go mod download
```

### 2. Build Binario

```bash
# Build standard
go build -o omniclient .

# Build ottimizzato per produzione
go build -ldflags="-s -w" -o omniclient .

# Build con debug symbols
go build -gcflags="all=-N -l" -o omniclient .
```

### 3. Verifica

```bash
# Versione Go
go version

# Test unitari
go test -v ./...

# Test con coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### 4. Cross-Compilation

```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 go build -o omniclient-linux-amd64 .

# macOS ARM64
GOOS=darwin GOARCH=arm64 go build -o omniclient-darwin-arm64 .

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -o omniclient-windows-amd64.exe .
```

## Build node1-gateway (Python)

### 1. Virtual Environment

```bash
cd node1-gateway
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
```

### 2. Install Dipendenze

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Verifica

```bash
python --version
pytest -v
pytest --cov=. --cov-report=term-missing
```

## Configurazione

### omniclient (config.yaml)

```yaml
gateway_url: http://localhost:8000
mqtt_broker: localhost:1883
cdp_port: 9222
mcp_port: 8080
log_level: info
```

### node1-gateway (.env)

```
BIND_HOST=127.0.0.1
BIND_PORT=8000
MQTT_BROKER=localhost:1883
AUDIT_LOG_PATH=/var/log/omni/audit.jsonl
POLICY_ENFORCE=true
LOG_LEVEL=info
```

## Test

### omniclient

```bash
cd omniclient
go test -v ./...
go test -race ./...
```

### node1-gateway

```bash
cd node1-gateway
source venv/bin/activate
pytest -v
pytest --cov=. --cov-report=term-missing
```

## Deployment

### Sviluppo Locale

```bash
# Terminal 1: Mosquitto
mosquitto -c /etc/mosquitto/mosquitto.conf

# Terminal 2: Chrome
google-chrome --remote-debugging-port=9222

# Terminal 3: Gateway
cd node1-gateway && uvicorn main:app --reload --port 8000

# Terminal 4: omniclient
cd omniclient && ./omniclient
```

## Troubleshooting

**Go: "module not found"**
```bash
go clean -modcache && go mod download
```

**Chrome: "Cannot connect to CDP"**
```bash
curl http://localhost:9222/json/version
pkill chrome && google-chrome --remote-debugging-port=9222
```

**MQTT: "Connection refused"**
```bash
systemctl status mosquitto
mosquitto_sub -u omniclient -P ${MQTT_PASSWORD} -t "omni/#" -v
```

## Release

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## Risorse

- [Go Documentation](https://go.dev/doc/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
