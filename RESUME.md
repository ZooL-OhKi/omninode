# Ripresa operativa e copie da preservare

Riferimento: 16 ottobre 2026, codice b669ec404007e01d56b12d502887f695895a8ae1. Per capacita e CI usare lo [stato corrente](docs/CURRENT_STATUS.md); i precedenti conteggi locali non descrivono i commit successivi.

## Stato di ripresa

Branch feature/bridge-gemini-vertical, PR #9 non integrata al controllo di baseline. Base handover: 86fe9f2ab8805cd850bf60811de10fb813012cd5. Il recupero PR #8 e consolidato sul branch handover, non su main. Non eliminare local-work-20261016-005605 e non uniformarne la storia con reset o force push.

Sono presenti estensione, bridge HTTP e host desktop nativo. Il file tool Go ora usa creazione esclusiva e OpenRoot: le vecchie affermazioni su os.WriteFile/sovrascritture erano superate. Questo non rende sicuri tutti i metadati o tutte le API. Il ritorno automatico nella chat reale resta non dimostrato.

## Copie e backup

- Copia Windows attiva: C:\Users\ugopl\omninode-github; modulo omniclient. Ultimo SHA locale esplicitamente mostrato nella sessione: ae21a159864689126ea7aa7e089fef536d72031d. Gli aggiornamenti successivi del PC non sono certificati da questa nota.
- Backup verificato dall'utente: C:\Users\ugopl\omninode-github-backup-20261016-005605, 186 file e zero fallimenti Robocopy.
- Copia storica: A:\omninode; backup A:\omninode-backup-20261015-223838.
- Branch di sicurezza: backup/windows-before-sync-20261015-224242. Stash da cercare tramite messaggio Windows prima allineamento 20261015-224242, non tramite indice fisso.

GoogleDriveFS aveva un handle sulla copia A:. Non chiudere Drive, smontare volumi, cambiare permessi o cancellare oggetti Git alla cieca. La condivisione con Gemini e voluta, ma non prova sincronizzazione o accesso shell.

## VPS: storia, non salute attuale

Orchestratore omninode-orchestrator; archivista omninode-archivista-vcn. Le sorgenti /home/ubuntu/omninode erano state allineate dall'utente a 86fe9f2. Archivista esegue /opt/omninode/omniclient/omniclient con WorkingDirectory /opt/omninode/omniclient: un pull altrove non aggiorna quel binario. Nessun deploy o riavvio e provato da questa manutenzione.

Il report omniclient/local-verification-report.txt e un'evidenza storica del 15 ottobre, non il risultato corrente. Copilot non e una dipendenza. Nessun contatto diretto con Gemini e stato dimostrato. [Regole operative](AGENTS.md).
