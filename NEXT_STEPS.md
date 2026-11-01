# Prossimi passi operativi

Leggere docs/CURRENT_STATUS.md e SECURITY.md. e2e-footer-003 e e2e-text-004 provano rispettivamente screenshot nel pannello e ritorno testuale nella chat, non ancora immagine ricevuta dal modello.

1. Provare un solo allegato screenshot dopo inserimento testo: consenso alla condivisione, singolo paste, preview stabile, conferma yes nell'input Gemini, unico invio, dettaglio visivo riconosciuto dal modello.
2. ATTACHMENT_UNCERTAIN_HALT e SEND_UNCERTAIN_HALT sono terminali: nessun retry o secondo upload. Non inferire successo da paste, preview locale o semplice composer vuoto.
3. Verificare con test automatici e prova mirata: bozza, allegati preesistenti, upload attivo/fallito, preview cambiata, STOP/scadenza/navigazione durante attese, duplicati e click unico. Distinguere conferma umana, fixture, DOM e prova reale.
4. Chiudere propagazione STOP nativo/browser, persistenza, DPI, Unicode e multi-monitor prima di ampliare il perimetro; poi seconda chat IA con consenso ai dati condivisi.

Preservare mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL e branch di recupero. Nessun merge/deploy implicito. Riparare separatamente il clone A: senza cancellazioni; non sincronizzare .git con Drive.
