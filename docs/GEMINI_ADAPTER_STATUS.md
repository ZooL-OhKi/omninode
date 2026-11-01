# Gemini: testo reale provato, immagine in verifica

Baseline 55291dbd3b65f16f03b923a770657972865674c4, tutti gli 11 check success. e2e-footer-003 prova lo screenshot locale; e2e-text-004 prova ritorno testuale e risposta di Gemini con ID e dimensioni. Evidenze dell'utente, non esecuzione fisica dell'assistente.

Il footer message-actions richiede quattro controlli, assenza di streaming, nascita/mutazioni osservate, quiescenza e conferma locale. Non e una garanzia universale del DOM Gemini. Il parser rifiuta omninode_response e gli ID del registro consegna.

La tranche immagine aggiunge: allegato richiesto con consenso esplicito, File PNG/JPEG con estensione corretta dai byte gia normalizzati, un solo paste sintetico sul composer del testo proprio, nessuna clipboard di sistema. Upload sintetico non ancora validato sul provider reale.

ATTACHMENT_PENDING -> ATTACHMENT_READY_FOR_CONFIRM richiede una sola nuova img caricata, niente upload/alert rilevati e 3 secondi stabili. Il click yes conferma che l'utente vede lo screenshot nell'input Gemini, l'upload e concluso e autorizza l'unico invio: ATTACHMENT_VERIFIED, verification=user-confirmed. Non e verifica automatica dei byte caricati o del server. Il controllo resta conservativo: varianti DOM non riconosciute possono bloccare il flusso.

Dopo il tentativo, timeout/errore/preview sostituita bloccano con ATTACHMENT_UNCERTAIN_HALT; nessun fallback automatico a un secondo upload. L'invio richiede testo invariato e preview confermata invariata. Nessun allegato preesistente viene rimosso. SENT_CONFIRMED per il modo immagine richiede immagine nel nuovo user-query correlato; se il selettore non rileva il messaggio, esito incerto terminale senza retry.

Test con fixture non certificano l'upload reale. Accettazione finale: Gemini riceve l'immagine e descrive un particolare visivo non deducibile dal JSON. Il testo e gia provato, non va ripetuto solo per conteggi. Leggere CURRENT_STATUS.md e SECURITY.md.
