# Riprendere OmniNode da zero

Aggiornamento: 1 novembre 2026, sessione fino alle 03:21 CET. Non serve la conversazione precedente: iniziare da [handover completo](docs/ZERO_CONTEXT_HANDOVER.md).

## Ordine di lettura

1. [Handover da zero](docs/ZERO_CONTEXT_HANDOVER.md): obiettivo, bootstrap, prove, problemi, priorita e completamento.
2. [Stato corrente](docs/CURRENT_STATUS.md): fonte operativa per capacita e limiti.
3. [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md): regole normative, da preservare.
4. [RESUME](RESUME.md): copie, recuperi, branch e VPS.
5. [BUILD](BUILD.md), [mappa](docs/REPOSITORY_MAP.md), codice e workflow della tranche.
6. [NEXT_STEPS](NEXT_STEPS.md): verifiche residue e ordine del lavoro.

## Obiettivo e baseline

Rendere le IA delle chat web operative sull'ambiente esplicitamente autorizzato tramite OmniNode: osservare lo schermo, usare mouse e tastiera, leggere risultati reali, continuare nella stessa conversazione e collaborare con altre IA tramite canali reali. Non costruire un LLM sostitutivo e non confondere un popup con la chat.

Repository ZooL-OhKi/omninode; branch feature/bridge-gemini-vertical; PR #9 verso ai-handover-20261015-worker2, aperta all'ultimo controllo. Baseline codice e CI verificata: 9316f6b2eecb252ffe7c7447549bd91a36b91a0f. Questo aggiornamento documentale e successivo: rileggere HEAD e CI, non fissare la baseline come HEAD corrente.

La prova e2e-image-006 ha completato il circuito screenshot Windows -> allegato nella chat Gemini -> descrizione visiva, con conferme locali. Non prova controllo desktop completo, autonomia, persistenza o deploy. Le evidenze e i loro limiti sono nell'handover.

## Prima di agire

Scoprire gli strumenti realmente disponibili; verificare branch, SHA, diff e CI. Eseguire autonomamente cio che l'esecutore disponibile consente. Non dichiarare accesso al PC, esecuzione di test o contatto con altre IA senza evidenze. Nessun lavoro in background inventato.

Preservare copie, stash, branch di recupero e VPS. Un commit GitHub non aggiorna Windows, runtime installati o Drive. Nessun reset distruttivo, force push, cancellazione, merge o deploy implicito. Fermarsi alle approvazioni specifiche con target e contenuto esatti.
