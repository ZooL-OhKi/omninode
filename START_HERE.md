# Riprendere OmniNode

Leggere prima lo [stato corrente](docs/CURRENT_STATUS.md), poi [AGENTS](AGENTS.md), [sicurezza](SECURITY.md), [architettura](ARCHITECTURE.md) e codice interessato. Baseline documentale: b669ec404007e01d56b12d502887f695895a8ae1; non presumere che sia ancora HEAD.

## Obiettivo

L'assistente deve usare OmniNode dalla stessa chat web per osservare e controllare l'ambiente autorizzato, leggere risultati reali e continuare. Mouse, tastiera, schermo e chat di altre IA fanno parte del requisito; il popup non sostituisce la conversazione. Il circuito completo e ancora mancante.

## Prima di agire

Verificare strumenti disponibili, branch, SHA, differenze e CI. Leggere autonomamente e testare dove esiste un esecutore reale. Non far ripetere all'utente prove eseguibili tramite strumenti o CI. Non dichiarare accesso al PC, contatto con Gemini o esecuzione di test senza evidenze.

La PR #9 riguarda feature/bridge-gemini-vertical verso il branch handover. La UI Go HTTP e il nuovo canale nativo Python sono percorsi distinti. Il manifest 0.2.0 non carica il vecchio content.js. La presenza di un metodo MCP nel sorgente non prova che main avvii quel trasporto.

## Preservazione

Copie e backup sono riepilogati in [RESUME](RESUME.md). Non toccare A:, stash, branch di recupero o VPS per far apparire tutto allineato. Un aggiornamento GitHub non aggiorna Windows o binari installati.

Procedere per tranche coerenti, controllare contenuti pubblicati e CI; fermarsi ai gate obbligatori con destinazione e contenuto esatti. Nessun merge, deploy, force push, cancellazione o pubblicazione implicita. [Prossimi passi](NEXT_STEPS.md).
