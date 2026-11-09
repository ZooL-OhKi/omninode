# Estensione OmniNode Bridge

Manifest letto al commit 1a6ce035d814d7e6a77fcab002ab663baebdfd99: versione 0.3.4. [Stato corrente](../../docs/CURRENT_STATUS.md), [handover](../../docs/ZERO_CONTEXT_HANDOVER.md).

Background service_worker.js; popup desktop.html. Content Gemini: action_policy.js, task_delivery.js, text_delivery.js, content.js. Content Perplexity: gli stessi primi tre piu perplexity_adapter.js, perplexity_delivery.js, perplexity_content.js. Non trattare content.js come universalmente disabilitato e non cambiare manifest solo per seguire vecchie guide.

Perplexity accetta screenshot e move con riferimento a un'osservazione fresca e coord_space=image_pixels. Click/type/hotkey non sono accettati dal parser corrente. Il 9 novembre e riuscito il ciclo reale 0014 -> 0015 con immagine ricevuta. Non e una qualifica generale degli altri provider o del desktop.

Nel DOM verificato l'allegato e il fratello precedente della bolla JSON. La consegna verifica struttura stretta, bolla unica, una sola immagine visibile caricata e composer vuoto. Un solo click; incertezza -> SEND_UNCERTAIN_HALT_NO_RETRY e canale in pausa. Non fare reinvio o fallback Enter. Preservare bozze e allegati preesistenti.

L'host com.omninode.desktop va associato all'ID reale dell'estensione: [installazione](../../desktop/INSTALL_STATUS.md). GitHub non aggiorna l'estensione Windows. Ricarica e aggancio servono dopo cambi runtime approvati, non dopo soli Markdown. Suite e limiti in [BUILD](../../BUILD.md); CI non sostituisce prova del browser reale.
