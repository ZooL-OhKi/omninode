# Stato corrente OmniNode

Aggiornamento: 9 novembre 2026. Fonte operativa per lo stato; AGENTS.md e SECURITY.md restano normativi. Le vecchie descrizioni screenshot-only/non operativo e i vecchi branch non prevalgono su questo stato.

## Versioni e ambienti distinti

- Repository: ZooL-OhKi/omninode; branch `feature/headless-local-work`.
- Ultimo commit codice verificato prima di questo aggiornamento documentale: `1a6ce035d814d7e6a77fcab002ab663baebdfd99`. Rileggere HEAD: il commit dei documenti sara successivo.
- File: `omniclient/extension/perplexity_delivery.js`; blob remoto `3470ec0d19a2c851cbcfe13777ac77553a213da5`, identico all'InstalledBlob riportato dall'utente Windows.
- Installazione locale: `C:\Users\ugopl\omninode-github\omniclient\extension\perplexity_delivery.js`; aggiornamento e sintassi PASS riportati dall'utente. HEAD locale non letto; non equipararlo al commit sorgente.
- Manifest letto: 0.3.4; nessuna modifica a manifest o host nativo nella correzione.

## Evidenze e provenienza

Resoconto della sessione Perplexity del 9 novembre, non log grezzi o immagini versionate nel repository:

| ID | Osservazione | Limite |
|---|---|---|
| 0006 | Consegna screenshot automatica confermata dall'utente nella sessione precedente | Non prova il movimento |
| 0010 | Immagine e JSON ricevuti; halt `req=omni-screenshot-0010:phase=post_click:ATTACHMENT_COUNT_0` | Falso negativo della verifica allegato |
| 0014 | Immagine screenshot 1280x720 e JSON correlato ricevuti | Osservazione iniziale |
| omni-move-0015 | JSON `completed_action=move`, `execution_status=executed`, observation_id corrispondente e nuova immagine ricevuti, senza screenshot separato | Singola prova nel browser reale, non controllo generale |

0014 observed_at_ms=1794221565085; 0015 observed_at_ms=1794221576551; TTL 60000 ms; coord_space=image_pixels; immagini 1280x720; sorgente 3840x2160. Movimento richiesto (920,350), senza click, riferito a 0014. Le immagini erano allegate alla conversazione; non sono incluse in Git e questo resoconto non e una ricevuta server indipendente.

## Causa e correzione

DOM fornito dall'utente: parent immediato `flex ... flex-col gap-1`, con due figli diretti: contenitore allegati `flex ... flex-wrap ...`, poi bolla `group/user-bubble` con JSON. L'immagine caricata e sorella della bolla, non sua discendente.

`abe5c7914fed4c92a69124f8582af81f434fe96d` (PR #10 squash) gestisce composer sostituito e diagnostica post-click, ma non bastava. `1a6ce035...` limita la ricerca al contenitore allegati fratello nella struttura verificata: due figli, bolla unica, nessun composer/risposta assistente nel contenitore. Un solo tentativo di invio; non cerca immagini in antenati generici. Layout differente -> halt, non successo presunto.

## Test: non sommare evidenze diverse

236 pass erano stati riportati per la precedente installazione da `31eb38e0eded706e74f5aa1ae40a0b98c8a43c62`, non per l'ultimo commit. I due check adapter-tests della PR #10 sono stati osservati success. Quattro verifiche isolate della guardia strutturale sono passate nell'ambiente Node dell'assistente; non sono la suite completa e non sono state aggiunte al repository. CI completa del commit `1a6ce035...`: non verificata in questa sessione. La prova browser 0014 -> 0015 e distinta da queste esecuzioni.

## Residui

Ciclo pointer osservato riuscito; non qualificati in questa sessione: STOP/race completi, crash e replay, tastiera/click da chat, Unicode/multi-monitor, collaborazione AI autonoma, servizi remoti e produzione. Seguire NEXT_STEPS.md. Non reinstallare il file gia corrispondente solo per i documenti.
