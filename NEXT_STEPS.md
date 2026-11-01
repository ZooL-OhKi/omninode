# Prossimi passi e criteri di completamento

Leggere [handover da zero](docs/ZERO_CONTEXT_HANDOVER.md), [stato](docs/CURRENT_STATUS.md), AGENTS.md e SECURITY.md. Il test immagine `e2e-image-006` è riuscito con conferme locali: non lasciarlo fra le prove ancora da eseguire. Non equivale al completamento dell’intero progetto.

## Stato raggiunto

Il commit `7ce0eb6c3a304b098d17e4ada5f8bb9cf6e90f0e` implementa la consegna automatica autorizzata one-shot nel composer Gemini.

La suite locale è stata eseguita con:

```powershell
node --test omniclient/extension/*.test.cjs
```

Esito: 165 pass, 0 fail. Sono coperti bozze, modifiche concorrenti, sessioni scadute, duplicati, upload, preview, STOP/scadenza, un solo click di invio e anti-loop.

## Ordine operativo

1. Ricaricare l’estensione non pacchettizzata in Chrome e verificare una nuova consegna automatica con ID nuovo. Accettazione: composer libero, inserimento del solo payload OmniNode, un solo invio, evidenza del messaggio uscente e `SENT_CONFIRMED`; bozze e allegati preesistenti intatti.
2. Verificare HEAD, diff e CI del branch. La baseline `9316f6b2` aveva 11 check verdi; i commit successivi vanno controllati separatamente.
3. Chiarire lo stato delle copie senza rischi: `C:` attiva, `A:` con precedente ref `desktop.ini` e allineamento non confermato. Non sincronizzare `.git` tramite Drive e non cancellare recuperi.
4. Chiudere propagazione STOP nativo/browser e race: revoca deve fermare nuove azioni e invalidare operazioni pendenti in entrambe le direzioni. Non promettere annullamento di input già consegnati al sistema operativo.
5. Revisionare e consolidare i registri di idempotenza esistenti; provare riavvio/crash senza replay di effetti incerti. Non aggiungere un altro ledger come scorciatoia.
6. Validare Unicode, DPI e multi-monitor, quindi estendere le azioni desktop nella conversazione con policy e consenso specifici.
7. Completare hardening Go e revisione dei trasporti effettivamente avviati. UI HTTP, MQTT, MCP e Native Messaging non sono intercambiabili.
8. Validare una seconda chat IA reale con consenso sui dati condivisi, un responsabile per patch e risultati correlati. Non simulare una collaborazione.

## Condizioni non negoziabili

`ATTACHMENT_UNCERTAIN_HALT` e `SEND_UNCERTAIN_HALT` sono terminali: nessun retry o secondo upload automatico. Non inferire successo dal paste, dalla sola preview locale o dal composer vuoto. Nessun segreto in Git/chat/log, nessuna shell remota arbitraria, porta pubblica, elevazione automatica o fallback plaintext. Preservare mTLS/ACL, TLS 1.3 e OpenRoot/O_EXCL.

## Quando dichiarare finito

Dimostrare, nel perimetro autorizzato, un ciclo osservazione -> azione -> risultato -> prosecuzione nella stessa chat; azioni richieste effettivamente collegate e testate; STOP/scadenza/navigazione fail-closed; duplicati e crash senza replay incerto; dati e credenziali confinati secondo policy; collaborazione IA reale se inclusa nella consegna. Documentare per requisito codice, test, prova reale e limite residuo. CI verde o un singolo screenshot non bastano. Merge, release e deploy hanno gate propri: nessuno è implicito nel completamento della documentazione.
