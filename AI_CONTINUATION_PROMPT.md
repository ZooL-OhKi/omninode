# Prompt di continuazione per una nuova IA

Sei una nuova IA che riprende OmniNode senza accesso alla conversazione precedente. Leggi questo file per intero prima di agire. Non inventare stato, accessi, deploy o risultati. Verifica sempre ciò che affermi.

## Missione

OmniNode collega chat web AI, estensione browser e strumenti locali per osservare e controllare un ambiente esplicitamente autorizzato, restituendo il risultato nella stessa conversazione. Non è un nuovo LLM.

Il progetto comprende:

- `omniclient/`: worker Go, MQTT, workspace, UI/bridge e idempotenza.
- `omniclient/extension/`: estensione Chrome/Edge, adapter Perplexity e broker desktop.
- `desktop/`: host Native Messaging Python, primitive Windows, consenso e preview.
- `node1-gateway/`: gateway Python, MQTT, task, policy, audit e orchestrazione.
- `deploy/` e `scripts/`: configurazioni e strumenti; non provano servizi attivi.
- `docs/`: stato corrente, handover, runbook, readiness e mappe.

## Documenti da leggere

Dopo questo file, leggi in quest’ordine:

1. [README](README.md)
2. [docs/CURRENT_STATUS](docs/CURRENT_STATUS.md)
3. [docs/ZERO_CONTEXT_HANDOVER](docs/ZERO_CONTEXT_HANDOVER.md)
4. [AGENTS](AGENTS.md)
5. [SECURITY](SECURITY.md)
6. [NEXT_STEPS](NEXT_STEPS.md)
7. [BUILD](BUILD.md)
8. [RESUME](RESUME.md)
9. [docs/OPERATIONS_RUNBOOK](docs/OPERATIONS_RUNBOOK.md)
10. [docs/PRODUCTION_READINESS](docs/PRODUCTION_READINESS.md)

Se un documento storico entra in conflitto con `README.md`, `docs/CURRENT_STATUS.md` o `docs/ZERO_CONTEXT_HANDOVER.md`, prevale quest’ultimo. Non usare una baseline storica come HEAD attuale.

## Stato corrente

Repository: `ZooL-OhKi/omninode`. Branch di manutenzione corrente: `main`.

La PR #11 è stata unita con squash nel commit `370d93cb8c24460315bc1ac38b6aead88576f748`. Il commit `6b3564a80206cf3b95550e1ec7dce97fe931ddb9` corregge il confronto della conversazione nella concessione desktop. Il commit `4da4e974c72b0c303dd2cfd93a0fce4b1bc15e60` installa Chromium per i test gateway e rende idempotente la creazione della directory Native Messaging nel test desktop.

Sul commit `4da4e974...` risultano verdi OmniNode CI #163, Desktop primitive validation #70 e Build and Release #86. `Extension validation` non è stata eseguita su quel commit: non trasferire esiti fra SHA diversi.

Il commit `6cc47a58fb5a383285e42dba1a6357e84484d5c4` aggiunge `CONTRIBUTING.md`, `CHANGELOG.md`, `.editorconfig` e `.gitattributes`. Verifica la CI specifica di quel commit prima di dichiararla verde.

## Capacità implementate

L’estensione Perplexity supporta `screenshot`, `move`, `click`, `type`, `press` e `hotkey`. Il broker richiede un target confermato da `click`, `drag` o `notepad_write` prima di `type`, `press` e `hotkey`.

La consegna del risultato inserisce JSON e allegato nel composer Perplexity, invia una sola volta e verifica la bolla uscente con il layout allegato-fratello. Dopo una consegna verificata, il composer viene sfocato.

Il backend desktop conserva consenso locale, binding alla conversazione, scadenza, STOP, lock, deadline cooperativa e fail-closed su identità o focus cambiati.

## Limiti reali

Le prove storiche riportano screenshot, movimento e azioni pointer/tastiera nel browser reale, ma non una prova di `type` sul target corretto dopo la consegna. Il click precedente e il blur del composer non certificano l’identità del controllo interno alla stessa finestra Chrome. L’attesa di 150 ms non garantisce il rendering.

Restano da qualificare:

- typing sul target corretto;
- race di focus;
- STOP, revoca, scadenza e navigazione;
- crash/restart senza replay incerto;
- Unicode, DPI e multi-monitor;
- collaborazione AI autonoma;
- servizi remoti e produzione.

La CI verde non certifica produzione, controllo desktop non sorvegliato, deploy o collaborazione AI autonoma.

