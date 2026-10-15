# Fase 17 — Oracle bootstrap e handoff per una nuova IA

Aggiornato: 2026-10-15, 09:23 CEST. Snapshot operativo, NON certificazione production.

## Come usare questo documento

Leggere questo file prima di eseguire installazioni o modifiche. Le evidenze Oracle provengono dagli output della sessione SSH eseguita dall'operatore e riportati nella conversazione; non da accesso SSH diretto dell'assistente. Rivalidare lo stato corrente. Nessuna modifica ai sorgenti applicativi e' stata effettuata durante questa sessione. Le modifiche descritte sono alla rete e all'ambiente Oracle.

## Git e tracking

- Repository: ZooL-OhKi/omninode.
- PR #3 merged via squash. Commit main verificato: 1b7b97f3e931635bd7fa7e767a0db31dcf7b12ee.
- Issue operativa: https://github.com/ZooL-OhKi/omninode/issues/4. La sua creazione NON ha avviato un esecutore.
- Branch di questo handoff: docs/phase-17-oracle-handoff, creato dal commit sopra.
- feature/phase-17-mqtt-integration-fix era soltanto proposto; non creato alla verifica dei branch.
- Non fare push diretto su main, merge automatici o deploy non approvati. Ogni IA deve verificare branch e diff correnti per evitare conflitti con altri collaboratori.

## Obiettivo e limiti

L'utente vuole OmniNode residente su Oracle Free Tier e capace di fungere da braccio esecutivo autonomo, minimizzando comandi manuali. Questa e' una destinazione progettuale, non una capacita' E2E gia' provata. Non dichiarare che OmniNode legge/esegue issue GitHub senza verificarne l'implementazione. Le precedenti dichiarazioni di readiness completa erano premature rispetto ai blocchi sotto.

## Infrastruttura

Regione OCI: eu-milan-1 (Milano).

| Nodo | IP pubblico osservato | IP privato | Stato verificato |
| --- | --- | --- | --- |
| omninode-orchestrator | 129.152.6.17 | 10.0.0.237 | SSH funzionante dopo reboot |
| omninode-archivista | 92.4.172.19 | 10.0.0.226 | Running in console; software non ispezionato |

Entrambe mostravano shape VM.Standard.E2.1.Micro, 1 OCPU e 1 GB. IP e stato vanno riconfermati. Non pubblicare credenziali. Le chiavi SSH restano sul PC dell'operatore, fuori Git; non chiedere di incollarle o caricarle. Utente SSH orchestratore: ubuntu. L'assistente non dispone di una sessione SSH remota propria: la connessione GitHub non equivale ad accesso Oracle.

## Modifica di rete realmente effettuata

SSH inizialmente in timeout. Route table associata vuota. L'operatore ha aggiunto:
- tabella: default route table for omninode-vcn;
- destinazione: 0.0.0.0/0;
- target: Internet gateway-omninode-vcn.

SSH poi funzionante. Subnet: public subnet-omninode-vcn. Nessun NSG associato nella schermata osservata. Security List osservata: ingress stateful TCP 22 da 0.0.0.0/0; egress tutti i protocolli a 0.0.0.0/0. Non aprire altre porte per aggirare problemi applicativi. Limitare successivamente SSH all'origine amministrativa verificata, senza perdere l'accesso. Non usare un vecchio IP del login come prova dell'attuale IP amministrativo.

## Stato orchestratore e installazioni

- Ubuntu 26.04.1 LTS, x86_64.
- Python 3.14.4; Git 2.53.0; Go 1.26.0 installato da apt.
- Clone shallow main in /home/ubuntu/omninode.
- Venv: /home/ubuntu/omninode/node1-gateway/venv.
- Installato python3-venv e relative dipendenze.
- Dipendenze requirements.txt installate nel venv tramite pip, preferendo solo wheel binarie. pip aggiornato a 26.2.1. pip check: No broken requirements found.
- Playwright Python 1.64.0 aggiunto LOCALMENTE nel venv: manca nel requirements.txt del commit osservato.
- Eseguito: venv/bin/python -m playwright install --with-deps --only-shell chromium. Installati headless shell v1248 e FFmpeg v1013 con dipendenze OS. Cache: /home/ubuntu/.cache/ms-playwright/.
- Nessuna unit OmniNode/Mosquitto risultava installata nei controlli iniziali; non sono state successivamente predisposte o avviate da questa sessione.
- Utente di servizio omninode, /opt/omninode, certificati broker e configurazione protetta NON predisposti da questa sessione. Non presumere che non esistano per interventi successivi: verificare.
- Non presumere che un futuro utente omninode acceda alla cache Playwright di ubuntu.

