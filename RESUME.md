# OmniNode — ripresa operativa verificata

Aggiornamento: 16 ottobre 2026, circa 02:37 CEST. Leggere questo file prima dei riepiloghi storici. Non costituisce certificazione di produzione.

## Missione

OmniNode collega le IA nelle rispettive chat web al browser e agli strumenti autorizzati locali/remoti, restituendo i risultati nella stessa conversazione. Non è un nuovo chatbot o un agente sostitutivo. La console PWA è accessoria. Obiettivo immediato: una chat reale → richiesta strutturata → core locale → creazione autorizzata di un file nuovo → risultato alla stessa chat, senza trasporto manuale di comandi.

## Repository e branch

Repository ZooL-OhKi/omninode.
- Branch di recupero: local-work-20261016-005605.
- PR #8 verso ai-handover-20261015-worker2: https://github.com/ZooL-OhKi/omninode/pull/8
- Baseline documentale handover: fa410777c531005329127215f96f56d743111067, con START_HERE.md sul branch ai-handover-20261015-worker2.
- Questo branch di recupero non contiene necessariamente START_HERE.md: questo RESUME.md è autonomo. Non cambiare branch con lavoro locale non salvato solo per leggerlo.
- Ultimo commit di codice verificato in CI: 8ba3218d825b287d707216009006f3107cab979f. Il presente commit documentale sarà successivo: ricavare lo SHA reale con Git.
- Nessun merge su main e nessun deploy effettuato durante queste correzioni.

## Lavoro recuperato e correzioni pubblicate

26fcde2: salvataggio locale di gateway/MQTT/CI, UI Go/PWA, test e idempotency.go.
80a0b7c: formattazione Go.
e0c8cf7823b1af2f0449966e7631902d4ac7f123: rollback workspace con rilascio mutex garantito da defer e due test.
0c518e6ecbbe61c8810e5808f42245ecc7e40bb8: workflow Recovery Validation.
8ba3218d825b287d707216009006f3107cab979f: import task_store mancante, cleanup lifecycle con try/finally, terminatore SSE corretto e due test.

## Evidenze di test

Output terminale utente precedente alle ultime correzioni: 21 test Go passati; Python 122 passed, 2 skipped. Non attribuire tali conteggi ai commit successivi.

Verifica GitHub effettuata alle circa 02:37 CEST: job go e python entrambi success in ciascuna delle due esecuzioni sul nuovo codice:
- https://github.com/ZooL-OhKi/omninode/actions/runs/38830216337
- https://github.com/ZooL-OhKi/omninode/actions/runs/38830221263

Il job Go esegue mod verify, vet, test -race e build. Il job Python installa requirements, pytest-asyncio, Playwright/Chromium, compila ed esegue pytest. I due run derivano dai trigger push e pull_request. Success dei job non prova una demo reale con chat web, sicurezza completa o segreti assenti.

## Cosa NON è implementato o validato

- La directory omniclient/extension non compare nell’elenco remoto esaminato.
- ui_server.go non registra /api/bridge/execute: contiene UI e proxy verso /mcp.
- Nessuna verticale chat web → estensione → Go → chat verificata.
- Endpoint UI di scrittura senza verifica del chiamante/sessione: non esporli in rete o tramite tunnel.
- workspace.write usa os.WriteFile: permette sovrascrittura. Il vincolo solo file nuovi non è implementato in quel percorso.
- Controllo percorsi lessicale: non considerarlo prova di confinamento contro symlink o reparse point.
- WorkspaceHandler ha un registro persistente separato da LocalIdempotencyStore: non introdurre un terzo registro. Registra gli ID prima dell’effetto; rimane una finestra di crash. Non confronta impronta del payload né restituisce risultato originale.
- idempotency.go presente non dimostra che sia usato nel flusso operativo.
- UI index usa innerHTML per cronologia con campi controllabili e uno script CDN esterno: hardening da completare.
- Scansione Advanced Security non eseguibile tramite connettore perché non abilitata. La precedente scansione mirata NON copriva tutti i file: non dichiarare la repository priva di segreti.

## Copie locali e backup

Windows di lavoro: C:\Users\ugopl\omninode-github.
Backup verificato dall’output utente: C:\Users\ugopl\omninode-github-backup-20261016-005605, 186 file, zero fallimenti.
Ultimo stato locale mostrato: pulito e sincronizzato prima dei commit remoti e0c8cf7, 0c518e6 e 8ba3218. Non dichiarare Windows aggiornato agli ultimi commit.

Copia storica A:\omninode: blocchi GoogleDriveFS, backup A:\omninode-backup-20261015-223838, branch backup/windows-before-sync-20261015-224242 e stash con messaggio Windows prima allineamento 20261015-224242. Non cancellare, rinominare o pulire alla cieca. Identificare lo stash dal messaggio/SHA, non assumere indice immutato.

VPS: sorgenti storicamente osservati a 2a07fda in /home/ubuntu/omninode. Archivista esegue /opt/omninode/omniclient/omniclient: aggiornare sorgenti non aggiorna quel binario. Stato live attuale non ricontrollato, nessun rollout.

## Copilot

Non è un prerequisito. Account mostrato su Copilot Free, reviewer non selezionabile; richieste del connettore senza errore non hanno provato l’ingaggio. Non attendere Copilot e non acquistare abbonamenti per continuare. Non dichiarare collaborazione con Gemini se non esiste una comunicazione reale.

## Prompt di avvio per la prossima IA

Sei il co-sviluppatore che riprende OmniNode senza conoscere la chat precedente. Leggi RESUME.md, poi AGENTS.md e le policy della repository. Le affermazioni storiche non sostituiscono la lettura del codice. La missione è l’estensione operativa delle IA web, non un nuovo chatbot.

Verifica branch, SHA, diff, working tree e check CI. Preserva lavoro locale e backup. Non rifare roadmap o audit generali. Correggi prima le protezioni del percorso che userà il bridge: autenticazione/sessione, loopback, limiti delle richieste, workspace confinato anche rispetto ai link, creazione esclusiva, conflitto stesso ID/payload diverso e semantica di crash esplicita. Aggiungi test negativi mirati. Poi implementa il bridge e l’estensione mancanti con attivazione esplicita sulla sola scheda/conversazione scelta.

Non eseguire blocchi durante streaming, esempi citati o cronologia preesistente. Non inserire token nel DOM/prompt. Rifiuta formati sconosciuti; prevedi stop visibile e timeout. Non sovrascrivere testo dell’utente durante il ritorno alla chat. Distinguere mock backend da verticale con chat reale.

Usa strumenti autorizzati per letture e test; non chiedere all’utente operazioni eseguibili da te. Se manca accesso al PC/browser, dichiaralo e separa implementazione remota da validazione locale. Non esistono attività in background implicite.

Conserva mTLS, TLS/ACL e policy esistenti; niente shell arbitraria, segreti, esposizione di rete, force push, reset distruttivi o deploy. Per scritture esterne rispetta il gate di conferma dello strumento; autorizzazione generale non lo elimina. Nessun merge di componenti non verificati solo per dichiarare tutto allineato.

Consegna finale con commit reali, test realmente eseguiti, stato di ciascuna copia e blocchi residui. Non dichiarare completata la verticale se non è avvenuto il ritorno automatico nella chat reale.
