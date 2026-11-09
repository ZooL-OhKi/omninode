# OmniNode

OmniNode collega chat web AI, estensione browser, strumenti locali e gateway/worker. Non e un nuovo LLM. Obiettivo: osservare, agire nell'ambiente autorizzato e ricevere risultati nella stessa conversazione.

## Iniziare

Leggere [START_HERE](START_HERE.md), [handover autosufficiente](docs/ZERO_CONTEXT_HANDOVER.md), [stato corrente](docs/CURRENT_STATUS.md), [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md).

Il 9 novembre 2026 e stato osservato nel browser reale Perplexity il ciclo screenshot 0014 -> movimento senza click 0015 -> nuova immagine ricevuta. Non prova autonomia desktop generale o completamento del progetto. Codice della correzione: `1a6ce035d814d7e6a77fcab002ab663baebdfd99`, branch `feature/headless-local-work`; verificare HEAD attuale. Manifest 0.3.4. CI dell'ultimo commit non verificata in questo handover.

Componenti: `omniclient/` Go; `omniclient/extension/` browser; `desktop/` Windows/Native Messaging; `node1-gateway/` gateway Python; `deploy/` e `scripts/` configurazioni, non prova di deploy.

[Indice](INDEX.md), [build](BUILD.md), [priorita](NEXT_STEPS.md), [recupero e copie](RESUME.md). Licenza MIT come dichiarata storicamente; questo aggiornamento non cambia la licenza.
