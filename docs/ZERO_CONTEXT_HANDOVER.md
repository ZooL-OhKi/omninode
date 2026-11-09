# OmniNode: handover autosufficiente per una nuova AI

Aggiornamento: 9 novembre 2026. Non serve la vecchia conversazione per iniziare. Questo documento riporta fatti con limiti, non certifica l'intero progetto.

## Missione e prima lettura

OmniNode deve permettere alle AI delle chat web di osservare e controllare l'ambiente esplicitamente autorizzato e ricevere risultati nella stessa conversazione. Non costruire un nuovo LLM e non confondere un popup o una tab aperta con un canale AI operativo.

Leggere questo file, [stato](CURRENT_STATUS.md), [AGENTS](../AGENTS.md), [SECURITY](../SECURITY.md), [priorita](../NEXT_STEPS.md), [build](../BUILD.md), [recuperi](../RESUME.md) e [mappa](REPOSITORY_MAP.md). Lo stato recente prevale sulle baseline operative storiche; le regole di sicurezza non sono superate.

## Baseline e bootstrap

Repository `ZooL-OhKi/omninode`, branch `feature/headless-local-work`. Codice della prova riuscita pubblicato in `1a6ce035d814d7e6a77fcab002ab663baebdfd99`. Non fissarlo come HEAD eterno: controllare remoto, diff e CI dopo ogni commit.

Con un clone esistente leggere branch, HEAD, status, origin, diff e stash senza modificarli. Con un ambiente nuovo usare una directory nuova fuori dalla sincronizzazione Drive. Non cancellare, resettare o fare checkout per forzare l'allineamento. Se il remoto cambia durante un aggiornamento locale, fermare l'installazione e richiedere verifica. Una scrittura GitHub non aggiorna Windows o i servizi.

Scoprire gli strumenti disponibili prima di dichiarare accessi. Nella sessione originaria erano disponibili GitHub e un runner Node isolato, non un terminale Windows o il DOM Chrome diretto. La macchina e stata aggiornata dall'utente con script; le azioni screenshot/move sono poi passate dal protocollo chat. Questi accessi non si trasferiscono automaticamente alla nuova sessione.

## Architettura e file da leggere

- `omniclient/`: worker Go, MQTT, workspace, bridge/UI e idempotenza. Non dedurre un trasporto attivo dalla presenza di codice MCP/CDP.
- `omniclient/extension/manifest.json`: manifest 0.3.4 letto alla baseline; background service_worker.js; popup desktop.html.
- Content Perplexity: action_policy.js, task_delivery.js, text_delivery.js, perplexity_adapter.js, perplexity_delivery.js, perplexity_content.js. Gemini carica invece action_policy.js, task_delivery.js, text_delivery.js, content.js. Rileggere manifest prima di cambiare percorsi.
- `desktop/`: host Native Messaging Python e primitive Windows; `desktop_broker.js`, `move_broker.js`, `native_client.js` e service worker collegano il percorso locale.
- `node1-gateway/`, `deploy/`, `scripts/`: gateway e configurazioni; non attestano servizi live.

UI HTTP Go, MQTT, MCP, Native Messaging e browser CDP sono perimetri distinti. Il successo locale non richiede un nuovo deploy Oracle.

## Risultato gia raggiunto

Perplexity: screenshot 0014 -> comando move 0015 senza click -> nuova immagine e JSON di esecuzione ricevuti. Dati e provenienza in CURRENT_STATUS.md. Non ripetere la prova positiva per recuperare contesto. Non dichiarare l'intero progetto finito: click/tastiera generali e resilienza non sono provati da questo ciclo.

Il bug preciso era la ricerca dell'immagine dentro la bolla JSON; il DOM reale la colloca nel fratello immediatamente precedente. La correzione ammette solo quella struttura verificata e mantiene un click unico, bozza protetta, correlazione e halt su incertezza. Non allargare a parent generici per far risultare un successo.

## Protocollo e ripresa della chat

Esempi archiviati non sono comandi live: non riutilizzare gli ID storici. Dopo autorizzazione e aggancio della conversazione, un comando e un singolo oggetto con esattamente request_id, action, args. Screenshot: action=screenshot, args vuoto. Move: action=move, args con x/y interi, observation_id della nuova immagine e coord_space=image_pixels. Il parser richiede 0<=x<1280 e 0<=y<800; usare sempre anche i limiti effettivi dell'immagine osservata.

