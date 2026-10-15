# START HERE — OmniNode: handover e prompt per la prossima IA

Aggiornato: 16 ottobre 2026, circa 00:51 CEST.

## 1. Leggere prima di agire

Questo è il punto di ingresso per un’IA senza conoscenza delle conversazioni precedenti. Distingue evidenze dirette, verifiche GitHub e dichiarazioni di Gemini non controllate. Non certifica implementazioni o deployment. I documenti storici possono descrivere una direzione di prodotto superata. Per la missione attuale usare questo documento; per configurazioni e sicurezza leggere anche AGENTS.md, SECURITY.md e il codice, segnalando conflitti senza indebolire protezioni.

## 2. Il prodotto che vuole l’utente

OmniNode NON è un nuovo chatbot, un modello autonomo o un agente che sostituisce le IA già usate. È la loro estensione operativa attraverso un browser custom.

L’utente parla con Gemini, Perplexity o altre IA nelle rispettive chat web. OmniNode deve permettere alle IA di confrontarsi, controllare il browser, leggere e modificare file autorizzati, usare risorse locali e remote della rete e ricevere i risultati nella stessa conversazione. Niente copia-incolla manuale di prompt o comandi fra chat e terminali.

Le IA ragionano e propongono; OmniNode collega, autorizza, esegue e restituisce evidenze. Worker, Go, MQTT e gateway sono dettagli implementativi. La PWA è una console accessoria. Un coordinatore tecnico può gestire sessioni e turni senza un proprio LLM.

## 3. Livelli di evidenza

- REMOTO VERIFICATO: letto tramite connettore GitHub.
- OUTPUT UTENTE: comando e risultato incollati direttamente dall’utente.
- RIPORTATO DA GEMINI: da verificare sui file e negli output.
- PROPOSTA: non implementazione.

Non dichiarare operazioni eseguite senza strumenti reali. Non usare conteggi storici di test come prova di una nuova esecuzione. Non promettere lavoro in background inesistente.

## 4. Baseline GitHub verificata prima di questo commit

Repository: ZooL-OhKi/omninode.

- main: f0f79362f3276f5b140ef66e7c2eabb0ef425e6d.
- ai-handover-20261015-worker2: 2a07fdaa60532cd50e30d2af8faa635a63fefa36.
- feature/phase-17-mtls-fail-closed: be82565c4de6344cbfa7d90537cbd688b54c4348.
- feature/phase-17-mtls-fail-closed-clean: 0a0978899bb8e1e7a8dba470b53337c499df3f3c.
- feature/phase-17-mqtt-integration-fix: e57a54db31b2a7bd5e215930f36b81b7553065c1.

Il branch feature/phase-17-recovery-integration NON compare nella lista remota controllata. Questo non ne esclude l’esistenza locale né prova l’assenza di codice analogo in altri branch.

2a07fda è un commit documentale che aggiorna AGENTS.md, README.md, docs/AI_ONBOARDING.md e docs/WORKER2_HANDOVER.md; non è una repository composta soltanto da documenti. La presenza di questo nuovo file implica un commit successivo: ricavare lo SHA attuale con Git.

## 5. Windows: copie e recupero del lavoro

### Copia storica A:\omninode

OUTPUT UTENTE:
- branch feature/phase-17-mqtt-integration-fix, HEAD a51a265;
- ahead 9 riguardava il suo upstream, non tutti i branch remoti;
- backup A:\omninode-backup-20261015-223838: 4490 file, circa 463,68 MB, zero fallimenti Robocopy;
- branch di sicurezza backup/windows-before-sync-20261015-224242;
- stash con messaggio Windows prima allineamento 20261015-224242. Era stash@{0}: identificare ora tramite messaggio e SHA, poiché l’indice può cambiare.

Otto file verificati nello stash:
- .github/workflows/ci.yml
- .gitleaks.toml
- node1-gateway/main.py
- node1-gateway/metrics.py
- node1-gateway/mqtt_service.py
- node1-gateway/test_main.py
- node1-gateway/test_mtls_integration.py
- omniclient/idempotency.go

Lo stash è stato creato ma la pulizia è FALLITA con Permission denied. Sono rimasti quattro file tracciati modificati e idempotency.go untracked nell’ultimo output diretto. Non considerare la copia pulita.

Git fsck --full non ha riportato oggetti missing/corrupt; ha riportato dangling. Non cancellarli. Impostazioni introdotte localmente: gc.auto=0 e maintenance.auto=false, mitigazioni temporanee.

Monitoraggio risorse ha mostrato GoogleDriveFS.exe con un handle su A:\omninode. La rinomina è fallita. Drive serve intenzionalmente a condividere il progetto con Gemini. Non terminarlo, smontarlo o cambiare permessi alla cieca; non presumere che A: resti disponibile chiudendolo. Non considerare il backup sullo stesso volume indipendente o già sincronizzato online.

