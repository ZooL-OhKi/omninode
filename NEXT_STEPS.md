# Prossimi passi

## Prima del deploy

- [ ] Eseguire `go mod tidy` e `go build ./...` in `omniclient/`.
- [ ] Correggere eventuali incompatibilita' API di `playwright-go` emerse in compilazione.
- [ ] Verificare che `mqtt_client.go` sia presente, compili e gestisca `web_snapshot`/`web_click` con il formato MQTT documentato.
- [ ] Eseguire `pip install -r node1-gateway/requirements.txt` in un virtualenv Python.
- [ ] Controllare che `aiomqtt` sia elencato in `requirements.txt`.
- [ ] Rimuovere tutti i segreti e valori predefiniti dalle variabili di ambiente e dai file `.env` committati.

## Mosquitto (Oracle B)

- [ ] Creare CA privata, certificato server e un certificato client distinto per ciascun worker e gateway.
- [ ] Abilitare listener TLS sulla porta 8883 e `require_certificate true`.
- [ ] Disabilitare listener anonimi e usare ACL MQTT minime per gateway e worker.
- [ ] Consentire ai worker solo subscribe sui propri `cmd/+` e publish sui propri `result/+` e `heartbeat`.
- [ ] Consentire al gateway publish sui comandi/approvazioni e subscribe ai risultati, heartbeat e alert.

## Gateway e Cloudflare

- [ ] Configurare `MCP_SECRET` lungo e non committato.
- [ ] Configurare `MQTT_BROKER`, `MQTT_CA`, `MQTT_CERT`, `MQTT_KEY` e bind loopback.
- [ ] Installare Cloudflare Tunnel su Oracle A e instradare `plini.net` verso `http://127.0.0.1:8000`.
- [ ] Applicare Cloudflare Access interattivo per dashboard e policy M2M separata per `/mcp`.
- [ ] Verificare che gli header Service Token di Cloudflare e il Bearer applicativo siano supportati dal connector MCP scelto.
- [ ] Testare SSE da rete mobile dopo login Access.

## Worker locali

- [ ] Avviare Chrome con profilo dedicato e CDP su loopback.
- [ ] Creare `certs/ca.crt`, `certs/client.crt`, `certs/client.key` con permessi stretti.
- [ ] Impostare `OMNI_WS_TOKEN` e `OMNI_WS_ORIGINS` senza inserirli nel repository.
- [ ] Configurare `OMNI_NODE_ID`, URL broker MQTT e percorsi certificati.
- [ ] Verificare heartbeat immediato e poi ogni 30 secondi.
- [ ] Verificare che un worker offline non resti visibile indefinitamente nella dashboard.

## Test di accettazione

1. **Build worker:** `go build ./...` deve completare senza errori.
2. **mTLS MQTT:** il worker si connette a Mosquitto con certificato valido; un certificato non autorizzato viene rifiutato.
3. **Heartbeat:** `ryzen` e/o `surface` compaiono nella dashboard e il timestamp si aggiorna.
4. **Routing:** un task per `agent_id` supportato arriva solo al nodo pubblicato nell'heartbeat.
5. **Browser:** `web_snapshot` restituisce un snapshot e `web_click` rifiuta ref scaduti.
6. **SSE:** un messaggio su `omninode/alerts/approval` compare in dashboard senza refresh.
7. **Approval:** la dashboard pubblica una sola decisione valida; il worker scaduto rifiuta decisioni tardive.
8. **Access:** `/` richiede login umano; `/mcp` rifiuta richieste senza autenticazione prevista.

## Step successivi

### Step 5: Ops CLI Human-in-the-loop

Implementare tool allowlisted `ops.terraform` e `ops.oci` con:

- argomenti strutturati e validazione rigida;
- `exec.Command` con argv separati, mai `sh -c` o `cmd /c`;
- stato persistente `pending_approval`;
- alert SSE/MQTT;
- approvazione o rifiuto con TTL;
- audit append-only;
- risultati e log con dimensione massima.

### Hardening produzione

- [ ] Persistenza task/routing/audit (Postgres o SQLite con backup).
- [ ] Rate limit su `/mcp`, `/api/v1/approve` e SSE.
- [ ] Scadenza nodi basata su heartbeat (es. offline dopo 90 secondi).
- [ ] Limite e backpressure sulle code SSE.
- [ ] CORS/CSRF per endpoint dashboard e approvazione.
- [ ] Osservabilita': metriche, alert e rotazione log.
