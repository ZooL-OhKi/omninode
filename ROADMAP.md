# Roadmap basata su evidenze

Aggiornamento: 9 novembre 2026. Nessuna percentuale o data di rilascio certificata. [Stato](docs/CURRENT_STATUS.md), [ordine operativo](NEXT_STEPS.md).

| Area | Evidenza attuale | Residuo |
|---|---|---|
| Perplexity locale | Screenshot 0014, move senza click 0015 e immagine ricevuta; manifest 0.3.4 | Regressione DOM integrata, robustezza e condizioni di arresto |
| Desktop | Installazione della correzione locale e ciclo pointer osservati | Click/tastiera da chat, Unicode/DPI/multi-monitor e policy complete |
| Native Messaging | Usato nel percorso locale; codice e test presenti | STOP bidirezionale, race e crash/replay da qualificare |
| Gemini | Prova assistita storica e2e-image-006 | Nuova autonomia non dimostrata dalla prova Perplexity |
| Multi-AI | Suggerimenti scambiati tramite utente | Collaborazione autonoma reale non dimostrata |
| Go/gateway/rete | Codice e configurazioni presenti, evidenze storiche | Hardening e salute/deploy live da verificare separatamente |

Non introdurre un nuovo LLM o deploy distribuiti per risolvere il percorso locale. Nessun successo locale implica produzione pronta.