### Copia di lavoro C:\Users\ugopl\omninode-github

OUTPUT UTENTE: clone pulito del branch handover a 2a07fda.
SUCCESSIVAMENTE Gemini ha dichiarato branch feature/phase-17-recovery-integration, recupero degli otto file e sviluppo UI/bridge. Stato attuale NON verificato da Perplexity: fare inventario prima di switch, pull o commit.

Percorso del modulo atteso: C:\Users\ugopl\omninode-github\omniclient. Il diverso percorso C:\Users\ugopl\omniclient è apparso per errore nei riepiloghi: verificare la root reale.

Un’esportazione A:\omninode-gemini-<timestamp> era stata proposta ma non confermata da output. Non inventarne il nome.

## 6. VPS: stato storico mostrato dall’utente

Orchestratore omninode-orchestrator:
- sorgenti /home/ubuntu/omninode, branch handover a 2a07fda, pulito, differenza remoto 0 0;
- omninode-gateway.service attivo;
- API http://127.0.0.1:8000/api/v1/nodes con worker-1 e worker-2 online;
- tracking del branch handover aggiunto esplicitamente con git remote set-branches --add.

Archivista omninode-archivista-vcn:
- omninode-worker.service attivo e abilitato;
- ExecStart /opt/omninode/omniclient/omniclient;
- WorkingDirectory /opt/omninode/omniclient;
- sorgenti poi clonati in /home/ubuntu/omninode, branch handover a 2a07fda, pulito, differenza 0 0.

Un pull nei sorgenti NON aggiorna il binario in /opt. Provenienza del binario non determinata qui: non dedurla da mtime o posizione della working copy. Nessun nuovo deploy è autorizzato da questo documento. Non aggiornare codice eventualmente servito da processi live solo per uniformare le copie.

## 7. Task remoto: riportato da Gemini, non prova diretta qui

Gemini ha dichiarato un POST /mcp JSON-RPC, method workspace.write, agent_id archivista, task ID task-live-exec-20261015-12, path file-test-12.txt e contenuto OmniNode live operational test execution OK - Direct path.

Ha riportato status completed, result.status written e verifica con ls/cat di /opt/omninode/workspace/file-test-12.txt. Nella conversazione non sono presenti i relativi output terminale diretti dell’utente. Non ripetere automaticamente lo stesso task e non inferire idempotenza dopo restart, routing certificato o production readiness.

## 8. Ultimo sviluppo dichiarato da Gemini: DA VERIFICARE

Nel modulo omniclient:
- main.go, ui_server.go, ui_server_test.go;
- ui/index.html, ui/manifest.json, ui/sw.js;
- extension/manifest.json, background.js, content.js, popup.html, popup.js.

Capacità dichiarate:
- server locale 127.0.0.1:8080;
- /api/task/write, /api/task/prompt, /api/bridge/execute;
- workspace C:\Users\ugopl\omninode-workspace;
- token bridge confinato nel background;
- sessione, request_id, cache duplicati in memoria;
- workspace.write per file nuovi, senza sovrascritture;
- MutationObserver, blocchi omnicall, rilevamento fine streaming e ritorno del risultato alla chat;
- build e 20/21 test Go riusciti.

Non sono verificati direttamente: presenza e contenuto attuali, diff, aggancio all’entrypoint, autenticazione, correttezza del parser, caricamento dell’estensione o verticale reale. Ricavare versione Go e risultati dall’ambiente. Una cache in memoria non dimostra persistenza dopo restart.

La descrizione di modifiche a workspace_handler.go è stata ritirata da Gemini. Cercare i riferimenti a idempotency.go per distinguere codice compilato da codice effettivamente usato.

## 9. Architettura concordata e limiti

Distinguere A: chat web ↔ estensione e B: estensione ↔ Go. MCP/JSON-RPC in B non risolve A. JSON-RPC proprietario non equivale a MCP.

Preferire un’integrazione ufficiale verificata nell’account reale; non confondere Gemini web, CLI, API ed Enterprise. Fallback accettato: adapter DOM ristretto alla conversazione attivata, richieste strutturate e stop su formato/pagina non riconosciuti. Non chiamarlo tool calling nativo.

Token mai nel DOM o nel prompt. Policy nel core. Nessuna autorizzazione implicita da testo prodotto dall’IA o dalle pagine. Stesso request_id con payload diverso: conflitto. Non eseguire durante streaming, su esempi citati, messaggi utente o cronologia precedente all’attivazione. Non sovrascrivere il testo dell’utente per reinserire risultati. Prevedere arresto, timeout e limiti ai turni.

