# Unit systemd OmniNode

[Stato corrente](../../docs/CURRENT_STATUS.md). Le unit gateway, worker e heartbeat sono configurazioni presenti, non certificazione di esecuzione continua o deploy corrente. Non inventare un omninode-browser.service assente dall'inventario.

Prima dell'uso verificare ExecStart, WorkingDirectory, utente e file EnvironmentFile reali. Conservare segreti e chiavi fuori da Git. Un servizio active non prova un task applicativo riuscito.

Nessuna installazione, enable, restart o cambio permessi e implicito nella manutenzione della documentazione. Servono approvazione, backup, rollback ed evidenze successive. [Runbook](../../docs/OPERATIONS_RUNBOOK.md).
