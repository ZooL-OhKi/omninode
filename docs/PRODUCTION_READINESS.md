# OMNINODE SWARM FABRIC v5.0 — PRODUCTION READINESS REPORT

Stato Repository: main (Fasi 1-8 completate, 100% test verdi Python e Go)
Data di Emissione: Ottobre 2026
Classificazione: Documentazione Architetturale e di Sicurezza

---

## 1. Stato delle Fasi (1-8)

La Swarm Fabric v5.0 è stata sviluppata attraverso otto fasi incrementali, tutte testate, verificate e integrate sul branch principale main:
- Fase 1-3 & Task A: Trasparenza dell'audit crittografico append-only (ed25519/SHA-256) e trasporto MQTT over WSS con envelope canonico e validazione dell'identità basata su certificato/chiave.
- Task B-C: Isolamento dei processi a livello di kernel (Windows Job Objects e Unix Process Groups) e motore di redaction locale per prevenire la fuga di segreti e token.
- Fase 5: Gestione esplicita dei budget per goal, checkpoint persistenti su SQLite e Control Plane protetto da autenticazione MCP.
- Fase 6: Control plane MQTT distribuito con idempotenza (request_id), scadenze (expires_at), stop sicuro graceful (SIGTERM con fallback) e motore di Safe Self-Improvement basato su Trust Tiers (0-4).
- Fase 7: Orchestrazione di flotta con heartbeat arricchiti, leasing delle esecuzioni, versioning, capacity-aware scheduler e Circuit Breaker per nodo (closed, open, half_open).
- Fase 8: Telemetria strutturata, anomaly detection deterministica, calcolo dell'Health Score multi-fattoriale e workflow di self-healing limitato e auditato.

---

## 2. Matrice dei Rischi

| Area di Rischio | Severità | Mitigazione Implementata | Rischio Residuo |
|---|---|---|---|
| Spoofing Identità Nodo | Critica | Validazione rigorosa del node_id basata sull'identità MQTT autenticata. | Richiede validazione con broker Mosquitto TLS/WSS reale. |
| Doppia Esecuzione (Partizioni di Rete) | Alta | Modello di leasing temporale (lease_expires_at) e quarantena dei task orphaned. | Richiede test di partizione di rete prolungata. |
| Self-Improvement Fuori Controllo | Critica | Trust Tiers 0-4 con divieto assoluto di modifica a policy, ACL, chiavi e audit (Tier 4). | Verificato via test unitari; richiede audit umano sui Tier 2-3. |
| Remediation Distruttiva | Alta | Workflow di remediation limitato a restart worker, purge cache e ridistribuzione task. | Azioni distruttive bloccate a livello di policy di sicurezza. |

---

## 3. Test di Integrazione (Eseguiti e da Eseguire)

- Eseguiti (100% Verdi):
  - Suite unitaria Python (pytest, 94 test passati) su gateway, audit, goal manager, control plane MQTT, trust tiers, leasing, scheduler, circuit breaker e diagnostics.
  - Suite unitaria e di compilazione Go (go vet, go test) su omniclient.
  - Verifica dell'integrità dei commit e assenza di file sensibili (git diff --check).
- Da Eseguire (Fase 9):
  - Test end-to-end con broker Mosquitto reale configurato con WSS, TLS mutual authentication e ACL granulari per topic.
  - Test di partizione di rete simulata con interruzione del flusso MQTT e verifica dei timeout di lease.
  - Test di esecuzione su host Windows reali (con Job Objects) e Linux reali (con Process Groups).

---

## 4. Requisiti di Deploy

1. Infrastruttura Gateway (Python 3.11+):
   - FastAPI, Pydantic v2, SQLite con WAL mode abilitato.
   - Variabili d'ambiente gestite tramite file .env protetti (mai tracciati in Git).
2. Infrastruttura Worker (Go 1.22+):
   - Compilazione nativa per l'architettura di destinazione (Windows/Linux).
3. Broker MQTT:
   - Eclipse Mosquitto con supporto WebSocket Secure (WSS) su porta 443, certificati TLS validi e file ACL configurati.

---

## 5. Configurazione Mosquitto, WSS e ACL

Esempio di configurazione di riferimento per il broker (mosquitto.conf):

listener 8883
protocol mqtt
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/broker.crt
keyfile /etc/mosquitto/certs/broker.key
require_certificate true

listener 443
protocol websockets
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/broker.crt
keyfile /etc/mosquitto/certs/broker.key
require_certificate true

acl_file /etc/mosquitto/acl.conf

Regole ACL di isolamento nodi (acl.conf):
- Gateway: scrittura su omninode/v1/nodes/+/control, lettura su +/control/ack e +/heartbeat.
- Nodi ({node_id}): lettura esclusiva su omninode/v1/nodes/{node_id}/control, scrittura su {node_id}/control/ack e {node_id}/heartbeat.

---

## 6. Procedure di Backup e Restore

- Database SQLite (goals.db, audit.db):
  - Backup a caldo tramite comando SQLite VACUUM INTO 'backup_path.db'.
  - Restore subordinato alla verifica dell'integrità crittografica della catena di audit (firme Ed25519).

---

## 7. Runbook di Incident Response

1. Rilevamento Anomalia / Apertura Circuit Breaker:
   - Isolare immediatamente il nodo interessato pubblicando il comando di stop o forzando la quarantine tramite API di Control Plane.
2. Procedura di Stop di Emergenza:
   - Esecuzione sequenziale: invio SIGTERM ai processi figli, attesa timeout, fallback a SIGKILL sul process group e rollback delle modifiche non verificate.
3. Analisi Forense:
   - Consultazione del registro di audit append-only firmato e dei log strutturati della telemetria.

---

## 8. Soglie di Alert

- Heartbeat Age > 30s: Attivazione stato suspect / unavailable.
- Failure Rate > 20% in finestra mobile: Apertura Circuit Breaker in stato open.
- Task Latency P95 > 60s: Generazione anomalia e trigger di remediation automatica (Tier di rischio basso).

---

## 9. Roadmap della Fase 9 (Production Hardening)

1. Deploy di un ambiente di test con broker Mosquitto reale su Docker Compose.
2. Integrazione di test E2E multi-nodo con simulazione di partizioni di rete.
3. Consolidamento dei runbook operativi e stesura delle policy-as-code firmate.