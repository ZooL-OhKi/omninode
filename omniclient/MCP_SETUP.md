# MCP: codice presente e integrazione da verificare

[Stato corrente](../docs/CURRENT_STATUS.md). Questa guida non certifica un setup Claude Desktop o una chat web funzionante.

mcp_server.go usa modelcontextprotocol/go-sdk e registra i tool nel codice. main.go, nella baseline, espone i modi worker/UI e non avvia automaticamente StartMCPStdio. Non copiare il vecchio mcp_config.json con -config, credenziali fittizie o endpoint /health, /tools e /invoke non verificati.

Prima di configurare un client ufficiale occorrono entrypoint/trasporto effettivamente avviati, discovery reale dei tool e prova sull'account concreto. Claude Desktop, Claude web, Gemini web e Perplexity web sono integrazioni distinte; la presenza del server SDK non risolve l'adapter delle chat.

Il bridge HTTP proprietario e il canale Chrome Native Messaging non diventano MCP perche trasportano JSON. Niente token nei prompt o nella repository; niente riavvii o nuove esposizioni di rete per simulare una connessione riuscita. [Architettura](../ARCHITECTURE.md).
