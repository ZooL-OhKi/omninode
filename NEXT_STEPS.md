# Prossimi passi e criteri di completamento

Leggere [handover da zero](docs/ZERO_CONTEXT_HANDOVER.md), [stato](docs/CURRENT_STATUS.md), AGENTS.md e SECURITY.md. Il test immagine e2e-image-006 e riuscito con conferme locali: non lasciarlo fra le prove ancora da eseguire. Non equivale al completamento dell'intero progetto.

## Ordine operativo

1. Verificare HEAD, diff e CI del branch feature/bridge-gemini-vertical. La baseline 9316f6b2 aveva 11 check verdi; controllare i commit successivi separatamente. Individuare un esecutore reale prima di promettere test o azioni Windows.
2. Chiarire lo stato delle copie senza rischi: C: attiva, A: con precedente ref desktop.ini e allineamento non confermato. Il primo script non ha superato il parsing; quello corretto non ha un risultato attestato e punta alla vecchia baseline. Non sincronizzare .git tramite Drive e non cancellare recuperi.
3. Verificare con test automatici bozza, allegati preesistenti, upload attivo/fallito, preview cambiata, STOP/scadenza/navigazione durante attese, duplicati e click unico. Prova reale mirata soltanto per un requisito non coperto o una modifica che la renda necessaria.
4. Chiudere propagazione STOP nativo/browser e race: revoca deve fermare nuove azioni e invalidare operazioni pendenti. Provare entrambe le direzioni, scadenza e navigazione; non promettere annullamento di input gia consegnati al sistema operativo.
5. Revisionare e consolidare i registri di idempotenza esistenti; progettare e provare riavvio/crash senza replay di effetti incerti. Non aggiungere un altro ledger come scorciatoia.
6. Validare Unicode, DPI e multi-monitor, quindi estendere le azioni desktop nella conversazione con policy e consenso specifici. Le primitive presenti nel codice non sono automaticamente esposte o collaudate nel percorso chat.
7. Completare hardening Go e revisione dei trasporti effettivamente avviati. UI HTTP, MQTT, MCP e Native Messaging non sono intercambiabili.
8. Validare una seconda chat IA reale con consenso sui dati condivisi, un responsabile per patch e risultati correlati. Non simulare una collaborazione.

## Condizioni non negoziabili

ATTACHMENT_UNCERTAIN_HALT e SEND_UNCERTAIN_HALT sono terminali: nessun retry o secondo upload automatico. Non inferire successo dal paste, dalla sola preview locale o dal composer vuoto. Nessun segreto in Git/chat/log, nessuna shell remota arbitraria, porta pubblica, elevazione automatica o fallback plaintext. Preservare mTLS/ACL, TLS 1.3 e OpenRoot/O_EXCL.

## Quando dichiarare finito

Dimostrare, nel perimetro autorizzato, un ciclo osservazione -> azione -> risultato -> prosecuzione nella stessa chat; azioni richieste effettivamente collegate e testate; STOP/scadenza/navigazione fail-closed; duplicati e crash senza replay incerto; dati e credenziali confinati secondo policy; collaborazione IA reale se inclusa nella consegna. Documentare per requisito codice, test, prova reale e limite residuo. CI verde o un singolo screenshot non bastano. Merge, release e deploy hanno gate propri: nessuno e implicito nel completamento della documentazione.
