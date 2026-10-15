# OmniNode v5.0 — Milestone 2: Resiliency, Network Split & Fault Tolerance (Fase 16)

## 1. Architettura di Resilienza e Lease Management
- **Lease Expiry & Quarantena:** Ogni task assegnato a un worker possiede un lease temporale (default: 300 secondi). Se il worker non invia heartbeat o ACK entro la scadenza, il gateway attiva la quarantena del nodo, revoca il lease e inserisce il goal in coda per la riassegnazione sicura.
- **Circuit Breaker:** Monitoraggio continuo dello stato di salute per nodo e capability. Se il tasso di fallimento supera il 20% in una finestra di 5 minuti, il circuito si apre (Open State), isolando temporaneamente il nodo ed emettendo un alert di sistema.
- **QoS 1 Dedicated Handling:** Gestione rigorosa dei messaggi MQTT con QoS 1 e deduplicazione tramite ID transazione tracciati nella catena di audit.

## 2. Scenari di Test E2E Certificati
1. **Disconnessione Improvvisa di `worker-1`:** Interruzione del flusso MQTT; il gateway rileva la mancata risposta e avvia il conto alla rovescia del lease.
2. **Scadenza Lease e Quarantena:** Superamento della soglia temporale; il task viene spostato in quarantena ed evinta qualsiasi esecuzione concorrente (zero doppia esecuzione).
3. **Ritorno del Worker post-Partizione:** Riconnessione del nodo isolato; il gateway verifica lo stato crittografico e re-integra il worker solo dopo handshake mTLS valido.
4. **Duplicazione Messaggi QoS 1:** Invio ripetuto di pacchetti identici; il motore di deduplicazione scarta i duplicati registrando l'evento nell'audit log.
5. **Crash del Browser Worker / Riavvio Gateway:** Persistenza dello stato su SQLite (`goals_queue.db`); al riavvio, il gateway riprende lo stato coerente senza perdita di dati.
6. **Tentativo di Cross-Talk:** Invio di messaggi da `worker-1` verso i task di `worker-2`; il broker Mosquitto blocca la trasmissione in base alle ACL v1.
7. **Circuit Breaker Trip & Reset:** Chiusura automatica del circuito dopo la risoluzione delle anomalie e 15 minuti di stabilità.

## 3. Procedure di Backup e Restore (SQLite & Audit Chain)
- **Backup a Caldo:** Esportazione cifrata dei database operativi e della catena di audit append-only Ed25519/SHA-256 verso storage protetto.
- **Restore Protocol:** Validazione crittografica della catena di audit prima del ripristino dei database SQLite, garantendo l'immutabilità dello storico delle transazioni.