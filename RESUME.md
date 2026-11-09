# Ripresa operativa e copie da preservare

Aggiornamento: 9 novembre 2026. Questo documento conserva informazioni di recupero e cronologia; non è un invito a fare restore. [Stato corrente](docs/CURRENT_STATUS.md) e [handover](docs/ZERO_CONTEXT_HANDOVER.md) descrivono lo stato operativo attuale.

## GitHub e prove

Repository `ZooL-OhKi/omninode`; branch di manutenzione corrente: `main`. La PR #11 è stata unita con squash nel commit `370d93cb8c24460315bc1ac38b6aead88576f748`.

Le prove storiche Gemini `e2e-image-006` e Perplexity `0014`/`0015` restano storiche. Non attribuire all’assistente accesso fisico al PC o contatto autonomo con Gemini. Nessun deploy è stato provato in quelle sessioni.

## Copie e backup

- Windows attiva: `C:\Users\ugopl\omninode-github`. Lo SHA locale storico non certifica lo SHA attuale.
- Backup verificato dall’utente: `C:\Users\ugopl\omninode-github-backup-20261016-005605`.
- Copia storica: `A:\omninode`; backup `A:\omninode-backup-20261015-223838`.
- Copia A: coinvolta nell’ultimo tentativo: `A:\omninode-clean-20261101-011658`; riparazione e allineamento non confermati.
- Branch da preservare: `local-work-20261016-005605` e `backup/windows-before-sync-20261015-224242`.
- Stash da cercare tramite messaggio Windows, non mediante indice fisso.

Non uniformare queste storie con reset, force push o cancellazioni. Non chiudere processi, smontare volumi, modificare permessi o cancellare oggetti Git alla cieca. Evitare la sincronizzazione diretta di `.git` con Drive; preferire snapshot versionati senza metadati Git.

## Allineamenti storici

Il primo script PowerShell storico fallì il parsing; il blocco non fu eseguito. Lo script successivo era una proposta, non un’operazione attestata. Il target storico `9316f6b2eecb252ffe7c7447549bd91a36b91a0f` è superato dai commit successivi.

Per un nuovo allineamento verificare prima HEAD, CI, modifiche locali e backup; preservare i recuperi e ottenere le approvazioni richieste. Un commit documentale non aggiorna copie locali o host installati. Non dichiarare Drive sincronizzato senza verificare artefatti e hash. Non pubblicare backup `.git` o log console.

## VPS: storia, non salute corrente

Orchestratore: `omninode-orchestrator`; archivista: `omninode-archivista-vcn`. Le sorgenti `/home/ubuntu/omninode` erano state allineate dall’utente a `86fe9f2`. L’archivista esegue `/opt/omninode/omniclient/omniclient` con `WorkingDirectory` `/opt/omninode/omniclient`; un pull altrove non aggiorna quel binario.

Non assumere accesso SSH, stato dei servizi o certificati validi. Nessun deploy o riavvio è stato provato in questa manutenzione. Il report `omniclient/local-verification-report.txt` è evidenza storica del 15 ottobre, non un test corrente.
