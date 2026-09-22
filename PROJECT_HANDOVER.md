# Omninode - Project Handover Document

**Data:** 22 Settembre 2026  
**Stato:** Infrastruttura base completata e operativa  
**Repository:** https://github.com/ZooL-OhKi/omninode

---

## 📋 Panoramica del Progetto

**Omninode** è un fabric di calcolo agentico distribuito, zero-cost, controllato via MCP (Model Context Protocol) da agenti IA esterni, con deploy e aggiornamenti zero-touch tramite GitHub Actions.

### Obiettivo
Creare una rete di nodi computazionali distribuiti che possono essere orchestrati da agenti IA esterni (Gemini, Claude, etc.) tramite il protocollo MCP standard.

### Architettura ad Alto Livello

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL AI AGENTS                          │
│              (Gemini, Claude, etc. via MCP)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (stdio/SSE)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OMNICLIENT (Desktop App)                     │
│              Go + Wails | Windows/macOS/Linux                   │
│  - MCP Server esponibile ad agenti esterni                     │
│  - Gateway client verso Node1                                   │
│  - Zero-touch updates via GitHub Actions                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 NODE1-GATEWAY (Cloud/Edge)                      │
│              Python + FastAPI + Uvicorn                         │
│  - Validazione header X-Omninode-Key                            │
│  - MQTT bridge per nodi distribuiti                             │
│  - API REST per gestione nodi e task                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MQTT
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED NODES                            │
│         (Node2, Node3, ... | Edge/Cloud/IoT)                    │
│  - Pubblicano heartbeat su MQTT                                 │
│  - Ricevono task computazionali                                 │
│  - Restituiscono risultati                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Componenti Implementati

### 1. Node1-Gateway (Python/FastAPI)

**Path:** `node1-gateway/`  
**Stato:** ✅ COMPLETO E OPERATIVO

#### File Principali

- **`main.py`**: API REST FastAPI con autenticazione
- **`mqtt_service.py`**: Client MQTT thread-safe per comunicazione con nodi
- **`requirements.txt`**: Dipendenze Python
- **`.env`**: Configurazione (API key, MQTT settings)

#### API Endpoints

| Endpoint | Metodo | Auth | Descrizione |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | Health check pubblico |
| `/nodes` | GET | ✅ | Lista tutti i nodi connessi |
| `/nodes/{node_id}` | GET | ✅ | Stato di un nodo specifico |
| `/nodes/{node_id}/tasks` | POST | ✅ | Invia task a un nodo |
| `/fabric/health` | GET | ✅ | Salute complessiva del fabric |

#### Autenticazione

Tutti gli endpoint protetti richiedono header:
```
X-Omninode-Key: <api-key-dal-file-.env>
```

#### MQTT Topics

- `omninode/nodes/+/heartbeat` - Heartbeat dai nodi
- `omninode/nodes/+/status` - Status updates
- `omninode/nodes/+/results` - Risultati task
- `omninode/nodes/+/tasks` - Task da eseguire (publish dal gateway)

---

### 2. OmniClient (Go + Wails)

**Path:** `omniclient/`  
**Stato:** ✅ COMPLETO (gateway integration pronta)

#### File Principali

- **`main.go`**: App Wails con lifecycle
- **`mcp_server.go`**: Server MCP con 4 tools esponibili
- **`gateway_client.go`**: Client HTTP verso Node1 Gateway
- **`go.mod`**: Dipendenze Go

#### MCP Tools Esposti

| Tool | Input | Output | Descrizione |
|------|-------|--------|-------------|
| `list_nodes` | {} | `[]NodeStatus` | Lista nodi connessi |
| `get_node_status` | `{node_id: string}` | `NodeStatus` | Stato di un nodo |
| `dispatch_task` | `{node_id, task_type, payload}` | `{status, task_id}` | Invia task |
| `get_fabric_health` | {} | `{total_nodes, online_nodes, health_status}` | Salute fabric |

#### Modalità¹¹ di Esecuzione

**GUI Mode (default):**
```bash
wails dev
# MCP SSE disponibile su :8080
```

**Stdio Mode (per agenti IA):**
```bash
./omniclient --mcp-stdio
# MCP su stdin/stdout
```

---

### 3. Infrastructure

