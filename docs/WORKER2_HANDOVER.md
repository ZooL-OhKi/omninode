# OmniNode — Handover operativo worker-2

Ultimo aggiornamento: 2026-10-15.

Questo documento consente a una nuova IA o a un operatore di riprendere il lavoro su `worker-2` senza presupporre conoscenze non verificate. Separa esplicitamente i risultati confermati dai test ancora da eseguire.

## Regola fondamentale

Non trattare la registrazione di `worker-2` nel gateway come prova di esecuzione applicativa. Al momento è verificata la connessione MQTT mTLS e la presenza del nodo nella flotta; non è ancora verificato un task end-to-end.

## Topologia verificata

```text
Archivista VCN
  worker-2 (systemd)
    -> MQTT mTLS / TLS 1.3
      -> Mosquitto sull’orchestratore
        -> gateway OmniNode
          -> API flotta
```

- Orchestratore: `omninode-orchestrator`.
- Worker: `omninode-archivista-vcn`.
- Nodo worker: `worker-2`.
- Agente dichiarato: `archivista`.
- Gateway HTTP: `127.0.0.1:8000`, non esposto pubblicamente.
- Broker MQTT: mTLS obbligatorio, TLS 1.3, ACL identity-based.
- Topic worker: `omninode/v1/nodes/worker-2/#`.

## Stato worker-2

Stato systemd verificato:

```text
ActiveState=active
SubState=running
UnitFileState=enabled
MainPID=78577
NRestarts=0
```

Il servizio è quindi in esecuzione e abilitato all’avvio automatico.

## Certificati e identità

- Certificato client: CN/SAN `worker-2`.
- CA: `/etc/omninode/certs/ca.crt`.
- Certificato worker: `/etc/omninode/certs/worker-2.crt`.
- Chiave privata: `/etc/omninode/certs/worker-2.key`.
- TLS: TLS 1.3.
- Verifica hostname: abilitata.
- `InsecureSkipVerify`: `false`.

Non inserire mai chiavi private, password, token o contenuti dei certificati nella repository o nei log.

## Verifiche già superate

1. Il certificato `worker-2.crt` è valido e firmato dalla CA attesa.
2. Il SAN/CN corrisponde a `worker-2`.
3. La connessione MQTT usa mTLS e TLS 1.3.
4. Il broker accetta l’identità `worker-2`.
5. Il gateway registra `worker-2` come `online`.
6. L’API flotta dichiara `supported_agents: ["archivista"]`.
7. Il servizio worker è abilitato al boot.
8. La regola firewall per il broker è persistente.

## Risposta gateway

Esempio osservato:

```json
{
  "worker-2": {
    "node_id": "worker-2",
    "status": "online",
    "supported_agents": ["archivista"],
    "timestamp": "2026-10-15T14:23:11Z"
  }
}
```

## Differenza heartbeat

`worker-1` e `worker-2` producono heartbeat con formati leggermente diversi:

- `worker-1`: timestamp numerico e campo `agent_id`.
- `worker-2`: timestamp testuale UTC e agente dichiarato in `supported_agents`.

Il gateway registra entrambi, ma questo non prova che ogni consumatore gestisca entrambi i formati. Prima di modificare il protocollo, completare il test end-to-end e documentare il contratto effettivo.

## Comandi di verifica

### Worker

```bash
sudo systemctl status omninode-worker.service --no-pager
sudo systemctl show omninode-worker.service --no-pager \
  -p ActiveState -p SubState -p UnitFileState \
  -p MainPID -p NRestarts
sudo journalctl -u omninode-worker.service --since '15 minutes ago' --no-pager
```

### Broker e TLS

```bash
sudo systemctl status mosquitto --no-pager
sudo journalctl -u mosquitto --since '15 minutes ago' --no-pager
sudo ss -lntp | grep ':8883'
```

### Gateway e flotta

```bash
sudo systemctl status omninode-gateway.service --no-pager
sudo journalctl -u omninode-gateway.service --since '15 minutes ago' --no-pager
curl --connect-timeout 3 --max-time 10 \
  -sS -i http://127.0.0.1:8000/api/v1/nodes
```

## Test ancora da eseguire

1. Inviare un task innocuo a `worker-2` tramite il gateway.
2. Verificare esecuzione nel workspace sandboxed.
3. Verificare risposta strutturata e ricezione dal gateway.
4. Testare ACL negative: `worker-2` non deve poter pubblicare o sottoscrivere topic di `worker-1`.
5. Riavviare `worker-2` in una finestra concordata e verificare riconnessione e heartbeat.
6. Riavviare broker e gateway solo dopo piano di rollback e approvazione.
7. Verificare persistenza/idempotenza del worker dopo riavvio.

## Prossimi passi consigliati

1. Eseguire il primo task end-to-end.
2. Aggiungere test automatici per formato heartbeat e compatibilità gateway.
3. Documentare il contratto MQTT v1 con esempi reali.
4. Aggiungere metriche e alert su heartbeat, reconnect e errori TLS.
5. Completare hardening systemd.
6. Definire rotazione e revoca certificati.

## Invarianti

- mTLS obbligatorio per MQTT.
- TLS 1.3 only per il worker Go.
- Nessun fallback plaintext.
- Nessun segreto nella repository.
- Nessuna shell arbitraria nel worker.
- Scrittura solo nel workspace sandboxed.
- ACL identity-based e restrittive.
- Gateway HTTP su loopback finché non esiste decisione esplicita di esposizione sicura.
- Nessun deploy, merge, modifica firewall o rotazione certificati senza approvazione umana.