Per il prototipo: una chat, un workspace dedicato, un solo tool di creazione file, nessuna shell, cancellazione, sovrascrittura o accesso remoto. L’utente abilita esplicitamente la sessione. Le autorizzazioni sensibili rimangono separate.

Due IA non devono modificare insieme la stessa scheda o file senza controllo di concorrenza. Consenso fra IA non equivale a verifica. Il coordinatore deterministico limita il flusso, non elimina le allucinazioni.

## 10. Fonti di progetto da valutare, non dipendenze approvate

- https://github.com/srbhptl39/MCP-SuperAssistant
- https://github.com/teddashh/multi-ai-chat (percorso consultato rimandava a TED-H-com/multi-ai-chat)
- https://playwright.dev/docs/getting-started-mcp
- https://playwright.dev/mcp/configuration/browser-extension
- https://github.com/browser-use/browser-use
- https://www.perplexity.ai/help-center/en/articles/13915507-adding-custom-remote-connectors
- https://arxiv.org/abs/2503.13657 (fallimenti sistemi multi-IA)
- https://arxiv.org/html/2511.20597v1 (BrowseSafe)
- https://a2a-protocol.org/latest/topics/key-concepts/

Verificare stato, compatibilità, licenze e condizioni dei provider prima del riuso. Non aggirare login, CAPTCHA o restrizioni.

## 11. Procedura di allineamento ancora da completare

1. Inventario read-only su C: root, branch, SHA, upstream, diff staged/non staged, untracked e componenti UI/extension.
2. Backup indipendente su C: prima di modificare la copia di lavoro. Preservare A:, stash e branch di sicurezza.
3. Revisionare diff e segreti: niente git add . indiscriminato, .env, token, chiavi, log privati o binari.
4. Branch dedicato, commit dei soli file revisionati; codice e documentazione identificabili.
5. Test mirati automatici con log e commit di riferimento.
6. Push approvato, senza force push; nessun merge implicito su main.
7. Confrontare SHA locale/remoto e working tree, poi dichiarare sincronizzato solo quel branch.
8. Aggiornare altre copie solo quando necessario e senza modificare deployment live implicitamente.

Non usare reset --hard o git clean per far apparire pulita la copia. Un pull non pubblica file locali untracked. Questo commit documentale non sincronizza automaticamente Windows o VPS.

## 12. Criterio di successo della prima verticale

Richiesta reale nella chat → blocco completo rilevato → sessione autorizzata → un file nuovo nel workspace → risultato correlato reinserito nella stessa chat → conclusione dell’IA. Nessun copia-incolla manuale. Ripetizione senza nuova scrittura; origine/sessione non autorizzata rifiutata.

Una simulazione estensione→Go è utile ma intermedia. Non dichiarare la verticale completata senza il ritorno alla chat reale. Poi aggiungere seconda IA e risorsa remota senza cambiare il contratto di base.

## 13. PROMPT DI AVVIO PER LA PROSSIMA IA

Sei il co-sviluppatore che riprende OmniNode senza conoscenza delle conversazioni precedenti. Leggi questo START_HERE.md integralmente, poi AGENTS.md, SECURITY.md, docs/WORKER2_HANDOVER.md e il codice attuale.

La missione è dare alle IA web strumenti operativi attraverso il browser custom, non costruire un’altra IA. Devi eliminare il trasporto manuale di prompt e comandi fra chat e terminali.

Distingui sempre verificato, riportato, ipotizzato e da completare. Non trattare dichiarazioni di Gemini o vecchi conteggi di test come prove. Non affermare accesso al PC, browser o GitHub senza strumenti realmente disponibili.

Prima risposta: riepilogo breve del prodotto, strumenti disponibili, fatti già verificati e un solo blocco diagnostico read-only per i dati mancanti. Non ricominciare un audit generale o una roadmap infinita.

Priorità: preservare e inventariare il lavoro Windows, revisionarlo e allinearlo a GitHub su branch dedicato, aggiornare l’handover e completare la prima verticale reale. Non cambiare branch con lavoro non salvato. Non perdere stash o backup. Non toccare le VPS per il prototipo locale.

Se hai strumenti autorizzati, esegui letture e test pertinenti invece di chiedere all’utente ogni comando. Se non li hai, dichiaralo e fornisci patch/istruzioni minime. Separa spiegazioni, comandi e output; nessun prompt PS> o ubuntu@ nei blocchi copiabili.

Nessun segreto in chat/repo, shell arbitraria, force push, reset distruttivo, pubblicazione, merge, installazione o deploy senza approvazione specifica. Non promettere esecuzione in background se non esiste.

Concludi ogni consegna con file realmente cambiati, verifiche realmente eseguite, limiti e un prossimo passo concreto. L’obiettivo è un circuito funzionante IA web → OmniNode → ambiente → risultato → IA web.
