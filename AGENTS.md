# AGENTS.md — OmniNode AI Handoff

Questo documento permette a un agente AI di riprendere il progetto OmniNode da zero, capire lo stato attuale, rispettare le invarianti di sicurezza e continuare lo sviluppo senza decisioni distruttive.

## Mission

OmniNode è un sistema distribuito con:

- Gateway/orchestrator Python (FastAPI) su `node1-gateway/`.
- Worker Go su `omniclient/`.
- Comunicazione MQTT mutual TLS (mTLS) esclusivamente su TLS 1.3.
- Contratto MQTT v1 sotto `omninode/v1/nodes/{node_id}/...`.
- Workspace sandboxed per il worker.
- Servizi systemd.
- Bootstrap Oracle idempotente e fail-safe.

## Stato attuale

- `main` include la Phase 17 tramite PR #6, merge squash commit `7a6e745520d9739e1b99be6871f56db9476d1559`.
- Gateway Python: mTLS obbligatorio, topic v1, reconnect, MQTT readiness separata da HTTP, HTTP su `127.0.0.1:8000`.
- Worker Go: mTLS TLS 1.3, sottoscrizione task/control, heartbeat, risposte JSON strutturate, reconnect/resubscribe, executor `workspace.write` sandboxed e idempotente.
- Mosquitto: TLS 1.3, `require_certificate true`, `use_identity_as_username true`, ACL identity-based.
- Bootstrap: `scripts/oracle_bootstrap.py`, dry-run di default, `--apply` esplicito, backup/rollback, nessuna modifica firewall, nessuna attivazione automatica dei servizi.
- Test Python: 122 passed, 0 failed.
- Test Go: 18 passed, 0 failed.
- `go vet ./...`: pulito.
- Build Linux amd64: riuscita, binario `omniclient` 18 MB.
- Test hostname mismatch: presente e PASS (`omniclient/tls_hostname_test.go`).

## Invarianti di sicurezza — NON VIOLARE

1. mTLS è obbligatorio per MQTT.
2. TLS 1.3 only sul worker Go.
3. Nessun fallback plaintext MQTT.
4. `InsecureSkipVerify` deve restare `false`.
5. Nessun segreto, password, token o chiave privata nel repository.
6. Nessuna esecuzione shell arbitraria nel worker.
7. Il worker scrive solo dentro `OMNINODE_WORKSPACE_ROOT`.
8. Le ACL Mosquitto restano identity-based e restrittive.
9. Il gateway HTTP resta su `127.0.0.1` finché non esiste una decisione esplicita di esposizione sicura.
10. Il bootstrap non modifica firewall e non attiva servizi senza `--apply` e `--enable-services`.
11. Nessun merge, deploy, rollout o modifica firewall senza approvazione umana esplicita.

## Struttura rilevante

- `node1-gateway/main.py`: gateway FastAPI e bridge MQTT.
- `node1-gateway/mqtt_service.py`: servizio MQTT thread-safe mTLS.
- `node1-gateway/mqtt_topics.py`: contratto topic v1.
- `node1-gateway/audit_api.py`, `audit_transparency.py`: audit.
- `omniclient/main.go`: entrypoint worker.
- `omniclient/mqtt_client.go`: client mTLS, task/control handling.
- `omniclient/workspace_handler.go`: executor sandboxed.
- `omniclient/tls_hostname_test.go`: negative test hostname mismatch.
- `deploy/mosquitto/`: configurazione broker e ACL.
- `deploy/systemd/`: unit systemd.
- `scripts/oracle_bootstrap.py`: bootstrap idempotente.

## Comandi di sviluppo

### Python gateway

```bash
cd node1-gateway
source venv/bin/activate
pytest
```

Se il virtualenv non esiste:

```bash
cd node1-gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

### Go worker

```bash
cd omniclient
go vet ./...
go test -count=1 ./...
```

Su istanze con poca RAM, usare:

```bash
GOMAXPROCS=1 go test -v -p 1 -timeout 300s ./...
```

### Build Linux amd64

```bash
cd omniclient
GOOS=linux GOARCH=amd64 go build -o omniclient .
```

## Bootstrap Oracle

Il bootstrap è sicuro di default:

```bash
python3 scripts/oracle_bootstrap.py
```

Applicare modifiche:

```bash
python3 scripts/oracle_bootstrap.py --apply
```

Abilitare e avviare servizi solo dopo approvazione esplicita:

```bash
python3 scripts/oracle_bootstrap.py --apply --enable-services
```

Prerequisiti fuori da Git:

- `/etc/omninode/certs/ca.crt`
- `/etc/omninode/certs/gateway.crt`
- `/etc/omninode/certs/gateway.key`
- `/etc/omninode/certs/worker-1.crt`
- `/etc/omninode/certs/worker-1.key`
- `/etc/omninode/omninode-gateway.env`
- `/etc/omninode/omninode-worker.env`

## Ambiente di test

`node1-gateway/conftest.py` imposta variabili fittizie solo per pytest. Non usarle in produzione.

## Prossimi lavori consigliati

1. CI GitHub Actions per `pytest`, `go vet`, `go test` e build Linux amd64.
2. Scansione segreti automatica sulla PR.
3. Test di integrazione mTLS end-to-end con broker effimero.
4. Persistenza idempotenza worker con write atomico o registro append-only.
5. Metriche Prometheus per gateway, worker e broker.
6. Rotazione e revoca certificati.
7. Hardening systemd: `ProtectSystem`, `ProtectHome`, `NoNewPrivileges`, `PrivateTmp`, dove compatibili.
8. Decisione esplicita e documentata su esposizione della porta WSS 8443.
9. Runbook operativo per incident response e rotazione certificati.
10. Rimozione eventuale della password MQTT se l’identità certificato è sufficiente.

## Regole operative per l’agente

- Leggere prima il codice esistente; non presupporre interfacce non presenti.
- Non fare merge, deploy, rollout, modifiche firewall o rotazioni certificati senza approvazione umana.
- Non inserire segreti nei file, nei test o nei log.
- Non indebolire TLS, ACL, sandbox o validazione certificati.
- Eseguire sempre test Python e Go prima di proporre un merge.
- Documentare ogni modifica con commit chiari e PR descrittive.
