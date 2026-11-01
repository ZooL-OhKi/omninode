# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026. Fonte operativa da leggere con AGENTS.md e SECURITY.md.

## Repository e CI verificati

- Repository: ZooL-OhKi/omninode.
- Branch: feature/bridge-gemini-vertical.
- Baseline codice: ee7565746809147cecb1be2dd91990ce127d56f7.
- Estensione: 0.3.1.
- PR #9: aperta, non mergiata, base ai-handover-20261015-worker2. Stato mergeable_state clean al controllo, non autorizzazione al merge.
- Tutti gli 11 check restituiti per HEAD della PR al controllo GitHub della sessione erano completed/success. Il conteggio comprende due esecuzioni adapter-tests. In altri commit il numero era 14 o 15 per workflow ripetuti: non sono conteggi di test unitari.

Questo aggiornamento documentale e successivo alla baseline: i suoi check vanno verificati separatamente, senza attribuirgli in anticipo il verde di ee756574.

## Evoluzione del codice

- 7ce0eb6c3a304b098d17e4ada5f8bb9cf6e90f0e: prima automazione solo testuale con fixture errate; non baseline valida del ritorno immagine.
- 400c02c7523d7fca9d50ea0513c6349bbda4163e: inserimento JSON + tentativo screenshot, con conferma locale dell'allegato.
- 89303bec47125b676904f8aca2eb75bd1ff7bbc3: correzione fixture auto-delivery; successivamente CI verde verificata.
- 447bd1aebbd059c8f1e58386389e30d6fc667730: dimensioni sorgente e mapping coordinate preview.
- ea1efb642302e109b367361d5a0f000674d89c9a: movimento puntatore collegato alla chat.
- 607a0c1a7dcc7e9251dc219c95fcf90b57e65d7f: azioni mouse/tastiera e input progressivo.
- 54d5dda57bba6071bb8caafeb6d52dcb83d82191: separazione sessione/backend, deadline cooperativa, focus, DPI prima della GUI e controlli installer.
- 8a2697d761f6be7af35f199cebf1e864043e1f58: compito nativo delimitato notepad_write.
- ee7565746809147cecb1be2dd91990ce127d56f7: collegamento del compito alla chat e tentativo automatico verificato di ritorno.

## Comportamento implementato

Le azioni screenshot, move, click, drag, scroll, press, hotkey e type hanno validazione esplicita. Le azioni desktop ordinarie mantengono la conferma locale specifica. Il riferimento screenshot e associato alla sessione, consumato dall'azione e valido al massimo 60 secondi. Il broker mantiene un solo input in volo, controlla la geometria e richiede uno screenshot dopo l'azione.

DesktopSession conserva credenziale nativa, conversazione, scadenza, lock e STOP. windows_input_backend.py contiene pianificatori deterministici e primitive Win32. Il budget di 12 secondi per execute() e cooperativo: non preempie una chiamata OS bloccante. Il timeout JS di 20 secondi e per richiesta nativa, non per l'intero compito.

Il backend richiede DPI per-monitor prima della GUI e verifica compatibilita geometrica. Seleziona e verifica HWND/PID della finestra bersaglio, tenta il ripristino del focus secondo le normali regole Windows e si arresta se il controllo fallisce. I rilasci di tasti/pulsanti sono tentativi best effort tramite SendInput, non una garanzia assoluta. Unicode e implementato, ma la compatibilita fisica delle applicazioni non e certificata.

notepad_write accetta testo fino a 256 caratteri e coordinate derivate da uno screenshot recente. Il backend limita il bersaglio al processo Blocco note previsto ed esegue un click sinistro seguito dal testo nella stessa operazione. Non invia Enter, non salva, non cancella e non ripete input incerti. Non prova che il documento fosse vuoto o che il testo sia stato accettato dall'applicazione.

Con share_result:true, l'OK locale sul compito autorizza anche la condivisione del risultato/screenshot con la conversazione Gemini corrente. Il ritorno tenta un inserimento, un paste e un invio; richiede preview unica stabile e confronto esatto dei pixel decodificati prima dell'invio. CORS, ricompressione, geometria o DOM non compatibili possono arrestarlo. Il confronto locale non e una ricevuta del provider ne prova di lettura visiva del modello.

