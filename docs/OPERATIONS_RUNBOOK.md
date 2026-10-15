# OMNINODE SWARM FABRIC — OPERATIONS RUNBOOK (Fase 13)

## 1. Worker non risponde
- Verificare heartbeat age tramite API `/api/v1/fleet/nodes`.
- Riavviare il worker in Go tramite system service o container.

## 2. Circuit Breaker Aperto
- Ispezionare la telemetria per identificare la capability o il nodo instabile.
- Eseguire il purge delle code orfane e forzare il reset del circuit breaker solo dopo verifica dei test.

## 3. Backup e Restore SQLite
- Eseguire il backup a caldo tramite `BackupManager.create_sqlite_backup()`.
- Verificare l'integrità della catena di audit prima di ogni operazione di restore.