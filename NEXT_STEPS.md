# Prossimi passi e accettazione

Aggiornamento: 9 novembre 2026. Leggere [stato](docs/CURRENT_STATUS.md), [handover](docs/ZERO_CONTEXT_HANDOVER.md), AGENTS.md e SECURITY.md.

## Gia raggiunto

Perplexity screenshot 0014 -> movimento senza click 0015 -> immagine automatica ricevuta nel browser reale. Correzione pubblicata: 1a6ce035d814d7e6a77fcab002ab663baebdfd99. Non rifare questo test solo per ricostruire contesto.

## Ordine utile

1. Verificare HEAD e CI del commit corrente; non trasferire i 236 test storici all'ultimo commit. Nessuna reinstallazione per i documenti o per un file gia identico.
2. Consolidare una regressione del DOM allegato-fratello nel percorso reale di consegna, includendo struttura ambigua/immagine estranea. I quattro check isolati della sessione non sono nel repository. Evitare una nuova infrastruttura di test non necessaria.
3. Verificare STOP/revoca/scadenza/navigazione e race in entrambe le direzioni native/browser. Nessun nuovo effetto dopo revoca; non promettere annullamento dell'input gia consegnato al SO.
4. Revisionare i registri di idempotenza esistenti e crash/restart senza replay incerto. Non aggiungere un altro ledger come scorciatoia.
5. Estendere le sole azioni richieste: click/tastiera/hotkey non sono disponibili nel parser Perplexity corrente. Policy, consenso e prove dedicate prima di estenderlo. Poi Unicode/DPI/multi-monitor.
6. Seconda chat AI reale, incarico e risposta correlati, consenso ai dati, un responsabile per patch. I suggerimenti Gemini via copia/incolla non la sostituiscono.
7. Hardening Go/gateway e servizi remoti con prove specifiche, preservando mTLS/ACL, TLS 1.3 e confinamento workspace. Nessun deploy o riavvio implicito.

Completamento generale: matrice requisito/codice/test/prova/limite, condizioni di arresto dimostrate e azioni richieste effettivamente collegate. Un ciclo riuscito non certifica produzione, multi-IA o autonomia generale.
