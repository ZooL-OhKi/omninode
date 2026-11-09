# Stato corrente OmniNode

Aggiornamento: 9 novembre 2026. Questo documento descrive lo stato verificato su `main`; `AGENTS.md` e `SECURITY.md` restano normativi. Le descrizioni storiche non prevalgono sullo stato corrente.

## Repository e CI

- Repository: `ZooL-OhKi/omninode`; branch di manutenzione: `main`.
- La PR #11 è stata unita con squash nel commit `370d93cb8c24460315bc1ac38b6aead88576f748`.
- Il commit `6b3564a80206cf3b95550e1ec7dce97fe931ddb9` corregge il confronto della conversazione nella concessione desktop.
- Il commit `4da4e974c72b0c303dd2cfd93a0fce4b1bc15e60` installa Chromium per i test gateway e rende idempotente la creazione della directory Native Messaging nel test desktop.
- Sul commit `4da4e974...` risultano `success`: OmniNode CI #163, Desktop primitive validation #70 e Build and Release #86. Extension validation non è stata eseguita su quel commit; non trasferire esiti fra SHA.

## Capacità implementate

L’estensione Perplexity supporta i comandi `screenshot`, `move`, `click`, `type`, `press` e `hotkey`. Il broker richiede un target confermato da `click`, `drag` o `notepad_write` prima di `type`, `press` e `hotkey`.

La consegna del risultato inserisce il JSON e l’allegato nel composer Perplexity, invia una sola volta e verifica la bolla uscente con il layout allegato-fratello. Dopo una consegna verificata, il composer viene sfocato.

Il backend desktop conserva consenso locale, binding alla conversazione, scadenza, STOP, lock, deadline cooperativa e fail-closed su identità o focus cambiati.

## Prove e limiti

Le prove storiche riportano screenshot, movimento e azioni pointer/tastiera nel browser reale, ma non una prova di `type` sul target corretto dopo la consegna. Il click precedente e il blur del composer non certificano l’identità del controllo interno alla stessa finestra Chrome. L’attesa di 150 ms riduce il rischio di screenshot prematuro, ma non garantisce il rendering.

Restano da qualificare: typing sul target corretto, race di focus, STOP/revoca/scadenza/navigazione, crash/restart senza replay incerto, Unicode, DPI, multi-monitor, collaborazione AI autonoma, servizi remoti e produzione.

## Manutenzione documentale

La manutenzione è in corso. I documenti storici vengono conservati quando contengono informazioni di recupero, invarianti di sicurezza o cronologia utile; vengono aggiornati solo dopo verifica del codice e dei riferimenti reali.
