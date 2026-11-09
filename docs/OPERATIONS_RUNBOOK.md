# Runbook operativo prudente

Prima leggere [stato corrente](CURRENT_STATUS.md) e [sicurezza](../SECURITY.md). Non è autorizzato un riavvio o purge automatico perché un nodo non risponde.

1. Identificare copia, SHA, processo, servizio e concessione coinvolti. Separare sorgenti da binari realmente avviati.
2. Desktop: usare STOP locale o disconnettere la sessione autorizzata. Non ripetere un input dall’effetto incerto. Conservare solo evidenze necessarie, senza token o schermate private nei log pubblici.
3. Gateway/worker: leggere stato e log con strumenti autorizzati; verificare età dell’heartbeat e identità. Un heartbeat non prova un task riuscito.
4. Prima di restart, revoche, ripristino o modifiche di rete, ottenere approvazione e predisporre rollback. Non cancellare code o database per mascherare errori.
5. Confrontare il risultato dopo l’intervento e registrare comandi, output, codice d’uscita e commit. [Storia worker-2](WORKER2_HANDOVER.md).
