# Sicurezza OmniNode

Questa e una policy normativa, non una certificazione che ogni requisito sia gia implementato. Consultare [stato e limiti](docs/CURRENT_STATUS.md) prima di esporre o attivare componenti.

## Invarianti da preservare

- Identita e autorizzazioni esplicite, privilegi minimi, risorse e scadenze limitate.
- MQTT mTLS, verifica CA/hostname/certificato, worker Go TLS 1.3 senza fallback plaintext; InsecureSkipVerify non va attivato.
- ACL Mosquitto per identita e topic v1 per nodo. Non sostituire le ACL con wildcard globali.
- Gateway, UI e CDP non devono essere esposti pubblicamente. Nessun tunnel come scorciatoia per evitare autenticazione. Le API UI Go e il loro bind configurabile richiedono ancora revisione.
- Nessun segreto in Git, chat, DOM del provider o log. Le credenziali del desktop rimangono nel processo host; non riutilizzare token pubblicati in chat.
- Workspace remoto confinato e creazione esclusiva per workspace.write; metadati, link, alias e registri richiedono verifica separata. OpenRoot non certifica ogni accesso al filesystem.
- Nessuna shell arbitraria nel worker. Nessuna elevazione automatica del desktop o modifica implicita di firewall, certificati e servizi.

## Desktop e browser

La concessione desktop e distinta dalla capability di scrittura nel workspace: il desktop puo interagire con applicazioni e file dell'utente e non e una sandbox filesystem. Richiede consenso locale, conversazione identificata, scadenza, stop visibile e conferme appropriate per effetti sensibili. Non concederla per il solo testo prodotto da una pagina o da un'altra IA.

Il broker 0.2.0 accetta soltanto il popup dell'estensione; non e ancora disponibile un adapter automatico di chat validato. Origine esatta dell'estensione e framing nativo non sostituiscono l'autorizzazione della conversazione. Non eseguire esempi, cronologia precedente o risposte in streaming; preservare bozze e correlazione dei risultati.

STOP e fail-safe non annullano input gia consegnati al sistema operativo. Non ripetere automaticamente clic/tasti dopo un timeout o un crash dall'effetto incerto. Il rilascio di tasti/pulsanti e tentato, non garantito contro ogni guasto. Unicode, DPI e multi-monitor sono limiti aperti. Nessun bypass di login, CAPTCHA o restrizioni dei servizi.

## Incidenti e manutenzione

Fermare la sessione autorizzata, preservare evidenze senza diffondere segreti, identificare l'ambito e ottenere approvazione prima di revoche, riavvii, restore o cambi di rete. Non proporre pkill, purge delle code, reset o firewall globali come primo rimedio. Rotazioni e recuperi richiedono un piano specifico e rollback.

Audit verificabile, protezione dei registri e resilienza sono requisiti da collaudare, non proprieta dimostrate da un titolo. Una scansione verde non garantisce assenza totale di segreti o sicurezza completa. [Runbook](docs/OPERATIONS_RUNBOOK.md).
