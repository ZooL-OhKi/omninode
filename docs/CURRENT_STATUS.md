# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026. Branch feature/bridge-gemini-vertical, PR #9 aperta verso ai-handover-20261015-worker2. AGENTS.md e SECURITY.md restano normativi: mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso locale, scadenza e STOP non vengono indeboliti. Nessun merge/deploy implicito.

## Evidenza verificata

56830c25 controlla dimensioni PNG/JPEG dai byte; 837df8b0 introduce hardening e lifecycle; 5ab25118 collega il footer Gemini osservato. Tutti gli 11 check di 5ab25118 sono success. Native-browser usa un host sintetico, non certifica Windows o il DOM reale.

L'utente ha mostrato e2e-footer-003: screenshot Windows nel pannello locale. Non e esecuzione fisica dell'assistente e non prova che Gemini abbia ricevuto l'immagine.

## Tranche corrente

Manifest 0.2.1 carica text_delivery.js e content.js. Un deliveryLedger per sessione distingue preparazione, bozza protetta, inserimento, modifica utente, tentativo di invio, conferma DOM ed esito incerto. Due click espliciti separano inserimento e invio del solo testo; il primo tentativo consuma definitivamente l'invio. Nessun retry incerto, clipboard implicita o base64 nel prompt.

Inserimento execCommand e riscontro user-query sono ancora da validare sul provider reale. Il solo composer vuoto non conferma. Download immagine e passaggio manuale, non upload verificato. La prova completa immagine -> chat -> analisi di Gemini manca.

Restano aperti propagazione dello STOP nativo alla UI browser, prove fisiche di race/scadenza, crash-persistenza del registro in memoria, Unicode/DPI/multi-monitor e hardening API/metadati/idempotenza Go. La nuova tranche non modifica quei componenti.

## Copie

Chrome/host usano C:\Users\ugopl\omninode-github. Il clone A: ha segnalato desktop.ini dentro .git/refs: riparazione/allineamento non confermati. Non cancellare copie o branch di recupero. Drive conserva snapshot, non certifica integrita di un clone sincronizzato.
