# Contribuire a OmniNode

Prima di modificare il progetto, leggere [README](README.md), [stato corrente](docs/CURRENT_STATUS.md), [handover](docs/ZERO_CONTEXT_HANDOVER.md), [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md).

## Regole operative

- Lavorare su un branch dedicato; non fare push diretti su `main` salvo manutenzione documentale concordata.
- Verificare HEAD, CI, modifiche locali e backup prima di ogni scrittura.
- Non presumere accessi a PC, VPS, Drive, browser o servizi remoti.
- Non ripetere azioni con esito incerto; usare ID nuovi e conservare le evidenze necessarie.
- Non pubblicare credenziali, token, log console grezzi, URL firmati o schermate private.
- Non cancellare backup, branch storici, oggetti Git o configurazioni di sicurezza.

## Cambiamenti

1. Aprire una issue o descrivere lo scopo, il perimetro e i criteri di accettazione.
2. Implementare la modifica con test appropriati.
3. Aggiornare i documenti interessati, distinguendo stato corrente, prove storiche e limiti.
4. Eseguire la CI pertinente e verificare il commit specifico.
5. Aprire una pull request con diff, motivazione, rischi e prove.

## Accettazione

Una modifica è completa quando codice, test, documentazione e limiti sono coerenti. Il successo di una CI non certifica produzione, deploy, controllo desktop reale o collaborazione AI autonoma.
