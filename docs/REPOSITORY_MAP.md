# Mappa della repository

Aggiornamento: 9 novembre 2026. [Stato corrente](CURRENT_STATUS.md) e [indice](../INDEX.md).

| Percorso | Responsabilità |
|---|---|
| `omniclient/main.go` | Worker MQTT oppure `UI_ONLY`; verificare i rami di avvio |
| `omniclient/mcp_server.go` | Registro SDK MCP; non prova avvio stdio dal main |
| `omniclient/cdp_agent.go`, `web_agent.go` | Browser/CDP; contesti isolati non equivalgono al desktop utente |
| `omniclient/bridge.go`, `ui_server.go` | Bridge/UI HTTP sperimentali, distinti dal canale nativo |
| `omniclient/workspace_handler.go`, `idempotency.go` | Creazione workspace e registri da distinguere/consolidare |
| `omniclient/extension/` | Manifest 0.3.4, service worker, adapter Perplexity, broker nativi e test |
| `desktop/` | Primitive, host con consenso, framing, installer e preview immagini |
| `node1-gateway/` | Gateway, MQTT, task, policy, audit e orchestrazione |
| `deploy/` e `scripts/` | Template e bootstrap; non descrizione del live corrente |
| `.github/workflows/` | CI Go, gateway, estensione, desktop e fixture browser |

Le dipendenze autoritative sono `go.mod` e i file `requirements` reali. Non copiare vecchi elenchi di pacchetti o script build/deploy non presenti.

I file di stato desktop non sostituiscono codice o prova Windows. Conservare test, configurazioni e prove storiche finché la loro rimozione non è revisionata.
