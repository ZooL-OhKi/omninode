# Notepad task: integrazione browser

Aggiornamento: 9 novembre 2026. Questo documento descrive l’integrazione browser del task Notepad delimitato. Non certifica un agente autonomo generale.

## Flusso

L’estensione accetta `notepad_write` solo con `reference_id`, `x`, `y`, `text` e `share_result: true`. La conferma locale fidata mostra azione e argomenti esatti.

Quell’approvazione autorizza il task nativo delimitato di click/type e la condivisione automatica del risultato/screenshot nella chat Gemini corrente. I controlli nativi su processo, sessione, STOP e no-retry restano obbligatori.

## Verifiche

Il risultato pianifica un inserimento, un paste e un invio. Attende un’anteprima stabile e unica, confronta i pixel decodificati con lo screenshot fornito, riverifica autorizzazione, composer e preview, poi invia una sola volta.

Fallimenti di lettura pixel, bozza cambiata, preview mancante, autorizzazione negata o timeout arrestano il flusso. Nessun fallback o retry automatico. Il confronto pixel è un controllo UI locale, non una ricevuta del provider o una prova di visione del modello.

Bozze e allegati preesistenti non vengono sovrascritti. Un hold richiede intervento; non viene ripreso silenziosamente. Record cancellati bloccano effetti tardivi di autorizzazione.

## Test e limiti

Prima della pubblicazione erano stati eseguiti 12 test Node: 7 mock driver, 3 ledger reali e 2 policy. Nessun DOM Chrome reale, upload reale, input Win32 o end-to-end fisico era stato eseguito.

Questo è un workflow delimitato, non un agente autonomo generale o una delega illimitata a comandi futuri. L’acquisizione iniziale dello screenshot resta sul percorso esistente.
