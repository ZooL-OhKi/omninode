# OmniNode

Sistema distribuito per l’automazione browser e operazioni infrastrutturali tramite MCP (Model Context Protocol).

## Panoramica

OmniNode è un’architettura client-gateway che espone capacità di automazione browser (CDP) e operazioni infrastrutturali (Terraform) attraverso un server MCP locale. Il sistema è composto da due componenti principali:

- **omniclient (Go)**: Server MCP locale che esegue su macchina client, espone tool `browser_*` e `ops_*`, gestisce Chrome DevTools Protocol (CDP) locale e comunica con il gateway.
- **node1-gateway (Python/FastAPI)**: Gateway centrale che gestisce MQTT, task store, policy engine, audit logging e browser runtime remoto.

## Stato operativo

Il deployment live utilizza MQTT mutual TLS su TLS 1.3. Il gateway HTTP è vincolato a `127.0.0.1:8000`; non esporlo pubblicamente senza una decisione di sicurezza esplicita.

I worker si registrano tramite heartbeat MQTT. `worker-2` è attualmente registrato come nodo online con agente `archivista`.

La registrazione nel gateway non equivale all’esecuzione verificata di un task. Per lo stato dettagliato e i test residui, vedere [docs/WORKER2_HANDOVER.md](docs/WORKER2_HANDOVER.md).

## Architettura

```text
Worker Go / MCP
  -> MQTT mTLS (TLS 1.3)
    -> Mosquitto
      -> Gateway FastAPI
        -> API flotta / task / audit
```

## Componenti

### omniclient (Go)

- **mcp_server.go**: Server MCP che espone tool `browser_navigate`, `browser_click`, `browser_type`, `browser_screenshot`, `ops_terraform_plan`, `ops_terraform_apply`.
- **cdp_agent.go**: Agente Chrome DevTools Protocol per automazione browser locale.
- **web_agent.go**: Agente per navigazione e scraping web.
- **ops_terraform.go**: Esecutore comandi Terraform per operazioni infrastrutturali.
- **gateway_client.go**: Client HTTP/gRPC verso il gateway.
- **mqtt_client.go**: Client MQTT mTLS per pub/sub asincrono.
- **ws_server.go**: Server WebSocket per connessioni bidirezionali.
- **heartbeat.go**: Health check periodici verso il gateway.

### node1-gateway (Python)

- **main.py**: Applicazione FastAPI con endpoint REST e WebSocket.
- **mqtt_service.py**: Servizio MQTT per messaggistica asincrona task/results.
- **task_store.py**: Store in-memory per task in esecuzione.
- **policy_engine.py**: Motore policy per autorizzazioni e limiti.
- **browser_runtime.py**: Runtime browser remoto con gestione sessioni.
- **audit.py**: Audit logging per tracciabilità operazioni.
- **workspace_manager.py**: Gestione workspace e contesti multi-tenant.

## Requisiti

- Go 1.22+
- Python 3.11+
- Broker MQTT con mTLS, ad esempio Mosquitto
- Certificati CA, gateway e worker fuori dalla repository
- Chrome/Chromium con debug remoto, solo quando si usano capacità browser
- Terraform CLI, solo per capacità `ops_*`

## Build

```bash
cd omniclient
go mod download
go build -o omniclient .
```

```bash
cd node1-gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configurazione

Il deployment live usa mTLS. Non configurare MQTT plaintext su porta 1883 in produzione.

Variabili tipiche del worker:

```text
OMNINODE_NODE_ID=worker-2
OMNINODE_MQTT_BROKER=<broker-host>:8883
OMNINODE_MQTT_CA=/etc/omninode/certs/ca.crt
OMNINODE_MQTT_CERT=/etc/omninode/certs/worker-2.crt
OMNINODE_MQTT_KEY=/etc/omninode/certs/worker-2.key
OMNINODE_WORKSPACE_ROOT=/var/lib/omninode/workspaces/worker-2
```

Non committare file `.env`, certificati o chiavi private.

## Avvio

In produzione usare systemd:

```bash
sudo systemctl start omninode-gateway.service
sudo systemctl start mosquitto
sudo systemctl start omninode-worker.service
```

Per sviluppo locale, consultare `BUILD.md` e i test esistenti prima di usare comandi manuali.

## Verifica flotta

Sull’orchestratore:

```bash
curl --connect-timeout 3 --max-time 10 \
  -sS http://127.0.0.1:8000/api/v1/nodes
```

Un nodo registrato deve avere `status: "online"` e un timestamp recente.

## Test

```bash
cd node1-gateway
source venv/bin/activate
pytest
```

```bash
cd omniclient
go vet ./...
go test -count=1 ./...
```

## Documentazione

- [ARCHITECTURE.md](ARCHITECTURE.md) — Topologia dettagliata, flussi, contratti
- [SECURITY.md](SECURITY.md) — Principi sicurezza, hardening, incident response
- [BUILD.md](BUILD.md) — Istruzioni build, test, configurazione
- [NEXT_STEPS.md](NEXT_STEPS.md) — Priorità e checklist sviluppo
- [ROADMAP.md](ROADMAP.md) — Stato implementazione e backlog
- [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md) — Onboarding per AI assistant
- [docs/WORKER2_HANDOVER.md](docs/WORKER2_HANDOVER.md) — Handover live worker-2
- [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md) — Runbook operativo
- [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) — Mappa repository
- [omniclient/README.md](omniclient/README.md) — Setup worker Go
- [omniclient/MCP_SETUP.md](omniclient/MCP_SETUP.md) — Config MCP per Claude Desktop

## License

MIT