Bozze/allegati preesistenti non vengono sovrascritti; un hold non viene ripreso automaticamente. ATTACHMENT_UNCERTAIN_HALT e SEND_UNCERTAIN_HALT non autorizzano retry. I record cancellati bloccano gli effetti tardivi delle autorizzazioni. Il JSON di ritorno usa omninode_response e completed_action e non soddisfa lo schema dei comandi.

Questa e l'automazione di un compito delimitato, non una delega illimitata a comandi futuri, un agente generale o l'automazione dello screenshot iniziale.

## Evidenze effettive

1. L'utente ha riportato 165 pass/0 fail da A:\omninode-clean-20261101-011658. Mancavano i nuovi casi auto-delivery e lo SHA locale: l'attribuzione iniziale alla nuova patch era errata. Le fixture furono poi corrette in 89303bec. Non riutilizzare quell'output per certificare le versioni attuali.
2. Sandbox Python dell'assistente: 30 test passati nella preparazione del refactoring (15 nuovi mock/planner/installer + 15 legacy, con hash del sorgente legacy verificato). Nessuna esecuzione fisica Win32.
3. Sandbox Python: 6 test del helper notepad_task con backend mock. La verifica reale del processo Windows non era eseguita da quei test.
4. Sandbox Node: 12 test del ritorno del compito (7 driver mock, 3 ledger reale con IO simulato, 2 policy) e controlli sintattici di cinque moduli. Non sono prove del DOM/upload reale.
5. CI GitHub della baseline ee756574: 11 check verdi verificati tramite connettore. Le fixture native-browser non equivalgono al desktop fisico.
6. Prova storica e2e-image-006: screenshot nella chat e descrizione visiva Gemini, secondo evidenza fornita dall'utente. Vedere l'handover per la provenienza.
7. Schermata utente delle 04:07 CET: JSON e miniatura nella chat, SENT_CONFIRMED / ATTACHMENT_VERIFIED user-confirmed; una nuova richiesta separata era ancora in attesa.
8. Schermata utente delle 05:00 CET: Blocco note vuoto, risultato screenshot consegnato e click notepad-click-20261101-0454 ancora da autorizzare. Non prova click, digitazione o compito completato.

Le immagini originali delle prove sono nella conversazione, non aggiunte al repository. Non ripetere prove gia positive solo per ricostruire il contesto.

## Installazione e copie

Percorsi riportati dall'utente: sorgenti nativi C:\Users\ugopl\omninode-github\desktop, estensione C:\Users\ugopl\omninode-github\omniclient\extension. A: contiene un'altra copia, non certificata allineata; precedente incidente desktop.ini in .git/refs non dichiarato risolto.

Lo script locale precedente era fissato a 54d5dda5 e aggiornava 6 file nativi e 11 dell'estensione, senza modificare Git. L'utente ha segnalato esito positivo dopo correzioni PowerShell: campo percorso inizialmente vuoto, blocco firma/download e File.Replace con $null convertito in stringa vuota, corretto con NullString.Value. Backup segnalato: C:\Users\ugopl\AppData\Local\OmniNode\Backups\runtime-20261101-045107-b61fe6a5d598400491753f9cbebfe55b. Preservarlo.

Non e attestata l'installazione coerente di 8a2697d7 o ee756574. Il vecchio script non distribuisce notepad_task.py o task_delivery.js e non va riusato come aggiornamento alla nuova baseline. Le sostituzioni dei file runtime possono lasciare modifiche nel clone: non eseguire pull/reset/stash automatici per cancellarle.

GitHub, working tree C:, working tree A:, file runtime, processo avviato e snapshot Drive sono stati distinti. Nessun allineamento globale, merge, release o deploy Oracle e stato eseguito. Il connettore GitHub non e un esecutore Windows; Python/Node sandbox sono esecutori diversi.

## Residui prioritari

Distribuzione locale coerente approvata della baseline corrente, prova fisica mirata del compito e verifica dei suoi arresti. Poi STOP nativo/browser bidirezionale, persistenza/crash senza replay, focus/DPI/Unicode reali, multi-monitor, hardening Go/trasporti live e ampliamento delle capability per compito. Il confronto Gemini e stato inoltrato manualmente dall'utente: non e collaborazione automatica fra agenti.

Conservare mTLS MQTT/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso e STOP. Nessun bypass login/CAPTCHA, shell remota arbitraria o esposizione pubblica.
