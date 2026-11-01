# Ripresa operativa e copie da preservare

Aggiornamento: 1 novembre 2026, sessione fino alle 03:21 CET. [Handover da zero](docs/ZERO_CONTEXT_HANDOVER.md) e [stato corrente](docs/CURRENT_STATUS.md) prevalgono sulle descrizioni operative storiche. I dettagli di backup sotto sono da preservare, non inviti a fare restore.

## GitHub e prove

Repository ZooL-OhKi/omninode, branch feature/bridge-gemini-vertical, PR #9 aperta verso ai-handover-20261015-worker2. Base handover 86fe9f2ab8805cd850bf60811de10fb813012cd5; codice/CI verificato 9316f6b2eecb252ffe7c7447549bd91a36b91a0f, 11 check success. Rileggere HEAD dopo ogni commit. Il recupero PR #8 e consolidato sul branch handover, non su main.

Il ritorno testuale e quello immagine sono stati osservati nella chat Gemini con conferme locali; e2e-image-006 e riuscito. Non attribuire all'assistente accesso fisico al PC o un contatto autonomo con Gemini. Nessun deploy e provato da questa sessione.

## Copie e backup

- Windows attiva: C:\Users\ugopl\omninode-github. Il vecchio SHA locale esplicitamente annotato ae21a159864689126ea7aa7e089fef536d72031d e storico, non certifica lo SHA attuale.
- Backup verificato dall'utente: C:\Users\ugopl\omninode-github-backup-20261016-005605, 186 file e zero fallimenti Robocopy nella prova storica.
- Copia storica: A:\omninode; backup A:\omninode-backup-20261015-223838.
- Copia A: coinvolta nell'ultimo tentativo: A:\omninode-clean-20261101-011658. Ha segnalato desktop.ini in .git/refs; riparazione e allineamento non confermati.
- Branch da preservare: local-work-20261016-005605 e backup/windows-before-sync-20261015-224242.
- Stash da cercare tramite messaggio Windows prima allineamento 20261015-224242, non mediante indice fisso.

Non uniformare queste storie con reset, force push o cancellazioni. GoogleDriveFS aveva un handle sulla copia A:. Non chiudere processi, smontare volumi, modificare permessi o cancellare oggetti Git alla cieca. Evitare la sincronizzazione diretta di .git con Drive; preferire snapshot versionati senza metadati Git.

## Ultimo tentativo di allineamento

Il primo allegato PowerShell ha fallito il parsing alle 03:18 CET: stringa con $repo: invece di ${repo}:. Il blocco non e stato eseguito. E stato rimandato il file corretto; non e arrivato un output che provi la sua esecuzione.

Lo script proposto controllava modifiche e branch, faceva backup metadata locale prima di quarantena dei soli desktop.ini riconosciuti come Windows, verificava fsck e consentiva solo fast-forward. Esportava ZIP e JSON con SHA256, lasciando drive_upload_verified=false. Queste sono intenzioni del file, non operazioni gia attestate; non e stato eseguito/testato qui con PowerShell Windows. Non e versionato nel repository.

Il target fissato era 9316f6b2eecb252ffe7c7447549bd91a36b91a0f. Nuovi commit rendono vecchio quel riferimento: non aggirare l'arresto sul remoto avanzato. Per un nuovo allineamento verificare prima HEAD e CI, preservare i recuperi e ottenere le approvazioni richieste. Un commit documentale non aggiorna automaticamente copie locali o host installati. Non dichiarare sincronizzato Drive senza verificare artefatti e hash. Non pubblicare backup .git o log console.

## VPS: storia, non salute corrente

Orchestratore omninode-orchestrator; archivista omninode-archivista-vcn. Le sorgenti /home/ubuntu/omninode erano state allineate dall'utente a 86fe9f2. Archivista esegue /opt/omninode/omniclient/omniclient con WorkingDirectory /opt/omninode/omniclient: un pull altrove non aggiorna quel binario. Non assumere accesso SSH, stato dei servizi o certificati validi. Nessun deploy o riavvio e provato da questa manutenzione.

Il report omniclient/local-verification-report.txt e evidenza storica del 15 ottobre, non un test corrente. Copilot non e una dipendenza. Conservare AGENTS.md e SECURITY.md come regole operative.
