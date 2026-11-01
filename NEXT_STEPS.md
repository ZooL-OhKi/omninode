# Prossimi passi e criteri di completamento

Leggere [stato corrente](docs/CURRENT_STATUS.md), [handover](docs/ZERO_CONTEXT_HANDOVER.md), AGENTS.md e SECURITY.md.

## Baseline

ee7565746809147cecb1be2dd91990ce127d56f7, estensione 0.3.1: 11 check GitHub completed/success al controllo della sessione. Questo commit documentale e successivo e non eredita automaticamente quei risultati. PR #9 aperta, non mergiata.

## Prossimo intervento utile

1. Preparare la distribuzione locale coerente di sorgenti nativi e file estensione, inclusi notepad_task.py e task_delivery.js, dopo verifica degli effettivi percorsi installati, delle modifiche locali e dei backup. Non riusare il vecchio updater fissato a 54d5dda5. Non cambiare ID/origine dell'estensione, registro, venv o dipendenze senza motivo e approvazione specifica.
2. Eseguire una sola prova fisica mirata del compito delimitato: screenshot recente -> notepad_write con testo esatto e share_result:true -> unico OK locale sul compito -> click e digitazione -> risultato e immagine inviati automaticamente. Conservare ID, versione installata, esito e limite. Verificare il testo nell'immagine, non soltanto status executed.
3. Verificare gli arresti realmente non coperti: bozza/allegato presenti, preview differente o non leggibile, STOP/scadenza durante attese, cambio bersaglio/focus e disconnessione. Nessuna ripetizione di effetti incerti. Usare sandbox e CI per i casi eseguibili autonomamente; non riversare tutta la suite sull'utente.
4. Rendere verificabili STOP nativo -> browser e browser -> nativo, anche durante input e consegna; non promettere di annullare input gia ricevuti dal sistema operativo.
5. Revisionare i registri di idempotenza esistenti e provare crash/restart senza replay di input o invii incerti. Non aggiungere un ledger parallelo come scorciatoia.
6. Validare DPI, Unicode, privilegi applicativi e focus sul Windows fisico. Multi-monitor non e completato: il percorso attuale e limitato al display primario.
7. Ampliare l'autonomia tramite concessioni per obiettivo, risorse, azioni e durata. Non rimuovere globalmente i gate: il compito Blocco note non autorizza acquisti, messaggi, installazioni o modifiche ad altri file/applicazioni.
8. Verificare hardening Go e trasporti effettivamente avviati prima di distribuzioni Oracle. Preservare mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL; nessuna shell arbitraria o porta pubblica non protetta.
9. Collegare una seconda IA tramite un canale reale autorizzato, solo dopo il ciclo locale utile; la revisione Gemini inoltrata dall'utente non prova orchestrazione automatica.

## Evidenze da non confondere

Il resoconto e2e-image-006 e le schermate successive attestano singole consegne assistite, non il nuovo compito autonomo. I 165 test locali storici non validano la nuova patch; le fixture errate furono corrette. I 30 test Python, 6 helper e 12 Node eseguiti dall'assistente hanno perimetri diversi, descritti nello stato. Non sommarli per dichiarare una suite end-to-end.

CI verde, file copiati, processo caricato, input fisico e risultato letto dal modello sono evidenze distinte. Dichiarare completato solo il requisito effettivamente dimostrato. Merge, release, modifiche dei servizi, allineamento C:/A:/Drive e deploy hanno gate separati.
