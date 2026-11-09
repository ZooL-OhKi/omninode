# Trasporto MQTT/WSS: contesto e requisiti

Aggiornamento: 16 ottobre 2026. [Stato corrente](CURRENT_STATUS.md).

Le vecchie note su porta 443, modalita legacy e WSS universale non sono la configurazione deploy/mosquitto corrente. Il file di configurazione prevede MQTT 8883 e WebSocket TLS 8443; la presenza di listener non ne prova esposizione, raggiungibilita o deploy.

Questo documento non certifica implementazioni o servizi live. Conservare le invarianti mTLS, verifica identita, ACL v1, workspace e approvazioni; non applicare configurazioni storiche come comandi di produzione.

[Versione storica completa alla baseline](https://github.com/ZooL-OhKi/omninode/blob/b669ec404007e01d56b12d502887f695895a8ae1/docs/PHASE_4_MQTT_WSS.md). Per procedere usare codice, configurazioni effettive e output delle verifiche, non il nome della fase.
