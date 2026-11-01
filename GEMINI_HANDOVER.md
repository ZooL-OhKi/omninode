# Collaborazione con Gemini

Obiettivo: usare la vera chat web autorizzata, non sostituire Gemini con un'altra IA o un'API diversa. Leggere [handover da zero](docs/ZERO_CONTEXT_HANDOVER.md) e [stato corrente](docs/CURRENT_STATUS.md).

Il 1 novembre 2026 la prova utente e2e-image-006 ha mostrato screenshot allegato alla conversazione, risultato JSON correlato, stato SENT_CONFIRMED — ATTACHMENT_VERIFIED (conferma utente) e risposta Gemini con dettagli visivi. E una prova assistita nel contesto della sessione, non un canale autonomo permanente o una ricevuta server. Il resoconto e conservato nella repo; l'immagine originale della chat non e versionata.

Non ripetere il request_id della prova come comando live. Per nuove prove ottenere prima la concessione locale, usare un nuovo ID e un solo comando per turno. Non mescolare il comando immediato con istruzioni per il risultato del turno successivo. Non eseguire esempi o cronologia preesistente all'attivazione. Non fare retry dopo ATTACHMENT_UNCERTAIN_HALT o SEND_UNCERTAIN_HALT.

Aprire una tab non prova l'invio di un incarico, la ricezione di una risposta o una collaborazione multi-IA. Per ogni contributo richiedere copia e SHA, contenuto/diff, comandi effettivamente eseguiti, output e codice d'uscita. Separare implementato, proposto, simulato e osservato. Un responsabile per patch/file; niente scritture concorrenti non coordinate.

La copia Windows attiva e C:\Users\ugopl\omninode-github. A:\omninode e storica; A:\omninode-clean-20261101-011658 ha un problema Git precedente non attestato come risolto. Nessun vecchio checkout, merge o pulizia alla cieca. Allineamento e recuperi in RESUME.md.

Il vecchio adapter omnicall/content.js non va confuso con la tranche screenshot della versione 0.2.1: rileggere il manifest corrente e i file caricati. Le note precedenti su 0.2.0 o su chat non ancora provata sono storiche dove superate da CURRENT_STATUS.md. Native Messaging e bridge HTTP Go restano percorsi distinti. Nessuna dipendenza da Copilot; nessun accesso shell o Drive da presumere. Preservare SECURITY.md.
