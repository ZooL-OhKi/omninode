# Stato di preparazione alla produzione

Esito: non certificato per produzione o controllo desktop non sorvegliato. [Baseline ed evidenze](CURRENT_STATUS.md).

La CI verde prova i job eseguiti sul commit indicato, non che il prodotto sia operativo, che tutto sia su main o che un'IA abbia controllato il PC. Il test nativo Linux usa una fixture e un'immagine sintetica. Mancano installazione/consenso Windows reali, ritorno automatico in chat, resilienza del desktop e collaborazione reale fra IA.

Prima di un rilascio servono revisione delle API UI e idempotenza, protezione metadati/registri, test negativi delle concessioni, stop e timeout, prove di crash senza retry pericolosi, gestione credenziali e osservabilita. Per la rete remota servono prove live di routing, ACL negative e recovery datate.

Il workflow Build and Release conserva Go 1.21 e una matrice piattaforme non equivalente a runner nativi: revisionarlo prima di main/tag. Non dedurre release o disponibilita di tutte le piattaforme dai check della PR #9. Nessun deploy, riavvio o firewall change e autorizzato da questa checklist.
