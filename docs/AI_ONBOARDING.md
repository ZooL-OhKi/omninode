# AI Onboarding — OmniNode

Questo documento è il punto di ingresso per una nuova IA che deve continuare il lavoro su OmniNode.

## Ordine di lettura

1. Leggere `AGENTS.md`: missione, invarianti, stato e regole operative.
2. Leggere `docs/WORKER2_HANDOVER.md`: stato live verificato di `worker-2`.
3. Leggere `ARCHITECTURE.md` e `SECURITY.md`.
4. Esaminare il codice prima di proporre modifiche.
5. Eseguire i test locali prima di proporre una PR.

## Regola più importante

Non confondere:

- **Nodo online nel gateway** con **task eseguito con successo**.
- **Servizio systemd attivo** con **funzionalità applicativa collaudata**.
- **Configurazione deployata** con **test di resilienza superati**.

## Stato live noto

Al 2026-10-15, `worker-2` è configurato sull’host `omninode-archivista-vcn`:

- systemd: `active / running`, `enabled`.
- MQTT: mTLS TLS 1.3 verso il broker dell’orchestratore.
- Identità: `worker-2`.
- Agente dichiarato: `archivista`.
- Gateway: nodo registrato come `online`.

Non è ancora stato verificato un task end-to-end.

## Cosa fare per primo

1. Verificare lo stato del worker:

```bash
sudo systemctl status omninode-worker.service --no-pager
```

2. Verificare la flotta dal gateway:

```bash
curl --connect-timeout 3 --max-time 10 \
  -sS http://127.0.0.1:8000/api/v1/nodes
```

3. Leggere i log recenti:

```bash
sudo journalctl -u omninode-worker.service --since '15 minutes ago' --no-pager
sudo journalctl -u omninode-gateway.service --since '15 minutes ago' --no-pager
```

4. Eseguire un task innocuo tramite il gateway e verificare:

- accodamento;
- consegna MQTT;
- esecuzione nel workspace;
- risposta strutturata;
- audit;
- assenza di accessi fuori sandbox.

## Test successivi

- ACL negative: `worker-2` non deve accedere ai topic di `worker-1`.
- Riavvio worker e verifica reconnect/heartbeat.
- Riavvio controllato di broker e gateway, solo con piano di rollback.
- Compatibilità heartbeat fra `worker-1` e `worker-2`.
- Persistenza e idempotenza.

## Limiti

- Non modificare firewall, certificati, ACL o unit systemd senza approvazione umana.
- Non fare merge o deploy senza PR, test e revisione.
- Non inserire segreti, token, password o chiavi private nella repository.
- Non indebolire TLS, validazione hostname, ACL o sandbox.
- Non presupporre che una capacità dichiarata sia già implementata o testata.

## Punto di ripresa

Il prossimo obiettivo operativo è il primo task end-to-end su `worker-2`, seguito dai test ACL e di resilienza. Dettagli e comandi sono in `docs/WORKER2_HANDOVER.md`.
