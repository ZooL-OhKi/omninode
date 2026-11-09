# Prossimi passi e accettazione

Aggiornamento: 9 novembre 2026. Leggere [stato](docs/CURRENT_STATUS.md), [handover](docs/ZERO_CONTEXT_HANDOVER.md), [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md).

## Stato raggiunto

La PR #11 è stata unita con squash su `main`. Il percorso Perplexity supporta `screenshot`, `move`, `click`, `type`, `press` e `hotkey`; il broker richiede un target confermato prima delle azioni da tastiera.

La consegna del risultato usa un solo invio, verifica il layout allegato-fratello e sfoca il composer dopo la consegna verificata. Il backend desktop conserva consenso locale, binding alla conversazione, scadenza, STOP, lock e deadline cooperativa.

## Priorità

1. Verificare HEAD e CI del commit corrente prima di ogni installazione o prova runtime.
2. Eseguire una prova `type` su una finestra esterna distinta dalla scheda Perplexity, dopo screenshot e click verificato.
3. Qualificare STOP, revoca, scadenza, navigazione e race nelle due direzioni native/browser. Nessun nuovo effetto dopo revoca; non promettere annullamento dell’input già consegnato al sistema operativo.
4. Revisionare registri di idempotenza esistenti e crash/restart senza replay incerto. Non aggiungere un altro ledger come scorciatoia.
5. Estendere le azioni solo quando richiesto, con policy, consenso e prove dedicate. Poi Unicode, DPI e multi-monitor.
6. Collaborazione AI reale solo con canale, consenso e output dimostrati; copia/incolla non è collaborazione autonoma.
7. Hardening Go/gateway e servizi remoti con prove specifiche, preservando mTLS, ACL, TLS 1.3 e confinamento workspace. Nessun deploy o riavvio implicito.

## Accettazione

Il completamento richiede una matrice requisito/codice/test/prova/limite, condizioni di arresto dimostrate e azioni richieste effettivamente collegate. Un ciclo riuscito non certifica produzione, multi-IA o autonomia generale.
