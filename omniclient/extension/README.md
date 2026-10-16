# OmniNode Bridge — estensione Gemini

Estensione Manifest V3 sperimentale che collega una conversazione Gemini esplicitamente attivata al core OmniNode locale.

## Comportamento

1. Apri una conversazione su `https://gemini.google.com`.
2. Premi **OmniNode OFF** per attivare la sessione nella scheda corrente.
3. Gemini può emettere, alla fine della risposta, un blocco:

```text
```omnicall
{
  "request_id": "gemini-test-0001",
  "path": "gemini/first-note.md",
  "content": "Contenuto del file"
}
```
```

4. L’estensione invia la richiesta al core locale su `http://127.0.0.1:8080/api/bridge/execute`.
5. Il risultato viene inserito nel composer Gemini come blocco delimitato `[OmniNode result]`, solo se l’utente non sta digitando.

## Sicurezza

- L’attivazione è esplicita e per scheda.
- Vengono elaborati soltanto blocchi recintati ` ```omnicall `.
- Lo stesso `request_id` non viene eseguito due volte nella sessione corrente.
- Il token è salvato in `chrome.storage.local`, non nel DOM della pagina.
- Il bridge accetta soltanto richieste da loopback, con origine consentita e token valido.
- Il core esegue solo creazioni esclusive di file nuovi nel workspace; niente shell, sovrascritture o cancellazioni.

## Caricamento

1. Apri `chrome://extensions` oppure `edge://extensions`.
2. Attiva **Modalità sviluppatore**.
3. Seleziona **Carica estensione non pacchettizzata**.
4. Scegli la cartella `omniclient/extension`.
5. Apri **Dettagli → Opzioni estensione** e incolla lo stesso token impostato per `OMNINODE_BRIDGE_TOKEN`.

## Limiti

- L’adapter DOM è un fallback: le interfacce Gemini possono cambiare.
- Non vengono bypassati login, CAPTCHA o restrizioni del servizio.
- Il supporto a Perplexity, altre IA e risorse remote verrà aggiunto solo dopo la validazione della verticale Gemini.
