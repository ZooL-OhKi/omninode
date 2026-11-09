# Handoff OmniClient

[Stato corrente](../docs/CURRENT_STATUS.md). Eliminati i vecchi valori percentuali: non dimostravano completezza dei componenti.

Il codice comprende worker MQTT, heartbeat, SDK MCP, CDP, client gateway, UI e bridge workspace. Il manifest dell'estensione sceglie invece un host desktop Python nativo. Questi percorsi non sono intercambiabili e il ciclo chat -> esecuzione -> chat non e provato.

workspace.write usa OpenRoot e O_EXCL, ma i metadati del registro sono un confine separato. WorkspaceHandler, LocalIdempotencyStore e cache del bridge vanno revisionati/consolidati: nessuna garanzia generale di exactly-once o recovery dopo crash. Non aggiungere un altro registro.

Preservare TLS 1.3 del worker, mTLS/ACL, verifica hostname e workspace. Per versioni e test usare go.mod e [BUILD](../BUILD.md). Non generare nuove chiavi, attivare endpoint o distribuire binari senza una necessita concreta e approvazione.