**Path:** `.github/workflows/`  
**Stato:** ✅ COMPLETO

#### CI/CD Pipeline

- **`build.yml`**: Build automatico su push e tag
  - Python: lint, test, package
  - Go: build multi-piattaforma (Windows, macOS, Linux)
  - Release automatica su GitHub Releases

---

## 📁 Struttura Repository

```
omninode/
├── .github/
│   └── workflows/
│       └── build.yml              # CI/CD pipeline
├── node1-gateway/
│   ├── main.py                    # FastAPI gateway
│   ├── mqtt_service.py            # MQTT client service
│   ├── requirements.txt           # Python dependencies
│   └── .env                       # Config (API key, MQTT)
├── omniclient/
│   ├── main.go                    # Wails app entry
│   ├── mcp_server.go              # MCP server implementation
│   ├── gateway_client.go          # HTTP client to gateway
│   ├── go.mod                     # Go module
│   ├── wails.json                 # Wails config
│   ├── MCP_SETUP.md               # Agent configuration guide
│   ├── test_mcp_client.py         # Python MCP test client
│   └── README.md                  # OmniClient docs
├── PROJECT_HANDOVER.md            # Questo file
└── README.md                      # Panoramica progetto
```

---

## 🚀 Istruzioni di Setup e Avvio

### Prerequisiti

- Python 3.11+
- Go 1.21+
- Mosquitto MQTT broker
- Wails CLI (opzionale, per OmniClient)

### Step 1: Installa Mosquitto MQTT

**Windows:**
```powershell
# Download: https://mosquitto.org/download/
# Installa in C:\Program Files\mosquitto

# Crea config
New-Item -ItemType Directory -Force -Path "C:\Program Files\mosquitto\{config,data,log}"
@"
listener 1883
allow_anonymous true
persistence true
"@ | Out-File "C:\Program Files\mosquitto\config\mosquitto.conf" -Encoding ascii

# Avvia
& "C:\Program Files\mosquitto\mosquitto.exe" -c config\mosquitto.conf -v
```

### Step 2: Avvia Node1 Gateway

```powershell
cd node1-gateway

# Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate.bat

# Installa dipendenze
pip install -r requirements.txt

# Configura .env (genera chiave API casuale)
# OMNINODE_API_KEY=<chiave-casuale>
# MQTT_HOST=localhost
# MQTT_PORT=1883

# Avvia gateway
$env:OMNINODE_API_KEY="<tua-chiave>"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Test Gateway

```powershell
# Health check
curl http://localhost:8000/health

# Lista nodi (richiede chiave)
$headers = @{"X-Omninode-Key" = "<tua-chiave>"}
Invoke-WebRequest -Uri "http://localhost:8000/nodes" -Headers $headers -UseBasicParsing

# Pubblica heartbeat di test
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -t "omninode/nodes/test-node/heartbeat" -m '{"status":"online","load":25}'
```

### Step 4: Avvia OmniClient (Opzionale)

```powershell
cd omniclient

# Installa dipendenze Go
go mod download

# Modalità¹¹ sviluppo GUI
wails dev

# Oppure MCP stdio per agenti IA
./omniclient --mcp-stdio
```

---

## 🧪 Test Procedures

### Test 1: Nodo Fittizio

```powershell
# Pubblica heartbeat
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -t "omninode/nodes/test-node/heartbeat" -m '{"status":"online","load":25}'

# Verifica API
$headers = @{"X-Omninode-Key" = "<chiave>"}
Invoke-WebRequest -Uri "http://localhost:8000/nodes" -Headers $headers -UseBasicParsing
# Dovresti vedere: [{"node_id":"test-node","status":"online",...}]

