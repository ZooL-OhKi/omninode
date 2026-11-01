# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026. Branch `feature/bridge-gemini-vertical`, HEAD `7ce0eb6c3a304b098d17e4ada5f8bb9cf6e90f0e`. PR #9 resta aperta; nessun merge o deploy implicito.

AGENTS.md e SECURITY.md restano normativi: mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso, scadenza e STOP non vengono indeboliti.

## Consegna automatica autorizzata

Il commit `7ce0eb6c3a304b098d17e4ada5f8bb9cf6e90f0e` aggiunge `DeliveryLedger.autoDeliver()` e il pulsante esplicito "Autorizza consegna automatica nel composer (inserimento + invio, un tentativo)".

La consegna automatica esegue al massimo un inserimento e un invio per `request_id`. Mantiene:

- `DRAFT_PROTECTED_HOLD` se il composer contiene una bozza utente, allegati o upload;
- verifica del composer prima e dopo l’autorizzazione locale;
- single-flight tramite `busy`, `autoAttempted` e `sendAttempted`;
- un solo tentativo di invio, senza retry;
- `SEND_UNCERTAIN_HALT` su evidenza mancante, timeout, STOP o errore;
- anti-loop: il risultato contiene `omninode_response: true` e `completed_action`, ma `parseRequest()` lo rifiuta come comando operativo.

## Test locali eseguiti

Comando eseguito dall’utente in `A:\omninode-clean-20261101-011658`:

```powershell
node --test omniclient/extension/*.test.cjs
```

Esito osservato:

- 165 test pass;
- 0 fail;
- 0 skipped;
- durata 216.6092 ms.

I test coprono bozze utente, modifiche concorrenti, sessioni scadute, duplicati, un solo inserimento/invio, timeout incerti, STOP, allegati, preview, anti-loop e rifiuto del JSON di risposta come nuovo comando.

## Prove e limiti

`e2e-image-006` resta l’unica prova positiva nota del percorso screenshot -> allegato Gemini -> lettura visiva, con conferma utente. Non è una certificazione generale.

La consegna automatica è implementata e coperta dai test automatici, ma non è ancora stata eseguita una prova fisica nel composer Gemini dopo il reload dell’estensione. Non dichiarare `SENT_CONFIRMED` per una nuova sessione senza evidenza nuova e ID nuovo.

## Copie e allineamento

La copia `A:\omninode-clean-20261101-011658` ha eseguito con successo la suite estesa. Questo non certifica l’allineamento Git completo con `C:` o Drive, né ripara il precedente problema `desktop.ini` in `.git/refs`.

Non sincronizzare `.git` tramite Drive, non cancellare recuperi e non forzare il branch.
