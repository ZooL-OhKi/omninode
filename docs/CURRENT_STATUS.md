# Stato corrente OmniNode

Aggiornamento documentale: 16 ottobre 2026. Baseline del codice verificata: b669ec404007e01d56b12d502887f695895a8ae1, branch feature/bridge-gemini-vertical. Questo documento distingue prodotto richiesto, codice presente e prove reali; non certifica la produzione. Ricontrollare sempre HEAD e CI dopo nuove modifiche.

## Missione e risultato mancante

OmniNode deve essere il braccio operativo delle IA nelle loro chat web: vedere lo schermo, usare mouse e tastiera, lavorare su file e web, aprire e coordinare altre chat nella stessa finestra, restituendo automaticamente evidenze alla conversazione autorizzata. Non e un nuovo chatbot; PWA e popup sono console accessorie. Un coordinatore deterministico non richiede un ulteriore LLM.

La conversazione web non e ancora collegata automaticamente al desktop. Aprire una scheda Gemini o Claude non significa aver consultato quell'IA. Non esiste una prova completa chat -> desktop -> risultato nella stessa chat -> continuazione.

## Codice presente e limiti

- Estensione 0.2.0: service_worker.js, native_client.js e desktop_broker.js; permessi activeTab, tabs, nativeMessaging. Il popup e il solo chiamante autorizzato dal broker; pagine web e content script non controllano il desktop. Il vecchio adapter Gemini e il worker HTTP non sono caricati dal manifest.
- Host Python: native_host.py, consenso locale Tk, STOP, sessione associata a conversazione, scadenza e sequenze senza retry automatici. L'host non apre porte di rete. Installer per utente presente, non eseguito sul PC dall'assistente.
- Primitive desktop: display principale, testo ASCII stampabile, mouse, tasti e screenshot. Unicode, multi-monitor e calibrazione DPI non verificati. STOP non annulla input gia consegnati al sistema operativo.
- Immagini: preview in memoria fino a 1280x800 e 600 KiB, sorgente fino a 16 MiB e limite dimensionale nel percorso di conversione. Il test browser usa un'immagine sintetica e un host fixture, non il desktop reale.
- Go: worker MQTT, UI/proxy e bridge HTTP sperimentale separati dal canale desktop nativo. workspace.write crea file esclusivamente tramite OpenRoot e O_EXCL. Metadati, API UI, bind/origini e idempotenza richiedono ancora hardening; la cache aggiuntiva del bridge non e crash-safe ne sufficiente contro richieste concorrenti.
- MCP SDK, CDP e coordinatore multi-IA sono codice presente, non integrazioni web operative. Il flag tests_passed di una proposta non sostituisce un'esecuzione verificata.

## Evidenze verificate

Sul commit di baseline, tutti i 9 check restituiti per la PR #9 erano success: Go, Python nei due workflow, desktop Windows/Linux, adapter, native-browser e controllo segreti. I job non sono conteggi di singoli test. Il test Chromium prova un vero canale nativo Linux con fixture sintetica; non prova consenso Windows, input fisico, account IA o allegati automatici. Il workflow Build and Release non e coperto da questa attestazione: contiene configurazioni storiche da revisionare prima di main o tag.

## Repository, copie e deploy

PR #9 aperta verso ai-handover-20261015-worker2, base 86fe9f2ab8805cd850bf60811de10fb813012cd5; non integrata al controllo di baseline. Nessun merge o deploy implicito.

Windows attivo: C:\Users\ugopl\omninode-github. Il suo SHA attuale non e verificato; nessun allineamento remoto prova quello locale. Le sorgenti VPS /home/ubuntu/omninode erano state allineate dall'utente a 86fe9f2; stato attuale non ricontrollato. Il binario archivista in /opt/omninode/omniclient non viene aggiornato da un pull in /home/ubuntu.

## Priorita

Chiudere il percorso autorizzato conversazione -> strumenti -> risultato, verificare l'installazione Windows e lo stop reale, poi coordinamento fra IA. Preservare mTLS, ACL, workspace e conferme per azioni sensibili. Niente esposizione pubblica, aggiramento di login/CAPTCHA, reset distruttivi o attivita in background dichiarate senza esecutore reale.