## Regole non negoziabili

- Non presumere accesso a PC, VPS, Drive, browser, shell, DOM o servizi remoti.
- Non eseguire checkout, reset, installazioni, restore, deploy, riavvii o modifiche firewall senza necessità esplicita e approvazione.
- Non cancellare backup, branch storici, oggetti Git, lock, refs o configurazioni di sicurezza.
- Non ripetere un input, upload, click, invio o comando dopo un esito incerto.
- Non riutilizzare ID storici: genera sempre ID nuovi.
- Non pubblicare credenziali, token, log console grezzi, URL firmati o schermate private.
- Non trattare un heartbeat come prova di task riuscito.
- Non dichiarare sincronizzati PC, Drive o VPS senza verificare artefatti e hash.
- Non modificare `AGENTS.md` o `SECURITY.md` senza necessità esplicita, revisione e approvazione.

## Protocollo operativo

Dopo autorizzazione e aggancio, un comando è un oggetto con `request_id`, `action` e `args`.

- `screenshot`: `args` vuoto.
- `move`: richiede `x`, `y`, `observation_id` e `coord_space`.
- `click`: richiede anche `button`.
- `type`, `press` e `hotkey`: richiedono un target confermato.

Un risultato valido contiene `omninode_response=true`, `request_id` correlato, `status=ok`, `completed_action`, `execution_status`, `observation_id`, metadati temporali e geometria.

`SEND_UNCERTAIN_HALT_NO_RETRY` indica un invio tentato una volta con esito non concluso. `deliveryHalted=true` blocca nuovi comandi. Non ripetere azione, ID, upload, click o Enter per sbloccare.

## Priorità di lavoro

1. Verifica HEAD remoto, CI del commit corrente, modifiche locali e backup.
2. Esegui una prova `type` su una finestra esterna distinta dalla scheda Perplexity, dopo screenshot e click verificato.
3. Qualifica STOP, revoca, scadenza, navigazione e race nelle due direzioni native/browser. Nessun nuovo effetto dopo revoca; non promettere annullamento dell’input già consegnato al sistema operativo.
4. Revisiona registri di idempotenza esistenti e crash/restart senza replay incerto. Non aggiungere un altro ledger come scorciatoia.
5. Estendi le azioni solo quando richiesto, con policy, consenso e prove dedicate. Poi Unicode, DPI e multi-monitor.
6. Collaborazione AI reale solo con canale, consenso e output dimostrati. Copia/incolla non è collaborazione autonoma.
7. Hardening Go/gateway e servizi remoti con prove specifiche, preservando mTLS, ACL, TLS 1.3 e confinamento workspace. Nessun deploy o riavvio implicito.

## Criteri di completamento

Una funzionalità è completa solo con:

- requisito chiaro;
- implementazione collegata;
- test automatici pertinenti;
- prova reale o limite dichiarato;
- documentazione aggiornata;
- condizioni di arresto dimostrate;
- assenza di promesse non supportate.

Non dichiarare completo un ciclo basato solo su mock, fixture o CI verde. Un ciclo riuscito non certifica produzione, multi-IA o autonomia generale.

## Recuperi da preservare

Backup storici sotto `C:\Users\ugopl\AppData\Local\OmniNode\Backups\`:

- `verified-579d9b7bbaac4a8a9f4f6cf49bfffb59`
- `post-send-6a52d80defb943ac8167aa3b0fa38010`
- `attachment-dom-af496f1337bd481bb0f26b0204816264`
- `perplexity-actions-9030e142f61549c3a1dccca0f1c1ed0e`
- `perplexity-actions-252ed22643ce4a2bb1f3c76112e84b91`

Preserva anche le copie C:/A:/Drive, stash, branch e VPS descritti in `RESUME.md`. Non sincronizzare `.git` con Drive, non cancellare oggetti/lock/refs e non ripristinare backup alla cieca.

## Modalità di lavoro

Test, mock, CI, installazione e prova browser sono evidenze distinte. Non sommare conteggi storici né attribuirli a commit successivi. Fermati per consensi specifici, esiti incerti o accessi mancanti.

Nessun commit, push, merge, deploy o modifica a manifest/host senza approvazione specifica. Un consenso generale non elimina i gate degli strumenti.

## Istruzione finale

Prima di qualunque modifica, leggi i documenti indicati, verifica HEAD e CI, identifica il perimetro esatto e chiedi approvazione per azioni irreversibili. Lavora in modo incrementale, conservando le evidenze e non inventando mai uno stato non verificato.
