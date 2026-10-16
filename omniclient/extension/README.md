# Estensione OmniNode 0.2.0

[Stato corrente](../../docs/CURRENT_STATUS.md). Il prodotto non e ancora operativo automaticamente dalla chat.

Il manifest carica service_worker.js, native_client.js e desktop_broker.js; il popup desktop.html gestisce selezione della conversazione, consenso host, STOP, screenshot locale e apertura di tab Gemini/Claude/Perplexity nella stessa finestra. Solo il popup e autorizzato dal broker. Aprire tab non significa leggere o inviare messaggi alle altre IA.

Non sono caricati content.js, background.js o options.*; non usare la vecchia guida omnicall o inserire token nelle opzioni come setup corrente. content.js resta necessario ai test finche non vengono migrati.

Il caricamento non pacchettizzato richiede intervento esplicito nel browser. L'host com.omninode.desktop deve essere registrato per l'ID reale dell'estensione tramite l'installer per utente; non e una funzione eseguibile da una chat priva del collegamento. [Installer](../../desktop/INSTALL_STATUS.md).

Test JS e fixture di trasporto non certificano il DOM dei provider, la fine dello streaming, l'invio di screenshot alla chat o la sessione Windows reale. Non aggirare login, CAPTCHA o restrizioni e non chiedere all'utente prove manuali ripetitive per componenti che possono essere testati in CI.
