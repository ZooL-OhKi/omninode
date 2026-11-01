# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026. Branch feature/bridge-gemini-vertical, PR #9 aperta verso ai-handover-20261015-worker2. AGENTS.md e SECURITY.md restano normativi: mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso, scadenza e STOP non vengono indeboliti. Nessun merge/deploy implicito.

## Evidenza reale e CI

56830c25: dimensioni immagini dai byte; 837df8b0: hardening e lifecycle; 5ab25118: footer osservato; 55291dbd: consegna testuale controllata. Tutti gli 11 check di 55291dbd sono success. Native-browser usa un host sintetico.

Prove fornite dall'utente Windows/Gemini: e2e-footer-003 mostra screenshot nel pannello; e2e-text-004 mostra JSON inviato, risposta di Gemini con ID e 1280x720 e SENT_CONFIRMED. Sono prove singole, non esecuzioni fisiche dell'assistente o certificazione generale.

## Tranche immagine

Manifest 0.2.1. Il ledger mantiene un solo tentativo di invio e ora un solo tentativo di allegato. Un click esplicito inserisce il testo proprio e condivide il File screenshot mediante evento paste sintetico. Questo e un tentativo di compatibilita, non prova di upload: Gemini puo ignorarlo.

Una sola nuova preview caricata, assenza degli indicatori di upload rilevati e stabilita di 3 secondi abilitano la conferma locale. ATTACHMENT_VERIFIED ha verification=user-confirmed: l'utente conferma immagine nell'input e upload concluso. Non e verifica crittografica ne ricevuta server. Mancanza/ambiguita dopo 15 secondi produce ATTACHMENT_UNCERTAIN_HALT; niente secondo paste, clipboard implicita o retry automatico. Non dichiarare che l'immagine e arrivata al modello prima della prova reale.

L'invio testo+immagine richiede tale conferma e la preview invariata. SENT_CONFIRMED richiede anche un'immagine nel nuovo messaggio uscente correlato. La prova finale Gemini che descrive un dettaglio dello screenshot resta da eseguire. Download e solo assistito.

Restano STOP nativo -> browser, race fisiche, persistenza crash, Unicode/DPI/multi-monitor e hardening Go. Nessuna shell arbitraria, porta pubblica o fallback plaintext viene introdotto.

## Copie

Chrome/host: C:\Users\ugopl\omninode-github. A: ha segnalato desktop.ini in .git/refs; riparazione non confermata. Preservare copie e recuperi. Drive conserva snapshot, non certifica integrita Git.
