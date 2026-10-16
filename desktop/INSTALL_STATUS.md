# Installer Windows nativo

[Stato corrente](../docs/CURRENT_STATUS.md). install_windows.py esiste ed e dry-run di default. Richiede l'ID reale dell'estensione, 32 lettere a-p; --browser seleziona chrome o edge. Solo --apply crea il runtime in LOCALAPPDATA/OmniNode/NativeHost-<browser>, installa requirements-windows.txt e registra l'host sotto HKCU per quell'utente.

L'origine consentita e esatta, senza wildcard. Sono rifiutati pairing/directory preesistenti non riconosciuti, registrazioni verso altre destinazioni e percorsi link/junction/metacaratteri dove controllati. I percorsi devono essere ASCII. Niente installazioni globali, privilegi amministrativi, servizi o modifiche firewall automatiche.

Il piano ha test unitari, non una prova di installazione Windows. Un errore puo lasciare un runtime parziale; non esiste rollback transazionale completo o garanzia contro ogni race filesystem. Nessuna installazione o attivazione desktop sul PC e dimostrata. Non richiedere token o chiavi in chat e non sostituire l'ID reale con un segnaposto.
