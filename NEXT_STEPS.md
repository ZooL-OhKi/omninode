# Prossimi passi operativi

Riferimento: [stato corrente](docs/CURRENT_STATUS.md). Non riaprire task storici gia risolti sulla base di vecchi conteggi o branch.

1. Collegare questa conversazione autorizzata al broker nativo, con provenienza della richiesta, fine risposta affidabile e rifiuto di esempi/cronologia.
2. Restituire automaticamente risultati e immagini nella stessa chat, correlati alla richiesta, senza alterare bozze o avviare loop illimitati.
3. Verificare installer e host Windows reali, consenso, STOP, disconnessione e scadenza; calibrare coordinate/DPI e documentare gli effetti parziali senza retry di input.
4. Dimostrare una sola azione innocua completa prima di ampliare il perimetro. Per workspace.write: duplicato senza nuova scrittura, conflitto di payload e rifiuto non autorizzato.
5. Aggiungere coordinamento reale con una seconda chat IA, consenso ai dati condivisi e un solo responsabile per ogni file.

Hardening ancora aperto: API/bind/origini UI Go, metadati workspace e idempotenza concorrente/crash-safe, Unicode e multi-monitor, audit del percorso desktop. Non usare VPS, nuovi protocolli o nuove roadmap per rinviare il circuito locale. Nessun merge/deploy solo per dichiarare tutto allineato.
