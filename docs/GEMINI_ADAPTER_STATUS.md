# Adapter Gemini: screenshot locale provato, consegna in verifica

Riferimento: 5ab251181a1fe146b5029ebf0529405e2331cf33. Tutti gli 11 check success. Leggere CURRENT_STATUS.md e SECURITY.md.

La prova utente e2e-footer-003 mostra screenshot Windows nel pannello. Il footer reale message-actions contiene thumb-up-button, thumb-down-button, regenerate-button e copy-button. Il controllo richiede anche assenza di streaming, quiescenza e conferma locale; non richiede gli attributi aria-busy/data-is-streaming false assenti nella prova. Non e una certificazione universale di Gemini o della virtualizzazione.

La tranche introduce deliveryLedger, PREPARED distinto da INSERTED, SEND_REQUESTED, SENT_CONFIRMED e SEND_UNCERTAIN_HALT. Bozza/allegati rilevati bloccano l'inserimento; modifica utente lo abortisce. Il JSON omninode_response/completed_action non e un comando; gli ID consegna gia registrati sono rifiutati dal parser.

Inserimento e invio testuali richiedono due click espliciti e rivalidazione del grant. SENT_CONFIRMED richiede nuovo user-query con payload esatto, composer vuoto e generazione osservata: e evidenza DOM, non ricevuta server. execCommand e user-query restano da provare sul provider reale.

L'immagine e scaricabile su click come passaggio assistito; nessun paste/drop sintetico, clipboard implicita, upload automatico o ATTACHMENT_VERIFIED fittizio. L'invio controllato blocca gli allegati rilevati. La diagnostica generazione 12 s e ritirata; e disponibile una diagnostica composer di sola lettura nel risultato.
