# OmniNode: handover autosufficiente

Aggiornamento: 9 novembre 2026. Questo documento consente di riprendere il lavoro senza la conversazione precedente. Riporta fatti, limiti e regole; non certifica il progetto completo.

## Missione

OmniNode permette alle AI delle chat web di osservare e controllare un ambiente esplicitamente autorizzato e ricevere risultati nella stessa conversazione. Non è un nuovo LLM.

Leggere [stato corrente](CURRENT_STATUS.md), [AGENTS](../AGENTS.md), [SECURITY](../SECURITY.md), [priorità](../NEXT_STEPS.md), [build](../BUILD.md), [recuperi](../RESUME.md) e [mappa](REPOSITORY_MAP.md).

## Bootstrap

Repository `ZooL-OhKi/omninode`; destinazione corrente della manutenzione: `main`. Verificare sempre strumenti, HEAD remoto, branch, status e diff prima di agire.

Non eseguire checkout, reset, installazioni o restore impliciti. Una scrittura GitHub non aggiorna Windows, Chrome, Drive o VPS. Una nuova conversazione richiede consenso locale e aggancio effettivo prima dell’input desktop.

## Architettura

- `omniclient/`: worker Go, MQTT, workspace, bridge/UI e idempotenza.
- `omniclient/extension/`: manifest 0.3.4, adapter Perplexity, broker desktop e test.
- `desktop/`: host Native Messaging Python, primitive Windows, consenso e preview.
- `node1-gateway/`: gateway Python, MQTT, task, policy, audit e orchestrazione.
- `deploy/` e `scripts/`: configurazioni e strumenti; non attestano servizi attivi.

UI HTTP Go, MQTT, MCP, Native Messaging e browser CDP sono perimetri distinti.

## Protocollo

Dopo autorizzazione e aggancio, un comando è un oggetto con `request_id`, `action` e `args`. Screenshot usa args vuoto; move richiede `x`, `y`, `observation_id` e `coord_space`; click richiede anche `button`; type, press e hotkey richiedono un target confermato.

Usare sempre ID nuovi. Non riutilizzare ID storici. Un risultato valido contiene `omninode_response=true`, `request_id` correlato, `status=ok`, `completed_action`, `execution_status`, `observation_id`, metadati temporali e geometria.

## Diagnostica

`SEND_UNCERTAIN_HALT_NO_RETRY` indica un invio tentato una volta con esito non concluso. `deliveryHalted=true` blocca nuovi comandi. Non ripetere azione, ID, upload, click o Enter per sbloccare.

Dopo un arresto riportare banner esatto e risultato ricevuto, distinguendo esecuzione da consegna. Non esportare URL firmati, credenziali o log console grezzi.

## Recuperi da preservare

Backup storici sotto `C:\Users\ugopl\AppData\Local\OmniNode\Backups\`:

- `verified-579d9b7bbaac4a8a9f4f6cf49bfffb59`
- `post-send-6a52d80defb943ac8167aa3b0fa38010`
- `attachment-dom-af496f1337bd481bb0f26b0204816264`
- `perplexity-actions-9030e142f61549c3a1dccca0f1c1ed0e`
- `perplexity-actions-252ed22643ce4a2bb1f3c76112e84b91`

Preservare copie C:/A:/Drive, stash, branch e VPS descritti in `RESUME.md`. Non sincronizzare `.git` con Drive, non cancellare oggetti/lock/refs, non ripristinare backup alla cieca.

## Modalità di lavoro

Test, mock, CI, installazione e prova browser sono evidenze distinte. Non sommare conteggi storici né attribuirli a commit successivi. Fermarsi per consensi specifici, esiti incerti o accessi mancanti.

Nessun commit, push, merge, deploy o modifica a manifest/host senza approvazione specifica. Un consenso generale non elimina i gate degli strumenti.
