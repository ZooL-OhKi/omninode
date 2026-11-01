# Worker-2: evidenze storiche e ripresa

Questa nota conserva osservazioni del 15 ottobre 2026, non la salute attuale. [Stato corrente del progetto](CURRENT_STATUS.md).

Storicamente: host omninode-archivista-vcn, nodo worker-2, agente archivista; systemd active/running ed enabled, PID osservato 78577 e NRestarts=0. Connessione MQTT mTLS TLS 1.3 con verifica hostname e identita worker-2; il gateway riportava online. Questi valori non sono stati ricontrollati durante lo sviluppo desktop.

Orchestratore: omninode-orchestrator; gateway HTTP su 127.0.0.1:8000. Topic worker omninode/v1/nodes/worker-2/#. CA/certificato/chiave restano fuori da Git. Le ACL devono impedire accessi ai topic di worker-1, ma un'osservazione online non sostituisce un test negativo ACL.

Le sorgenti /home/ubuntu/omninode erano state allineate a 86fe9f2 dall'utente. Il servizio archivista usa /opt/omninode/omniclient/omniclient e WorkingDirectory /opt/omninode/omniclient: nessuna equivalenza automatica fra sorgenti e binario installato.

Da verificare con approvazione e output reali: task innocuo completo, risposta correlata, confinamento, formati heartbeat, reconnect, ACL negative e idempotenza dopo crash. Non riavviare broker/gateway/worker o modificare certificati e firewall per la sola demo locale. [Runbook](OPERATIONS_RUNBOOK.md) e [backup](../RESUME.md).
