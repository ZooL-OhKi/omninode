# Configurazione Mosquitto e ACL

[Stato corrente](../../docs/CURRENT_STATUS.md). I file sono template revisionabili, non attestazione del broker live.

mosquitto.conf prevede listener MQTT 8883 e WebSocket TLS 8443, tls_version tlsv1.3, require_certificate true, use_identity_as_username true, accesso anonimo disabilitato e file password/ACL esterni. Non documentare WSS 443 o plaintext come configurazione attuale.

acl.conf assegna al gateway tasks/control in scrittura e responses/heartbeat/ack in lettura; worker-1 e worker-2 restano nei rispettivi topic omninode/v1/nodes/{node_id}/.... Servono prove negative reali per dimostrare il rifiuto del cross-talk.

Nessuna chiave o password in Git. Non copiare template, aprire porte o riavviare il broker senza approvazione, verifica certificati e piano di rollback. [Storia worker-2](../../docs/WORKER2_HANDOVER.md).
