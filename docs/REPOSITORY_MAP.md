# Mappa della repository

[Stato corrente](CURRENT_STATUS.md) e [indice completo](../INDEX.md).

| Percorso | Responsabilita |
|---|---|
| omniclient/main.go | Worker MQTT oppure UI_ONLY; verificare i rami di avvio |
| omniclient/mcp_server.go | Registro SDK MCP; non prova avvio stdio dal main |
| omniclient/cdp_agent.go, web_agent.go | Browser/CDP; contesti isolati non equivalgono al desktop utente |
| omniclient/bridge.go, ui_server.go | Bridge/UI HTTP sperimentali, distinti dal canale nativo |
| omniclient/workspace_handler.go, idempotency.go | Creazione workspace e registri da distinguere/consolidare |
| omniclient/extension/ | Manifest 0.2.0, service worker, client/broker nativi e test; adapter legacy non caricato |
| desktop/ | Primitive, host con consenso, framing, installer e preview immagini |
| node1-gateway/ | Gateway, MQTT, task, policy, audit e orchestrazione |
| deploy/ e scripts/ | Template e bootstrap, non descrizione del live corrente |
| .github/workflows/ | CI Go, gateway, estensione, desktop e fixture browser |

Le dipendenze autoritative sono go.mod e i file requirements reali. Non copiare vecchi elenchi di pacchetti o script build.sh/deploy.sh non presenti. I file di stato desktop non sostituiscono il codice o una prova Windows. Conservare test, configurazioni e prove storiche finche la loro rimozione non e revisionata.
