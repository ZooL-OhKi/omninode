# Architettura corrente e obiettivo

Stato e limiti: [CURRENT_STATUS](docs/CURRENT_STATUS.md). Non usare i vecchi diagrammi MQTT plaintext o le liste browser_* come contratto corrente.

## Percorsi distinti

1. Estensione 0.2.0: popup -> service_worker.js -> DesktopBroker -> NativeClient -> host Python via stdin/stdout -> concessione locale -> primitive Windows. Non passa attualmente attraverso il core Go. Le pagine web non sono chiamanti autorizzati del broker.
2. Core Go: main avvia worker MQTT oppure UI_ONLY; UI/proxy e bridge HTTP sono sperimentali. WorkspaceHandler crea file nuovi con OpenRoot/O_EXCL. Il bridge ha una cache aggiuntiva in memoria da consolidare e hardenizzare.
3. Rete remota: gateway Python, Mosquitto e worker Go con identita, certificati e topic omninode/v1/nodes/{node_id}/tasks|responses|heartbeat|control|control/ack. Le configurazioni non provano il servizio live.
4. Codice MCP/CDP: server SDK e sessioni browser presenti; registrazione dei tool, entrypoint e trasporto vanno controllati nel codice. JSON-RPC proprietario e Native Messaging non sono automaticamente MCP.

## Collegamento mancante

La conversazione autorizzata deve diventare l'interfaccia di controllo con richieste complete e provenienza verificata, screenshot/risultati correlati e continuazione automatica senza toccare bozze. Il collegamento chat -> desktop e l'integrazione del percorso nativo con le policy del core restano aperti.

Il coordinatore multi_ai_coordinator.py gestisce proposte e blocchi di file; un booleano tests_passed non e prova di test. Aprire tab non dimostra collaborazione fra IA. PWA e popup restano accessori; non servono gRPC, GraphQL, Kubernetes o un nuovo LLM per chiudere la verticale.
