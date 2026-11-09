# OmniClient Go

[Stato corrente](../docs/CURRENT_STATUS.md), [build](../BUILD.md), [sicurezza](../SECURITY.md).

Il modulo dichiara Go 1.26.0; le dipendenze effettive includono modelcontextprotocol/go-sdk, playwright-go, Paho MQTT e SQLite. go.mod/go.sum sono autoritativi, non i vecchi elenchi mcp-go/chromedp.

main.go avvia il worker MQTT oppure UI_ONLY. La UI/proxy HTTP e il bridge workspace sperimentale non sono il canale desktop Native Messaging. Il server SDK MCP esiste nel codice ma l'avvio stdio dall'entrypoint non va presunto. Nessun endpoint /tools o /invoke e promesso da questa guida.

Il worker mantiene mTLS, verifica certificati/hostname, topic v1 e workspace. Le variabili si ricavano da main.go e WorkerConfig, usando i suffissi _CA_PATH, _CERT_PATH e _KEY_PATH effettivi. Non usare config.yaml o credenziali dei vecchi esempi come contratto.

Non esporre UI/CDP, avviare nohup o riavviare servizi per un semplice test. La CI verde non aggiorna binari installati. [Handoff](HANDOFF.md) e [distinzione MCP](MCP_SETUP.md).
