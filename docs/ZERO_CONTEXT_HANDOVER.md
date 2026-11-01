# OmniNode: ripresa senza contesto

Aggiornamento: 1 novembre 2026, successivo alla verifica di ee7565746809147cecb1be2dd91990ce127d56f7. Non certifica il futuro SHA documentale o il completamento del progetto.

## Missione

L'utente vuole dare un obiettivo a una IA web e autorizzare un compito delimitato una sola volta, senza copiare continuamente PowerShell o cliccare ogni passaggio. OmniNode deve eseguire, osservare e restituire risultati nella stessa conversazione, con STOP e perimetri reali. Non costruire un nuovo LLM e non chiamare autonomia un popup o una demo screenshot.

## Ordine di lettura e regole

Leggere CURRENT_STATUS.md, ../AGENTS.md, ../SECURITY.md, ../RESUME.md, ../NEXT_STEPS.md, ../BUILD.md, quindi codice e workflow interessati. Le guide storiche possono essere superate: confrontarle con lo stato e i sorgenti. Non inventare esecutori Windows, test, attivita in background, contatti diretti con Gemini o deploy.

Preservare recuperi, stash, branch e copie storiche. Nessun reset distruttivo, force push, sincronizzazione di .git tramite Drive, shell remota arbitraria, fallback plaintext o bypass login/CAPTCHA. Conservere mTLS MQTT/ACL, TLS 1.3 e OpenRoot/O_EXCL. L'autorizzazione generale non sostituisce le approvazioni specifiche per scritture esterne, merge o deploy.

## Repository corrente

Repository ZooL-OhKi/omninode; branch feature/bridge-gemini-vertical. PR #9 aperta e non mergiata, base ai-handover-20261015-worker2. HEAD di codice verificato ee7565746809147cecb1be2dd91990ce127d56f7, estensione 0.3.1, 11 check completed/success al controllo. I check dei commit successivi vanno ricontrollati.

Non ripartire da 9798034c, 9316f6b2 o b669ec4 come HEAD: sono riferimenti storici. La sequenza dei commit recenti e nello stato corrente.

## Cosa c'e nel codice

- omniclient/extension/: parser Gemini, gate su risposte nuove e stabilizzate, broker, correlazione, ledger di consegna e IO del composer. Il manifest carica action_policy.js, task_delivery.js, text_delivery.js e content.js.
- desktop/desktop_control.py: sessione nativa, schemi, scadenza, lock, STOP e deadline cooperativa per operazione.
- desktop/windows_input_backend.py: pianificatori deterministici, input Win32/Unicode, focus e rilasci best effort; niente tecniche anti-bot.
- desktop/notepad_task.py: compito unico click+testo limitato al processo Blocco note e al bersaglio verificato. Nessun Enter, salvataggio o replay.
- desktop/native_host.py, native_channel.py e native_bootstrap.py: consenso visibile, framing stdio e correlazione nativa, non rete pubblica.
- desktop/install_windows.py: launcher per-user verso i sorgenti, runtime Python isolato e verifiche delle dipendenze; dry-run senza --apply.
- omniclient/ e node1-gateway/: percorsi Go/Python/MQTT distinti dal Native Messaging. Codice disponibile non prova servizi avviati su Oracle.

Con share_result:true, un OK locale sul comando notepad_write autorizza anche il tentativo automatico di ritorno nella chat Gemini corrente. La preview deve essere unica/stabile e superare il confronto pixel. Bozze, allegati preesistenti o incertezza fermano il percorso; niente retry automatico. Non e una delega generale a futuri comandi del modello e non automatizza lo screenshot iniziale.

## Prove e provenienza

