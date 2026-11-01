# Adapter Gemini: prova reale bloccata, non operativo end-to-end

## Riferimento

Analisi del commit 8a4a81587e398c75b75e8b1fee3a782fee1476ed sul branch feature/bridge-gemini-vertical, PR #9 aperta. Osservazioni locali fornite dall'utente il 1 novembre 2026; non esecuzione fisica dell'assistente. Vedere CURRENT_STATUS.md e SECURITY.md per i vincoli normativi.

## Codice e prove distinti

Il manifest 0.2.1 carica content.js per Gemini. La sessione e attivata dal popup tramite consenso nativo Windows; non e una certificazione del percorso automatico. La CI del commit di riferimento era verde, ma non valida il DOM reale Gemini ne il ritorno automatico nella chat. I documenti che descrivono il manifest 0.2.0 sono una baseline storica, non lo stato di questo commit.

## Evidenza locale

L'utente ha mostrato registrazione host riuscita, finestra Windows Desktop ACTIVE, badge ON e pannello di attivazione. Il cambio di conversazione ha terminato una sessione. Dopo riattivazione nella stessa conversazione, una nuova risposta JSON screenshot e rimasta senza esecuzione visibile.

Una lettura DOM ha trovato due model-response con un pre ciascuno; aria-busy e data-is-streaming erano entrambi null. isSettled in content.js richiede invece almeno un attributo esplicito false: questa condizione blocca la richiesta. Nessun segnale alternativo di completamento reale e stato validato. Non sostituire questa verifica con la sola assenza del pulsante STOP o con un timer di quiescenza.

## Ulteriori difetti verificati nel codice

- Il broker restituisce {ok, request_id, result}, dove result e l'envelope nativo {ok, session_id, sequence, result}. Il renderer tratta invece il primo result come immagine con kind e data_url.
- native_channel.py restituisce data_base64 e mime. screen_preview.py puo usare preview_width/preview_height mantenendo width/height della sorgente: serve un normalizzatore validato e limitato, non un cast del payload.
- Il pannello locale non e un messaggio inviato alla conversazione Gemini e non soddisfa il ritorno automatico richiesto da NEXT_STEPS.md.
- Il parser attuale non distingue un esempio JSON valido da una richiesta operativa nuova: il rifiuto categorico degli esempi non e dimostrato.
- La baseline WeakSet dei nodi non dimostra il rifiuto della cronologia quando il DOM viene ricreato.

## Prossima correzione e criteri di accettazione

Preservare fail-closed, consenso locale, binding conversazione, STOP, scadenza e nessun retry input. Acquisire solo metadati non sensibili del ciclo DOM reale streaming/completato prima di abilitare un nuovo rilevatore. Screenshot statici di risposte finite non provano una transizione affidabile.

Aggiungere fixture della transizione osservata e test negativi per pause, segnali mancanti, risposta precedente, esempi, navigazione e STOP durante operazioni asincrone. Verificare anche identita estensione/frame/documento e invalidazione delle risposte tardive tra sessioni.

Normalizzare e validare l'envelope nativo con test per MIME, base64, dimensioni preview e limite 600 KiB; non pubblicare dati immagine o credenziali nei log. Validare separatamente il ritorno nella stessa chat e la protezione della bozza. Nessuna dichiarazione di E2E completato prima della prova locale positiva.

## Esperimento precedente

Le prove storiche del parser e del bridge HTTP usavano fixture e Chromium simulato, non la chat reale. Non usare quei conteggi o la CI verde come certificazione operativa.
