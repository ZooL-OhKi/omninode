# OmniNode v5.0 — Live Pilot Certification Guide (Fase 16)

## 1. Stato delle Fasi 1-15
- **Fasi 1-4:** Transport MQTT over WSS con envelope canonico, audit chain append-only protetta da firme Ed25519 e hashing SHA-256, isolamento a livello kernel e motore di redaction locale.
- **Fasi 5-8:** Control Plane distribuito, budget per goal, persistenza SQLite e orchestratore di flotta con Circuit Breaker per nodo.
- **Fasi 9-11:** Code persistenti, risoluzione DAG delle dipendenze, Trust Tiers (0-4), tool MCP autenticati, webhook HMAC, Secure Browser Executor (CDP) e coordinatore multi-AI.
- **Fasi 12-15:** Autonomous Phase Driver, Patch Evaluator (con blocco rigoroso dei file protetti come policy/**, acl/**, keys/**, .env), Fleet Dashboard, Operations Runbook, servizi systemd 24/7, rilevamento cicli DAG e Workloop Driver end-to-end.

## 2. Architettura Finale
Swarm Fabric decentralizzata basata su un gateway di controllo in Python (node1-gateway) e client di flotta in Go (omniclient). L'orchestrazione è guidata da goal contrattuali eseguiti autonomamente da worker cognitivi (Gemini/Perplexity) tramite browser isolati, con validazione di patch, test reali, generazione automatica di PR e audit crittografico trasparente.

## 3. Requisiti Oracle Free
- Due istanze cloud Oracle Free Tier (Ubuntu 22.04 LTS o Oracle Linux 9).
- Utente di servizio dedicato non privilegiato: omninode.
- Directory di installazione standard: /opt/omninode.
- Directory di lavoro isolate e permessi ristretti sui file di configurazione.

## 4. Configurazione Systemd
Servizi residenti con avvio automatico al boot, restart policy in caso di crash (Restart=always, RestartSec=5) e logging strutturato su systemd journald:
- deploy/systemd/omninode-gateway.service
- deploy/systemd/omninode-worker.service
- deploy/systemd/omninode-browser.service

## 5. Configurazione Mosquitto TLS/WSS e ACL
Broker MQTT centralizzato configurato per accettare connessioni sicure crittografate (TLS 1.3) su WebSockets protetti (WSS):

### Configurazione mosquitto.conf (Estratto):
    listener 8883
    protocol mqtt

    listener 9001
    protocol websockets
    certfile /etc/mosquitto/certs/server.crt
    keyfile /etc/mosquitto/certs/server.key
    require_certificate true

    acl_file /etc/mosquitto/acl.conf

### Regole ACL (acl.conf):
    # Gateway Controller
    user omninode-gateway
    topic write omninode/fleet/#
    topic read omninode/workers/#

    # Fleet Workers (Go clients)
    user omninode-worker-node2
    topic read omninode/fleet/node2/#
    topic write omninode/workers/node2/#

## 6. Scenari di Test End-to-End
1. **Goal E2E Standard:** Inserimento di un goal Tier 1, risoluzione DAG, assegnazione workspace, dispatch browser, generazione patch, esecuzione test e apertura automatica di PR.
2. **Rilevamento Cicli DAG:** Iniezione di dipendenze circolari; il sistema deve intercettare il ciclo, bloccare immediatamente il goal, registrare l'anomalia nell'audit log ed evitare qualsiasi esecuzione.
3. **Protezione File Sensibili:** Tentativo di modifica di file in policy/** o .env; il Patch Evaluator deve rifiutare la patch indipendentemente dal Trust Tier.

## 7. Soglie di Alert
- **Tasso di Fallimento Task:** > 20% di fallimenti in una finestra mobile di 5 minuti attiva il blocco temporaneo del nodo tramite Circuit Breaker.
- **Disconnessioni MQTT:** Più di 3 riconnessioni consecutive in 60 secondi generano un allarme di rete registrato su journald.
- **Utilizzo Risorse:** CPU > 90% o RAM > 85% sull'istanza Oracle Free Tier attiva il throttling dei task concorrenti.

## 8. Procedure di Incident Response
1. **Isolamento del Nodo:** Revoca immediata del token MCP e del certificato MQTT del nodo compromesso tramite il pannello di controllo della flotta.
2. **Verifica Audit Chain:** Ispezione della catena crittografica Ed25519/SHA-256 per rilevare eventuali manomissioni dei registri di transazione.
3. **Rollback:** Ripristino dello stato sicuro precedente utilizzando i backup SQLite validati.

## 9. Backup e Restore
- **Backup Schedulato:** Cron job giornaliero per l'esportazione sicura dei database SQLite (goals_queue.db, audit_chain.db) verso un bucket Object Storage cifrato.
- **Restore Protocol:** Interruzione dei servizi systemd, ripristino dei file di database, verifica dell'integrità della firma crittografica e riavvio dei demoni.

## 10. Criteri di Passaggio da Pilot a Produzione
- Superamento di almeno 72 ore consecutive di esecuzione autonoma continua senza interventi correttivi non pianificati.
- Conformità al 100% dei test di integrazione e della suite unitaria (Python e Go).
- Validazione formale dell'approvazione umana obbligatoria per ogni singola Pull Request e merge su main.
