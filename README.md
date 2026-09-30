# OmniNode — Swarm Fabric v6.0

**Enterprise-Grade Zero-Dependency Browser Automation**

OmniNode è un fabric distribuito multi-agente che trasforma browser in interfacce sicure per AI assistant (Claude Desktop, ecc.) tramite MCP (Model Context Protocol).

## Caratteristiche Chiave

### 🚀 Zero-Dependency Architecture
- **Binario Go < 20MB** — Nessuna dipendenza esterna (CGO_ENABLED=0)
- **Job Objects OS-Native** — Zero zombie processes (Windows: Low Integrity Level)
- **Cross-Platform** — amd64/arm64 nativi (Ryzen desktop, Surface Pro 11 ARM)

### 🔒 Security Hardening
- **Low Integrity Token** — Impossibile scrivere in System32 o HKLM
- **Named Pipe DACL** — Solo processo Go autorizzato (zero IPC hijacking)
- **Cloudflare Access** — Zero Trust Edge con Service Tokens

### ⚡ Performance Enterprise
- **Spatial Pruning** — <10ms latenza (MutationObserver + WeakSet)
- **MQTT over WSS** — Keep-Alive 30s (zero drop Cloudflare 100s)
- **Audit WORM** — Transparency Log con Merkle Tree + Ed25519

## Architettura Swarm Fabric

```
Claude Desktop (Locale)
    ↓ stdio (MCP)
omniclient Go (Bridge)
    ↓ MQTT over WSS (Cloudflare Access)
node1-gateway Python (Orchestrator)
    ↓ MQTT (Swarm)
[omniclient-1, omniclient-2, ..., omniclient-N]
```

## Quick Start

```bash
# 1. Clona repository
git clone https://github.com/ZooL-OhKi/omninode.git
cd omninode

# 2. Build cross-platform (CGO_ENABLED=0)
export CGO_ENABLED=0
GOOS=linux GOARCH=amd64 go build -o bin/omniclient ./cmd/omniclient

# 3. Configura Cloudflare Access
# - Crea Service Token in Cloudflare Dashboard
# - Imposta CF_ACCESS_CLIENT_ID e CF_ACCESS_CLIENT_SECRET

# 4. Esegui
./bin/omniclient --config config.yaml
```

## Documentazione

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Architettura Swarm Fabric v6.0 completa
- **[INDEX.md](INDEX.md)** — Indice documenti e roadmap
- **[SECURITY.md](SECURITY.md)** — Security policy e hardening
- **[ROADMAP.md](ROADMAP.md)** — Roadmap 90 giorni (45 issue)

## License

MIT — Vedi [LICENSE](LICENSE)

## Status

**v6.0 Final** — Enterprise-Grade Zero-Dependency Swarm Fabric  
**Data:** 30 Settembre 2026
