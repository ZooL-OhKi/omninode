# Stato di preparazione alla produzione

Aggiornamento: 9 novembre 2026. Esito: non certificato per produzione o controllo desktop non sorvegliato. [Stato corrente](CURRENT_STATUS.md).

La CI verde prova i job eseguiti sul commit indicato, non che il prodotto sia operativo, che tutto sia su `main` o che un’IA abbia controllato il PC. Il test nativo Linux usa fixture e immagine sintetiche. Mancano installazione/consenso Windows reali, ritorno automatico in chat, resilienza desktop e collaborazione reale fra IA.

Prima di un rilascio servono revisione delle API UI e idempotenza, protezione metadati/registri, test negativi delle concessioni, stop e timeout, prove di crash senza retry pericolosi, gestione credenziali e osservabilità. Per la rete remota servono prove live di routing, ACL negative e recovery datate.

Il workflow Build and Release conserva Go 1.21 e una matrice piattaforme non equivalente a runner nativi: revisionarlo prima di main/tag. Non dedurre release o disponibilità di tutte le piattaforme dai check della PR #11. Nessun deploy, riavvio o cambio firewall è autorizzato da questa checklist.