# Verifica fabric health
Invoke-WebRequest -Uri "http://localhost:8000/fabric/health" -Headers $headers -UseBasicParsing
# Dovresti vedere: {"total_nodes":1,"online_nodes":1,"health_status":"healthy"}
```

### Test 2: MCP Client Python

```powershell
cd omniclient
python test_mcp_client.py --stdio
# Esegue tutti i 4 tools MCP e stampa risultati
```

### Test 3: Agente IA (Gemini/Claude)

1. Configura MCP nel client IA (vedi `MCP_SETUP.md`)
2. Chiedi: "Mostrami lo stato del fabric Omninode"
3. L'agente dovrebbe chiamare `get_fabric_health` e mostrare risultati

---

## 📡 API Reference

### GET /health

**Auth:** No  
**Response:**
```json
{"status": "ok", "service": "omninode-node1-gateway"}
```

### GET /nodes

**Auth:** Sì (X-Omninode-Key)  
**Response:**
```json
[
  {
    "node_id": "test-node",
    "status": "online",
    "load": 25,
    "last_seen": 1726966847,
    "metadata": {}
  }
]
```

### GET /nodes/{node_id}

**Auth:** Sì  
**Response:** Singolo nodo o 404

### POST /nodes/{node_id}/tasks

**Auth:** Sì  
**Body:**
```json
{
  "task_type": "compute",
  "payload": {"operation": "sum", "values": [1,2,3]}
}
```

**Response:**
```json
{
  "status": "dispatched",
  "task_id": "task-1726966847",
  "node_id": "test-node"
}
```

### GET /fabric/health

**Auth:** Sì  
**Response:**
```json
{
  "total_nodes": 1,
  "online_nodes": 1,
  "offline_nodes": 0,
  "average_load": 25,
  "health_status": "healthy",
  "fabric_version": "0.1.0"
}
```

---

## 🔧 Troubleshooting

### Gateway non si connette a MQTT

**Sintomo:** `WARNING: MQTT connection failed`

**Soluzione:**
1. Verifica Mosquitto in esecuzione: `Get-Service mosquitto`
2. Controlla `.env`: `MQTT_HOST=localhost`, `MQTT_PORT=1883`
3. Testa connessione: `telnet localhost 1883`

### API rifiutano richieste

**Sintomo:** `401 Unauthorized`

**Soluzione:**
1. Verifica chiave in `.env`: `OMNINODE_API_KEY=<valore>`
2. Usa stessa chiave in header: `X-Omninode-Key: <valore>`
3. Riavvia gateway dopo modifica `.env`

### Nodi risultano offline

**Sintomo:** `"status":"offline"` anche dopo heartbeat

**Soluzione:**
1. Pubblica heartbeat ogni 30-90 secondi (TTL default: 90s)
2. Verifica topic MQTT corretto: `omninode/nodes/{id}/heartbeat`
3. Controlla payload JSON valido: `{"status":"online","load":25}`

---

## 🎯 Prossimi Step Consigliati

### Priorità¹¹ Alta

1. **Implementare nodo worker reale**
   - Script Python che esegue task computazionali
   - Pubblica heartbeat e risultati su MQTT
   - Sottoscrive topic tasks

2. **Frontend Wails per OmniClient**
   - Dashboard per visualizzare nodi
   - Invio task manuali
   - Monitoraggio fabric health

3. **Persistenza dati**
   - SQLite per storico nodi e task
   - API per query storico

### Priorità²¹ Media

4. **Deploy Docker**
   - Dockerfile per gateway
   - docker-compose con Mosquitto
   - Deploy automatico su cloud

5. **Sicurezza avanzata**
   - MQTT con TLS
   - API key rotazione
   - Rate limiting

### Priorità³¹ Bassa

6. **Multi-gateway**
   - Load balancing tra gateway
   - Service discovery

7. **Monitoring**
   - Prometheus metrics
   - Grafana dashboard
   - Alerting

---

## 📞 Contatti e Risorse

- **Repository:** https://github.com/ZooL-OhKi/omninode
- **MQTT:** https://mosquitto.org/
- **MCP SDK:** https://github.com/modelcontextprotocol/go-sdk
- **Wails:** https://wails.io/
- **FastAPI:** https://fastapi.tiangolo.com/

---

## ✅ Checklist Stato Attuale

- [x] Repository GitHub configurata
- [x] Node1 Gateway implementato e testato
- [x] MQTT broker installato e operativo
- [x] OmniClient MCP server implementato
- [x] Documentazione completa (README, MCP_SETUP, HANDOVER)
- [x] CI/CD pipeline configurata
- [x] Test procedures documentate
- [ ] Nodo worker reale (solo test fittizio)
- [ ] Frontend Wails UI
- [ ] Persistenza database
- [ ] Deploy production

---

**Fine documento handover.**  
Per continuare il progetto, inizia dai "Prossimi Step Consigliati" in ordine di priorità.
