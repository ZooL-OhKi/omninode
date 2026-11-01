# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026, sessione fino alle 03:21 CET. [Ripresa senza contesto](ZERO_CONTEXT_HANDOVER.md). Branch feature/bridge-gemini-vertical, PR #9 aperta verso ai-handover-20261015-worker2 all'ultimo controllo. Baseline codice: 9316f6b2eecb252ffe7c7447549bd91a36b91a0f; questo documento non certifica il proprio futuro SHA o i check del commit documentale che lo contiene.

AGENTS.md e SECURITY.md restano normativi: mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso, scadenza e STOP non vengono indeboliti. Nessun merge/deploy implicito.

## CI e prove

Tutti gli 11 check di 9316f6b2 risultavano success al controllo GitHub della sessione. Native-browser usa un host sintetico: CI verde non prova consenso fisico Windows o tutte le condizioni reali.

Progressione storica: 56830c25 dimensioni immagini dai byte; 837df8b0 hardening e lifecycle; 5ab25118 footer osservato; 55291dbd consegna testuale controllata.

Prove Windows/Gemini fornite dall'utente:

- e2e-footer-003: screenshot nel pannello.
- e2e-text-004: JSON inviato, risposta Gemini con ID e 1280x720, SENT_CONFIRMED.
- e2e-image-005: Gemini ha risposto immagine non disponibile; nessuna prova positiva di allegato. Non inferire un guasto di upload da questo solo esito.
- e2e-image-006: screenshot allegato nella conversazione, risultato JSON correlato, risposta Gemini che descrive pulsante rosso STOP DESKTOP e pannello in basso a destra; stato SENT_CONFIRMED — ATTACHMENT_VERIFIED (conferma utente). Circuito immagine assistito riuscito nella configurazione della sessione.

La fonte dell'ultima prova e lo screenshot condiviso dall'utente nella conversazione del 1 novembre alle 03:12 CET. Questa nota ne conserva il resoconto, non una copia dell'immagine: l'artefatto originale non e aggiunto al repository. Non e un'esecuzione fisica dell'assistente, una ricevuta server o una certificazione generale. Non ripetere la prova solo perche la nuova IA non ha la chat precedente.

## Percorso immagine e limiti

Manifest dichiarato nella tranche 0.2.1. Un click esplicito inserisce il testo proprio e condivide il File screenshot mediante evento paste sintetico; e un tentativo di compatibilita, non una garanzia generale di upload. Un solo tentativo di allegato e un solo tentativo di invio nel ledger.

Una sola nuova preview caricata, assenza degli indicatori di upload rilevati e stabilita di 3 secondi abilitano la conferma locale. ATTACHMENT_VERIFIED ha verification=user-confirmed: l'utente conferma immagine nell'input e upload concluso, non una verifica crittografica. Ambiguita dopo 15 secondi produce ATTACHMENT_UNCERTAIN_HALT. Niente secondo paste, clipboard implicita o retry automatico.

Invio testo+immagine con conferma e preview invariata; SENT_CONFIRMED richiede anche immagine nel nuovo messaggio uscente correlato. In e2e-image-006 si aggiunge la risposta visiva del modello. Download resta assistito.

Restano da chiudere STOP nativo -> browser, race fisiche, persistenza crash, Unicode/DPI/multi-monitor, hardening Go e ampliamento autorizzato delle azioni. Non e provato un agente che sviluppa, testa e corregge autonomamente il repository, ne una collaborazione operativa con una seconda IA.

## Copie e ultimo blocco operativo

Copia Windows attiva: C:\Users\ugopl\omninode-github. Copia A: coinvolta nell'allineamento: A:\omninode-clean-20261101-011658. A: ha segnalato desktop.ini in .git/refs; riparazione non confermata.

Alle 03:18 CET il primo script di allineamento ha fallito il parsing per la stringa con $repo:; quel blocco non e stato eseguito. E stato consegnato un allegato corretto usando ${repo}:, ma non e arrivato un output di esecuzione riuscita. Non dichiarare allineati C:, A: o Drive.

Lo script consegnato non e versionato qui e fissava il target 9316f6b2: dopo nuovi commit documentali il suo controllo del remoto puo fermarsi. Non aggirare il controllo o riportare il remoto indietro; ricavare e approvare il nuovo riferimento, quindi rigenerare e validare lo script se serve. Drive conserva snapshot, non certifica integrita Git. Dettagli e recuperi in ../RESUME.md.
