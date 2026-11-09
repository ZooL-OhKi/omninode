# Stato integrazione browser nativa

[Stato corrente](../docs/CURRENT_STATUS.md). L'estensione 0.2.0 carica service_worker.js, native_client.js e desktop_broker.js. Permessi: activeTab, tabs, nativeMessaging; nessun host HTTP, clipboard, token storage o content script automatico nel manifest.

Solo il popup puo selezionare la conversazione, richiedere consenso locale, fermare, mostrare una preview e aprire tab IA nella stessa finestra. Navigazione/chiusura della scheda di controllo revocano la sessione. Il badge puo restare obsoleto dopo STOP locale fino alla risposta/disconnessione successiva.

Test JS e avvio worker sono verificati; [CI nativa](CI_NATIVE_DIAG.md) prova un diverso host fixture. Non sono verificati popup/consenso Windows reali, invio automatico alla chat o collaborazione fra IA. L'installer ora esiste, ma non e stato eseguito sul PC dall'assistente. I vecchi background.js/content.js/options restano file legacy, non percorsi attivi.
