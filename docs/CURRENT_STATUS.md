# Stato corrente OmniNode

Aggiornamento: 1 novembre 2026. Branch `feature/bridge-gemini-vertical`. Ultimo commit di codice pubblicato nella sessione: `400c02c7523d7fca9d50ea0513c6349bbda4163e`. Questo documento non certifica HEAD futuro, CI, merge o deploy.

AGENTS.md e SECURITY.md restano normativi: mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, consenso, scadenza e STOP non vengono indeboliti.

## Correzione del percorso di consegna

`7ce0eb6c3a304b098d17e4ada5f8bb9cf6e90f0e` introduceva un percorso automatico solo testuale. Non completava la consegna dello screenshot.

`400c02c7523d7fca9d50ea0513c6349bbda4163e` modifica `omniclient/extension/text_delivery.js`: `autoDeliver()` richiede lo screenshot, inserisce il JSON e tenta una sola volta il paste del File. Non invia automaticamente il solo testo quando manca l'allegato. La preview deve essere unica, caricata e stabile per 3 secondi; il caricamento non stabilizzato entro 15 secondi termina in `ATTACHMENT_UNCERTAIN_HALT`. Una preview pronta o verificata che cambia termina nello stesso stato.

L'invio richiede la conferma locale esplicita dell'allegato. `verification=user-confirmed` non significa verifica crittografica o ricevuta del provider. Il paste sintetico resta un tentativo di compatibilita. Il codice ricontrolla sessione, composer e preview prima del click; mantiene `DRAFT_PROTECTED_HOLD`, `busy`, `autoAttempted`, `sendAttempted` e nessun retry di upload o invio incerto. Queste sono proprieta previste dal codice, non risultati appena collaudati.

Il JSON contiene `omninode_response: true` e `completed_action`; il parser dei comandi accetta solo lo schema operativo esatto. Il percorso rimane limitato allo screenshot e non costituisce controllo desktop autonomo generale.

## Rettifica delle evidenze di test

L'utente ha eseguito `node --test omniclient/extension/*.test.cjs` in `A:\omninode-clean-20261101-011658`, riportando 165 pass, 0 fail, 0 skipped e 216.6092 ms. Nell'output non compaiono i sei nuovi test di `auto-delivery.test.cjs`; non e stata fornita una verifica dello SHA locale. Questo output non valida la nuova patch automatica ne il commit `400c02c7`.

La precedente dichiarazione che i 165 test comprendessero i sei nuovi test era errata. Il file `auto-delivery.test.cjs` pubblicato con `7ce0eb6c` contiene inoltre fixture errate: manca la preparazione del record prima di diverse chiamate ad `autoDeliver()`, e il mock di invio non svuota il composer. Non e stato corretto in questa tranche, per richiesta dell'utente di non lavorare sui test.

Nessun test eseguito dall'assistente per `400c02c7`; nessun esito CI recente verificato. Nessuna certificazione di funzionamento finale.

## Prove fisiche e limiti

`e2e-image-006` resta il resoconto positivo storico del percorso assistito screenshot -> allegato Gemini -> lettura visiva, con conferma utente. Provenienza e limiti sono in `ZERO_CONTEXT_HANDOVER.md`; l'immagine originale non e versionata. Non ripetere gli ID storici come comandi live.

Non e attestata l'installazione Windows del commit `400c02c7`, il reload dell'estensione o una nuova consegna nel composer. La schermata della sessione attiva non prova il successo dell'allegato. Nessun merge o aggiornamento Oracle effettuato.

Restano aperti STOP nativo/browser bidirezionale, race fisiche, persistenza/crash senza replay, Unicode/DPI/multi-monitor, hardening Go e collaborazione con una seconda chat reale.

## Copie e accesso operativo

Copia Windows storicamente attiva: `C:\Users\ugopl\omninode-github`. Copia usata per i 165 test: `A:\omninode-clean-20261101-011658`. Allineamento C:/A:/Drive e recupero del precedente `desktop.ini` in `.git/refs` non certificati. Preservare backup, stash e branch di recupero; nessun reset distruttivo, force push o sincronizzazione di `.git` tramite Drive.

Il connettore GitHub permette modifiche al repository, non l'esecuzione sul PC Windows. La ricerca degli strumenti disponibili non ha restituito un esecutore Windows o un canale desktop utilizzabile dall'assistente. Non chiedere approvazioni per azioni locali che non si possono eseguire e non dichiararle compiute.

## Precedenza documentale

Questa rettifica prevale sulle precedenti affermazioni di `NEXT_STEPS.md` che attribuiscono alla nuova consegna automatica la validazione dei 165 test. Il codice e pubblicato; installazione e funzionamento della nuova versione non sono dimostrati.
