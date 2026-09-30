# Indice documentazione Omninode

| Documento | Contenuto |
|---|---|
| `README.md` | Panoramica, avvio locale e topologia |
| `ARCHITECTURE.md` | Componenti, flussi, contratti MQTT e limitazioni |
| `SECURITY.md` | Confini di sicurezza, hardening e incident response |
| `ROADMAP.md` | Stato degli step e backlog tecnico |
| `NEXT_STEPS.md` | Checklist operativa, test e deploy |
| `PROJECT_HANDOVER.md` | Stato del branch e istruzioni per chi prosegue |

## Percorsi principali

- Gateway: `node1-gateway/main.py`
- Dashboard: `node1-gateway/static/index.html`
- Worker browser: `omniclient/web_agent.go`, `omniclient/cdp_agent.go`
- Worker MQTT/heartbeat: `omniclient/mqtt_client.go`, `omniclient/heartbeat.go`
- WS locale: `omniclient/ws_server.go`

## Stato

Lo sviluppo e' sul branch `feature/browse-rpc-mqtt`. Il codice implementa gli Step 1-6 come base, ma l'abilitazione in produzione richiede build, test di contratto MQTT, configurazione mTLS e Cloudflare Access.