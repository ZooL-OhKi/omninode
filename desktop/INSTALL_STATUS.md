# Installer Windows nativo

[Stato corrente](../docs/CURRENT_STATUS.md). install_windows.py e dry-run di default. Richiede l'ID reale dell'estensione, 32 lettere a-p; --browser seleziona chrome o edge. Solo --apply crea un runtime dedicato in LOCALAPPDATA/OmniNode/NativeHost-<browser>, installa requirements-windows.txt e registra l'host sotto HKCU per quell'utente.

L'origine consentita e esatta, senza wildcard. Sono rifiutati pairing/directory non riconosciuti, registrazioni verso altre destinazioni e percorsi link/junction/metacaratteri dove controllati. I percorsi devono essere ASCII. Nessuna installazione globale, elevazione, servizio, modifica firewall o attivazione desktop automatica.

La revisione aggiunge uno smoke test Windows opt-in: esegue l'installer reale con un venv temporaneo e una chiave HKCU/Software/OmniNodeCI casuale, non con la registrazione Chrome/Edge; verifica dipendenze, manifest, launcher .cmd, framing binario, ping inattivo e rifiuto dell'origine errata. Elimina soltanto la propria chiave se il valore coincide col manifest del test. Non cattura lo schermo, non digita e non approva la UI.

Nell'ambiente dell'assistente sono passati 7 test di bootstrap con il codec reale; lo smoke Windows non e stato eseguito qui: deve essere verificato dal nuovo job CI. Anche un suo successo non prova discovery del browser Windows, consenso Tk o input fisico. Un errore d'installazione puo lasciare un runtime parziale; non esiste rollback completo o protezione certificata contro ogni race. Nessuna installazione sul PC dell'utente e stata eseguita.