- e2e-footer-003: screenshot nel pannello, non nella chat.
- e2e-text-004: JSON nella chat e risposta Gemini correlata, non prova immagine.
- e2e-image-005: immagine non disponibile secondo risposta del modello, prova non positiva.
- e2e-image-006: secondo screenshot utente del 1 novembre alle 03:12 CET, immagine e JSON nella chat e descrizione visiva Gemini (STOP DESKTOP e pannello). Prova assistita singola. L'originale non e versionato; non attribuire una ricevuta server o una verifica crittografica. Non dichiarare confermato lo STOP successivamente richiesto.
- Schermata 04:07 CET: altra consegna assistita con SENT_CONFIRMED e ATTACHMENT_VERIFIED user-confirmed. Una richiesta nuova era distinta e ancora pendente.
- Schermata 05:00 CET: Blocco note vuoto e click ancora in attesa; non prova scrittura riuscita.

Non riutilizzare questi ID come comandi live e non ripetere prove positive solo per rimettere in contesto una nuova IA. La prova fisica del nuovo notepad_write con ritorno automatico non e ancora attestata.

I 165 test Windows storici erano stati erroneamente attribuiti ai nuovi casi; le fixture sono state corrette. In seguito l'assistente ha eseguito separatamente 30 test Python/mock del refactoring, 6 helper mock del compito e 12 Node del ritorno. Perimetri e limiti sono in CURRENT_STATUS.md e nelle note delle tranche. La CI verde non equivale a input sul PC dell'utente o assenza totale di difetti.

La revisione di Gemini e stata ricevuta tramite messaggi inoltrati dall'utente. Non c'e prova di una collaborazione automatica fra agenti. Un solo responsabile per patch.

## Windows, copie e incidenti da preservare

Copia operativa riportata: C:\Users\ugopl\omninode-github. Altra copia: A:\omninode-clean-20261101-011658, con precedente desktop.ini in .git/refs. Riparazione e allineamento Git completo non attestati. Non rimuovere refs, oggetti o lock per far passare fsck. Diagnosi e backup verificati prima di recuperi.

Un vecchio script delle 03:18 non supero il parsing per $repo: in stringa espandibile; usare ${repo}: quando necessario. La successiva consegna corretta non certificava l'allineamento C:/A:/Drive.

L'updater runtime successivo era fissato a 54d5dda5 e non aggiornava Git. Dopo errori per percorso vuoto, policy di esecuzione e File.Replace, l'utente ha segnalato esito positivo. Per File.Replace senza backup serve un vero null stringa, non l'eventuale stringa vuota prodotta dal binding di $null; la correzione locale usava System.Management.Automation.Language.NullString.Value. Non disabilitare globalmente le policy PowerShell. Preservare il backup esatto indicato in CURRENT_STATUS.md.

Quel vecchio updater non installa i moduli aggiunti in 8a2697d7/ee756574: non riutilizzarlo per dichiarare aggiornato l'ultimo runtime. Non e arrivata prova di installazione coerente della baseline attuale. L'aggiornamento dei file lascia possibili modifiche nel working tree; non forzare pull/reset e non cancellarle automaticamente. Drive deve conservare snapshot verificati, non una .git sincronizzata.

## Passo successivo e accettazione

Preparare un aggiornamento locale coerente, con target verificati, backup e approvazione specifica. Poi una sola prova mirata: screenshot recente, notepad_write con testo esatto/share_result:true, unico OK locale, click+digitazione e ritorno automatico. Serve evidenza del testo nell'applicazione e del messaggio uscente con immagine. Non dichiarare autonomia generale.

Dopo questa verticale restano STOP bidirezionale, crash/restart senza replay, verifiche fisiche focus/DPI/Unicode, multi-monitor, hardening Go, trasporti e servizi Oracle live e concessioni per altri obiettivi. Nessun merge, release o deploy e implicito.

Le versioni storiche complete di questo handover restano nella cronologia Git; RESUME.md conserva la mappa delle copie e dei recuperi e non viene modificato da questo allineamento. A fine tranche registrare SHA, comandi davvero eseguiti, CI, prova fisica e residui separatamente.