## Test Python reali

Prima raccolta: errore ModuleNotFoundError playwright. Dopo installazione libreria: 119 passed, 1 failed per headless shell assente. Dopo installazione browser:

```text
120 passed, 4 warnings in 30.03s
Exit code: 0
```

Report sul server: /home/ubuntu/omninode-readiness/20261015T065742Z (pytest.log, python-packages.txt, commit.txt). I log completi non sono stati caricati in Git. git status --short vuoto dopo i test. Segreto MCP effimero generato solo nell'ambiente del processo, non stampato ne' salvato.

Warning: deprecazione Starlette TestClient/httpx; chiave OMNINODE_AUDIT_SIGNING_KEY non definita e sostituita da chiave effimera in RAM per test/sviluppo. La chiave audit production deve essere persistente e conservata fuori Git; verificare formato richiesto nel codice prima di generarla.

pip freeze completo e' nei report locali; non equiparare dipendenze importabili a piena compatibilita' production. I test verdi non dimostrano mTLS, ACL e circuito live funzionanti.

## Go: risultati e incidente risorse

Richiesto da go.mod: go 1.26.0.
- go mod download: exit 0.
- go mod verify: all modules verified, exit 0.
- go vet e go test: NON completati. Non riportarli PASS.

Tentativo con GOMAXPROCS=1, GOMEMLIMIT=400MiB, go vet -p 1 ./... ha coinciso con unattended-upgrades e grave congestione della VM da 1 GB senza swap: compilatore circa 320 MB RSS, processi D, vmstat wa fino a 95%, PSI io full avg10 circa 90%, memoria disponibile circa 124-135 MiB. GOMEMLIMIT e' morbido, non un limite RSS globale.

Ctrl+C non ha subito terminato il compilatore. Inviato SIGTERM mirato verificando nome/PID; Go e compile poi scomparsi. NON riutilizzare quei PID. Successivamente b=0, wa=0, circa 504 MiB disponibili. Non dimostrato guasto disco: estratto dmesg mostrava avvisi storici, non nuovi errori storage.

Non ripetere build pesanti sulla micro. Preferire build/test esterni o CI verificando compatibilita' del binario. Non disabilitare aggiornamenti o aggiungere swap come correzione automatica senza valutazione.

## Riavvio gia' completato

Prima del reboot: dpkg --audit vuoto; apt-daily e apt-daily-upgrade inactive; nessun holder sui lock controllati. Riavvio ordinato effettuato. Dopo riconnessione:
- uname -r: 7.0.0-1010-oracle;
- systemctl --failed: 0 loaded units listed;
- 675 MiB disponibili; swap assente;
- git status --short vuoto.

Banner post-reboot: ancora 52 aggiornamenti disponibili, 38 standard security. Non dichiarare OS completamente aggiornato.

## Blocchi applicativi accertati

### Gateway Python

main.py usa aiomqtt.Client con hostname e port senza contesto TLS/certificato client nei tre percorsi letti. Default broker oracle-b.plini.net:8883. Richiede MCP_SECRET da os.environ. Topic hardcoded legacy omninode/nodes/... (heartbeat, result, cmd) e approval su topic separati. Listener MQTT in background senza ciclo di riconnessione mostrato. HTTP avviato non implica MQTT pronto. Avvio diretto main.py lega 0.0.0.0:8000.

mqtt_topics.py supporta legacy (default) e v1 via OMNINODE_MQTT_TOPIC_VERSION; v1 definisce tasks/responses/heartbeat sotto omninode/v1/nodes/{id}. main.py non usa il builder nei percorsi letti. mqtt_service.py importa il builder ma contiene topic legacy. Verificare collegamenti reali prima di scegliere entrypoint.

autonomy_app.py importa main.app e aggiunge build_router(verify_mcp_auth). Entry point documentato: uvicorn autonomy_app:app. autonomy_api offre run-step/goals per target_file, workspace list/read/rollback, command/verify a preset, pending-prompt/submit-dom-response. Non e' prova di provisioning Oracle o consumer GitHub issue. Ispezionare work_loop.py e autonomy_core.py per limiti reali.

mqtt_task_protocol.py valida schema_version=1, UUID task_id/goal_id, agent_id/node_id/task_type/capability, destinatario locale, deadline futura e task_type/capability workspace.write. Riutilizzare protocolli, envelope e policy esistenti; non sostituire con shell arbitraria.

