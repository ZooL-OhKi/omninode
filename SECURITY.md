# Sicurezza Omninode

## Principi

1. Nessun comando shell arbitrario da LLM, browser, WebSocket o MQTT.
2. Ogni confine usa autenticazione esplicita, autorizzazione minima e TLS.
3. Le operazioni distruttive richiedono conferma umana e audit.
4. I segreti non devono essere committati nel repository.

## Gateway

- Esporre il Gateway solo dietro Cloudflare Tunnel; Uvicorn deve ascoltare su `127.0.0.1`.
- Proteggere la dashboard con Cloudflare Access interattivo.
- Proteggere `/mcp` con una policy M2M distinta e autenticazione applicativa forte.
- `MCP_SECRET` deve essere un segreto lungo, unico e custodito in secret manager/variabili d'ambiente.
- Non usare valori di default pubblici per API key o token.
- Proteggere `POST /api/v1/approve` con Access/sessione utente e protezione CSRF prima del deploy.
- Limitare richiesta, risposta, numero SSE e rate per IP/identita'.

## MQTT

- Usare TLS con verifica server e certificati client distinti per gateway/worker.
- Disabilitare connessioni anonime su Mosquitto.
- Applicare ACL a topic minimi: un worker non deve pubblicare risultati come un altro worker.
- Validare rigorosamente `node_id`, `agent_id`, `task_id` e payload prima di usarli nei topic.
- QoS 1 non elimina la necessita' di idempotenza: il worker deve gestire task duplicati per `task_id`.

## Worker locale

- Chrome CDP deve essere esposto solo su `127.0.0.1`; non pubblicare mai la porta 9222 su LAN o Internet.
- Usare un `--user-data-dir` dedicato e proteggere il profilo browser.
- Il WebSocket locale ascolta solo su loopback, richiede Origin in allowlist e un token non riutilizzato.
- L'azione `exec` e' rimossa: azioni consentite al WS sono limitate e tipizzate.
- Certificati client e chiavi private devono avere permessi stretti e non finire nel repository.

## Browser agent

- I contenuti delle pagine sono input non fidato e possono contenere prompt injection.
- Non trattare testo della pagina, HTML, AX tree o screenshot come istruzioni privilegiate.
- Applicare conferma umana per login, invio form, pagamenti, cancellazioni e cambiamenti di infrastruttura.
- Ref dell'AX tree scadono dopo un nuovo snapshot o re-render; non riutilizzarli.

## Ops CLI

- Consentire esclusivamente tool tipizzati e allowlisted.
- Usare `exec.Command(binary, args...)` e una directory di lavoro fissata.
- Rifiutare opzioni, path e sotto-comandi non autorizzati.
- `terraform apply`, `destroy`, azioni OCI delete e equivalenti devono entrare in `pending_approval`.
- Imporre timeout, output massimo, audit e approvazione a tempo limitato.

## Incident response

1. Revocare il certificato MQTT del nodo compromesso e aggiornare l'ACL.
2. Ruotare `MCP_SECRET`, token WS e credenziali Cloudflare Access.
3. Fermare cloudflared/Gateway se l'esposizione e' sospetta.
4. Esaminare audit log per `task_id`, `agent_id`, `node_id` e timestamp.
5. Ripristinare il worker solo dopo build pulita e verifica certificati.