# Phase 4 — MQTT over WSS & Versioned Topics (Swarm Fabric v5.0)

## Architettura e Trasporto
- **Topic Versionati:** Supporto per i topic isolati per-nodo (`omninode/v1/nodes/{node_id}/tasks`, `responses`, `heartbeat`) accanto alla modalità `legacy`.
- **Configurazione Dual-Topic:** Gestita tramite la variabile d'ambiente `OMNINODE_MQTT_TOPIC_VERSION=v1|legacy` con controllo fail-fast all'avvio.
- **Envelope Canonico:** Obbligo di `schema_version: 1`, `message_id` (UUID v4) per l'idempotenza e validazione rigorosa del `node_id` rispetto all'identità MQTT autenticata per prevenire spoofing e violazioni ACL.
- **Trasporto WSS & Resilienza:** Client Go e Gateway configurati con trasporto WebSocket Secure (`wss://.../mqtt` su porta 443), Keep-Alive a 30s per evitare timeout di Cloudflare, e riconnessione con backoff esponenziale e jitter.
- **ACL Mosquitto:** Isolamento rigoroso per identità; ciascun client può pubblicare o sottoscrivere esclusivamente sui topic di propria competenza.