# Gemini adapter: stato e limiti

Aggiornamento: 9 novembre 2026. Questo documento distingue prove storiche, capacità correnti e limiti. Non certifica un ciclo autonomo Gemini.

## Prove storiche

La baseline `55291dbd3b65f16f03b923a770657972865674c4` aveva 11 check success. `e2e-footer-003` provava lo screenshot locale; `e2e-text-004` provava ritorno testuale e risposta di Gemini con ID e dimensioni.

Queste sono evidenze storiche riportate, non esecuzione fisica dell’assistente né prova di accesso autonomo fra agenti.

## Capacità correnti

Il flusso Gemini richiede controlli sul footer, assenza di streaming, mutazioni osservate, quiescenza e conferma locale. Il parser rifiuta `omninode_response` e gli ID del registro di consegna.

La tranche immagine prevede allegato con consenso esplicito, file PNG/JPEG con estensione corretta, un solo paste sintetico sul composer e nessuna clipboard di sistema. L’upload sintetico non è ancora validato sul provider reale.

## Limiti

`ATTACHMENT_PENDING` passa a `ATTACHMENT_READY_FOR_CONFIRM` solo con una nuova immagine caricata, nessun upload/alert e tre secondi di stabilità. Il click di conferma autorizza un unico invio; non è una ricevuta server.

Timeout, errore o preview sostituita bloccano con `ATTACHMENT_UNCERTAIN_HALT`; nessun fallback automatico. Test con fixture non certificano upload reale.

Accettazione finale: Gemini riceve l’immagine e descrive un dettaglio visivo non deducibile dal JSON. Leggere [stato corrente](CURRENT_STATUS.md) e [SECURITY](../SECURITY.md).