### Worker Go

main.go legge variabili OMNINODE_MQTT_BROKER (default tcp://127.0.0.1:1883), OMNINODE_NODE_ID (default omni-worker-go-1), OMNINODE_MQTT_USER/PASS/CA_PATH; chiama StartMQTTWorker e poi attende segnali. Non legge i flag del servizio mostrato.

mqtt_client.go configura CA ma non carica certificato/chiave client; errori lettura CA solo loggati e ritorno AppendCertsFromPEM non controllato. StartMQTTWorker nel codice letto si limita a creare/connettere il client, senza sottoscrivere task. publishRes usa topic v1 ma concatena stringhe per JSON. Correggere con serializzazione strutturata.

startHeartbeatLoop esiste in heartbeat.go ma non e' chiamato dal main.go mostrato. Topic heartbeat legacy anche nel sottopacchetto mqttclient. Non dichiarare ricezione/esecuzione task operativa senza percorso verificato.

ops_terraform.go ha TerraformWorkDir Windows hardcoded C:\omninode\iac, DB globale da InitDB, handler con HITL apply/destroy. Collegamento al main non dimostrato. Non attivare comandi distruttivi per completare il bootstrap.

### Broker e ACL

mosquitto.conf prevede MQTT 8883 e WSS 8443, require_certificate true, use_identity_as_username true, tls_version tlsv1.3, file password/ACL/CA/cert/key sotto /etc/mosquitto. Non ancora installato/configurato da questa sessione. Verificare semantica effettiva TLS e autenticazione nella versione Mosquitto: non equiparare la sola direttiva a prova di TLS esclusivamente 1.3.

ACL: identita' gateway, worker-1, worker-2; namespace v1. Gateway write tasks/control, read responses/heartbeat/control/ack. Ogni worker accesso soltanto ai propri topic. Non allargare ACL per coprire mismatch legacy.

### Servizi systemd attuali

Gateway: User=omninode, WorkingDirectory=/opt/omninode/node1-gateway, ExecStart=.../venv/bin/python main.py. Non entrypoint autonomia.
Worker: User=omninode, WorkingDirectory=/opt/omninode/omniclient, ExecStart=.../omniclient --node-id=node2 --broker=wss://localhost:9001. Flag non letti dal main osservato; identita' node2 e porta 9001 non coerenti con worker-1/worker-2 e 8443.

## Piano per riprendere da zero

1. Verificare branch/head correnti, issue #4 e questo snapshot; leggere sorgenti e test reali, non fidarsi delle vecchie dichiarazioni di certificazione.
2. Ispezionare mqtt_service/topics/task_protocol/envelope/control, autonomy_core/work_loop/API, handler e test Go, workflow CI.
3. Preparare patch su branch separato: mTLS fail-closed su tutti i client con verifica hostname e cert client, nessun fallback plaintext; topic e contratti v1 uniformi; subscription/heartbeat/risposta effettivi; reconnect con risottoscrizioni e readiness MQTT distinta da HTTP; policy/lease/idempotenza verificati.
4. Sistemare dipendenze Python riproducibili (Playwright incluso dove serve), serializzazione JSON e unit systemd/config protetta. API inizialmente localhost, utente non root. Nessun segreto in Git e nessuna sovrascrittura automatica di chiavi.
5. Verificare Python, Go vet/test in ambiente adatto e integrazione broker reale: certificato valido, assente/non fidato rifiutato, hostname errato rifiutato, ACL cross-talk negato, dispatch/risposta e reconnect. Non sostituire prove live con mock.
6. Bootstrap idempotente, backup/rollback e chiavi audit persistenti fuori repo. Verificare anche archivista prima di assegnargli ruoli.
7. Separare eventuale implementazione del consumer GitHub/autonomia estesa: non esiste evidenza sufficiente per delegargli automaticamente la issue.
8. Pubblicare diff, test, limiti, commit e PR; aggiornare issue #4 con evidenze. Merge e rollout solo dopo approvazione.

## Regole per il prossimo agente

Non affermare azioni eseguite senza esito dello strumento. Distinguere proposto/preparato/testato/installato/operativo. Non chiedere chiavi private. Non fare merge o push diretto su main. Non indebolire TLS/ACL, non usare shell arbitraria, non ripetere build saturanti. Minimizzare interventi manuali ma dichiarare chiaramente quando manca accesso esecutivo. Questo documento aggiunge solo conoscenza operativa: NON contiene la correzione del codice e NON rende OmniNode production-ready.
