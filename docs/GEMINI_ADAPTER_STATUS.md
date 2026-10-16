# Adapter Gemini: esperimento disabilitato

[Stato corrente](CURRENT_STATUS.md). Il manifest 0.2.0 non carica content.js o background.js: il flusso automatico Gemini/HTTP precedente non e il prodotto operativo corrente.

L'esperimento iniziale cercava backtick nel testo renderizzato e non funzionava nella prova dell'utente. La correzione leggeva nuovi model-response/pre e richiedeva aria-busy=false o data-is-streaming=false, attributi verificati solo nelle fixture. Restano rischi di esempi citati, provenienza e completamento reale dello streaming.

Le prove storiche comprendevano 16 test parser/delivery e 7 controlli Chromium con bridge simulato; non una chat Gemini reale o un file creato end-to-end. Il codice resta per revisione e test, non per riattivazione automatica. Non eliminare content.js senza aggiornare adapter.test.cjs e verificare riferimenti.
