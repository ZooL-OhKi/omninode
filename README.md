# OmniNode

OmniNode e il collegamento operativo fra chat web delle IA, browser/estensione, strumenti locali e rete gateway/worker. L'obiettivo e usare desktop, file e web dalla conversazione autorizzata, senza trasporto manuale di comandi o risultati. Non e un nuovo chatbot.

## Stato

Prototipo non ancora operativo dalla chat. Sono presenti core Go, gateway Python, estensione 0.2.0, primitive desktop e host Native Messaging con installer. La CI della baseline b669ec4 e verde, ma le prove browser usano fixture sintetiche: non dimostrano controllo del PC dell'utente o collaborazione reale fra IA.

Leggere [stato corrente](docs/CURRENT_STATUS.md), [ripresa](START_HERE.md), [sicurezza](SECURITY.md) e [build e test](BUILD.md). L'[indice](INDEX.md) elenca tutta la documentazione.

## Componenti

- omniclient/: worker MQTT mTLS, workspace, codice MCP/CDP e UI sperimentale.
- omniclient/extension/: popup e broker nativo; vecchio adapter automatico disabilitato.
- desktop/: strumenti Windows, consenso/STOP, framing nativo e installer per utente.
- node1-gateway/: gateway, task, policy e componenti di orchestrazione.
- deploy/ e scripts/: configurazioni e bootstrap, non prova di deploy corrente.

Nessuna porta pubblica e nessun nuovo deploy sono richiesti per lo sviluppo locale. Non riutilizzare vecchi esempi MQTT plaintext o versioni Go obsolete.

## Licenza

MIT, come dichiarato nel README precedente. Questa manutenzione non cambia la licenza.
