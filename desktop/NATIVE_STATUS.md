# Host Native Messaging

[Stato corrente](../docs/CURRENT_STATUS.md). Canale stdin/stdout JSON con lunghezza prefissata, input massimo 128 KiB e output 1 MiB; non e un endpoint MCP o HTTP.

native_host.py verifica origine browser/OMNINODE_NATIVE_ORIGIN, richiede un primo messaggio open con conversazione e consenso locale. Le azioni hanno session_id, sequence, action e args. La sequenza e consumata prima dell'effetto: dopo errore o timeout non ripetere input automaticamente. La credenziale desktop resta nel processo host.

Installer e client browser ora sono presenti. STOP/disconnessione/scadenza devono revocare gli input successivi, ma non annullano eventi consegnati; rilevamento di disconnect durante chiamate OS bloccanti non e immediato. [Preview](SCREEN_STATUS.md) gestisce il limite del messaggio.

I test di protocollo e la fixture Chromium sono verificati, non consenso o pipe Windows reali. Il percorso non e ancora utilizzabile automaticamente da questa conversazione. Nessuna modifica a MQTT o al workspace Go consegue alla presenza del canale nativo.
