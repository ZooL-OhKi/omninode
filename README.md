# OmniNode

OmniNode collega chat web AI, estensione browser e strumenti locali per osservare e controllare un ambiente esplicitamente autorizzato, ricevendo risultati nella stessa conversazione. Non è un nuovo LLM.

## Iniziare

Leggere [START_HERE](START_HERE.md), [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md). Consultare [indice](INDEX.md), [build e test](BUILD.md) e [recuperi](RESUME.md).

## Stato verificato al 9 novembre 2026

La PR #11 è stata unita con squash su main nel commit 370d93cb8c24460315bc1ac38b6aead88576f748. Il commit successivo 6b3564a80206cf3b95550e1ec7dce97fe931ddb9 corregge il confronto della conversazione nella concessione desktop.

Sul commit 4da4e974c72b0c303dd2cfd93a0fce4b1bc15e60 risultano success: OmniNode CI #163, Desktop primitive validation #70 e Build and Release #86. Extension validation non è stata eseguita su quel commit: non trasferire esiti fra SHA. Rileggere HEAD e CI prima di installare.

Il percorso Perplexity collega screenshot, move, click, type, press e hotkey. Le prove storiche riportano immagini e JSON per screenshot e azioni pointer/tastiera, ma non una prova di type sul target corretto dopo la consegna. Il click precedente richiesto dal broker e il blur del composer non certificano l'identità del controllo interno alla stessa finestra Chrome. L'attesa di 150 ms non garantisce rendering stabilizzato.

## Componenti

- omniclient/: worker e strumenti Go.
- omniclient/extension/: adapter chat e bridge browser.
- desktop/: host Native Messaging e input Windows autorizzato.
- node1-gateway/: gateway Python e orchestrazione.
- deploy/ e scripts/: configurazioni e strumenti; non attestano servizi attivi.

## Limiti

CI, fixture sintetiche, installazione Windows e prove reali sono evidenze distinte. Nessun aggiornamento remoto installa automaticamente file locali. Restano da qualificare typing sul target corretto, race di focus, STOP/revoca/scadenza/navigazione, crash/restart senza replay incerto e collaborazione AI autonoma.

La manutenzione documentale completa è in corso: i documenti non ancora revisionati possono contenere baseline storiche. Non cancellare backup o modificare licenze sulla base di descrizioni storiche.