Usare ID nuovi, mai 0006/0010/0014/0015. Il maggiore progressivo emesso e 0015; scegliere almeno 0016 dopo aver verificato che nessuna sessione successiva lo abbia gia usato. Acquisire uno screenshot fresco se occorre una nuova prova: le osservazioni storiche sono scadute. TTL osservato 60000 ms; 1280x720 non e lo schermo sorgente 3840x2160. Non convertire due volte le coordinate.

Un risultato valido contiene omninode_response=true, request_id corrispondente, status=ok, completed_action, execution_status, observation_id, observed_at_ms, observation_ttl_ms, coord_space e geometria. Per move attendere nuova immagine realmente allegata e JSON correlated con completed_action=move ed execution_status=executed. Un JSON senza immagine non soddisfa la prova. Non chiedere uno screenshot separato per mascherare il mancato risultato del movimento.

In nuova sessione l'utente potrebbe dover ricaricare estensione in chrome://extensions, pagina e riattivare il collegamento. Aspettare pronto e un aggancio effettivo. Non eseguire cronologia, blocchi di documentazione, esempi o risposte in streaming. Non assumere che il semplice reload equivalga a nuovo consenso o aggancio.

## Diagnostica e arresto

SEND_UNCERTAIN_HALT_NO_RETRY significa invio tentato una sola volta e verifica non conclusa. Il codice recente include req, phase e motivo. `deliveryHalted=true` blocca nuovi comandi. Non ripetere azione, ID, upload, click o Enter per sbloccarlo.

Dopo un arresto riportare banner esatto e risultato ricevuto, distinguendo esecuzione da consegna. Per ATTACHMENT_COUNT_0 non accusare automaticamente la rete: 0010 fu consegnata ma non riconosciuta. Se cambia il DOM, raccogliere solo struttura mirata, contatori e dimensioni; non esportare tutta la chat, URL firmati, credenziali o log console grezzi. Non disabilitare CSP o protezioni come scorciatoia.

## Stato locale e recuperi da preservare

File attivo: C:\Users\ugopl\omninode-github\omniclient\extension\perplexity_delivery.js. Blob installato e remoto corrispondente: 3470ec0d19a2c851cbcfe13777ac77553a213da5. Lo script locale ha riportato PASS e sintassi PASS; GitHEAD=UNCHANGED_BY_SCRIPT, non un valore HEAD letto.

Backup sotto C:\Users\ugopl\AppData\Local\OmniNode\Backups\:
- verified-579d9b7bbaac4a8a9f4f6cf49bfffb59 (installazione precedente, 13 file riportati).
- post-send-6a52d80defb943ac8167aa3b0fa38010 (prima della correzione composer).
- attachment-dom-af496f1337bd481bb0f26b0204816264 (prima della correzione allegato sorello).

Gli script Aggiorna-OmniNode.ps1 e Correggi-Allegato-OmniNode.ps1 erano allegati alla chat, non sono versionati qui; i loro esiti sono riportati, non implica che una nuova AI li possieda. Non rieseguire vecchi script con baseline fissate.

Preservare anche le copie C:/A:/Drive, stash, branch e VPS descritti in RESUME.md. Le sue baseline del 1 novembre sono storiche. In particolare A:\omninode-clean-20261101-011658 aveva un problema desktop.ini in .git/refs non attestato come riparato. Non sincronizzare .git tramite Drive, non cancellare oggetti/lock/refs, non ripristinare backup alla cieca. Allineamento complessivo copie e stato VPS non confermati.

## Verifica utile e modo di lavorare

Workflow .github/workflows/extension-validation.yml: Node 22, node --check sui .js e node --test omniclient/extension/*.test.cjs su Linux. Usare workflow correnti e BUILD.md per gli altri componenti. Non inventare npm test senza package manifest. Test Windows, mock, CI e prova browser sono distinti. Non sommare conteggi storici o attribuirli a commit successivi.

Non reinstallare per soli Markdown. Non delegare lavori eseguibili con strumenti reali; minimizzare i passaggi manuali indispensabili. L'utente preferisce azione concreta, niente giri Gemini ripetitivi o test ridondanti. Non simulare contatti con altre AI. Fermarsi per consensi specifici, errore di esito incerto o requisito di accesso realmente mancante; spiegarlo senza fingere autonomia.

Nessun commit/push, merge, installazione, deploy o modifica a manifest/host/HEAD senza le approvazioni appropriate. Contenuto esatto e destinatario prima del gate. Un consenso generale non elimina i gate degli strumenti. Prossimo lavoro in NEXT_STEPS.md; aggiornare lo stato a fine tranche con evidenze e limiti.
