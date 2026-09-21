# Omninode

**Fabric di calcolo agentico distribuito, zero-cost, controllato via MCP (Model Context Protocol)**

## Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL AI AGENTS                          │
│              (Claude, GPT, Llama, etc. via MCP)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OMNICLIENT (Desktop App)                     │
│              Go + Wails | Windows/macOS/Linux                   │
│  - MCP Server per agenti esterni                               │
│  - Orchestratore locale dei nodi                               │
│  - Zero-touch updates via GitHub Actions                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MQTT / HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NODE1-GATEWAY (Cloud)                        │
│              Python + FastAPI + Uvicorn                         │
│  - Validazione header X-Omninode-Key                            │
│  - Routing messaggi MQTT                                        │
│  - API REST per gestione nodi                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MQTT
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED NODES                            │
│         (Node2, Node3, ... | Edge/Cloud/IoT)                    │
│  - Esecuzione task computazionali                               │
│  - Reporting stato e risultati                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Componenti

### OmniClient
Applicazione desktop che funge da hub centrale:
- **Tecnologia**: Go + Wails (frontend web-based)
- **Ruolo**: MCP Server per agenti IA esterni
- **Deploy**: Build multi-piattaforma (Windows, macOS, Linux)

### Node1-Gateway
Gateway cloud per la comunicazione distribuita:
- **Tecnologia**: Python + FastAPI + Uvicorn
- **Ruolo**: Validazione, routing MQTT, API REST
- **Deploy**: Container Docker o VM cloud

## Quick Start

### Prerequisiti
- Go 1.21+
- Python 3.11+
- Node.js 18+
- Wails CLI: `go install github.com/wailsapp/wails/v2/cmd/wails@latest`

### Sviluppo Locale

**OmniClient:**
```bash
cd omniclient
wails dev
```

**Node1-Gateway:**
```bash
cd node1-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Build

**OmniClient (multi-piattaforma):**
```bash
cd omniclient
wails build -platform windows darwin linux
```

**Node1-Gateway:**
```bash
cd node1-gateway
python -m build
```

## CI/CD

La pipeline GitHub Actions (`build.yml`) gestisce:
- Build automatico su push a `main`
- Test e lint per Python e Go
- Build multi-piattaforma per OmniClient
- Release automatica su tag `v*`

## License

MIT
