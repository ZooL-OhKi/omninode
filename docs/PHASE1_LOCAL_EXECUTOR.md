# Phase 1: Real Local Vertical Slice

## Obiettivo

Chiudere il loopback test implementando il ciclo di esecuzione autonomo locale. Il demone Python locale agisce come nodo esecutore, iscrivendosi al proprio topic MQTT `tasks` ed eseguendo in sicurezza l'operazione `workspace.write`.

## Contesto Architetturale

L'analisi del repository mostra che:
- Il client Go funge da interfaccia MCP.
- Il motore di policy e il `LocalWorkspaceExecutor` risiedono nel gateway Python.

Per rispettare il principio del minimo privilegio e le direttive di progetto, il demone Python locale deve:
1. Iscriversi al topic `omninode/nodes/node-local/tasks`.
2. Intercettare i task destinati al nodo locale.
3. Eseguire localmente solo `workspace.write`.
4. Pubblicare il risultato su `omninode/nodes/node-local/results`.

## Modifiche Apportate

### `node1-gateway/mqtt_service.py`

1. **Attributo `task_handler`**: Aggiunto in `__init__` per registrare il callback dei task.
   ```python
   self.task_handler = None
   ```

2. **Metodo `set_task_handler`**: Nuovo metodo per registrare il callback.
   ```python
   def set_task_handler(self, handler):
       self.task_handler = handler
   ```

3. **Sottoscrizione al topic tasks**: In `_on_connect`, aggiunta sottoscrizione al nodo locale.
   ```python
   client.subscribe("omninode/nodes/node-local/tasks", qos=1)
   ```

4. **Intercettazione evento tasks**: In `_on_message`, intercettazione subito dopo il parsing JSON.
   ```python
   if event == "tasks":
       if self.task_handler:
           try:
               self.task_handler(node_id, payload)
           except Exception as e:
               logger.error(f"Task handler error for {node_id}: {e}")
       return
   ```

### `node1-gateway/main.py`

1. **Configurazione workspace temporaneo**:
   ```python
   WORKSPACE_ROOT = os.getenv(
       "OMNINODE_WORKSPACE_ROOT",
       os.path.join(tempfile.gettempdir(), "omninode_workspace")
   )
   os.makedirs(WORKSPACE_ROOT, exist_ok=True)
   local_executor = LocalWorkspaceExecutor(roots={"temporary": WORKSPACE_ROOT})
   ```

2. **Callback `handle_local_task`**: Intercetta il task da MQTT, lo esegue localmente e pubblica il risultato.
   - Filtra per `node_id == "node-local"`.
   - Supporta esclusivamente `task_type == "workspace.write"`.
   - Pubblica il risultato su `omninode/nodes/{node_id}/results`.

3. **Registrazione callback**:
   ```python
   mqtt_service.set_task_handler(handle_local_task)
   ```

4. **Endpoint di debug `/workspace/write`**: Aggiunto per testare `LocalWorkspaceExecutor` senza MQTT.

## Flusso di Esecuzione

1. Un task viene pubblicato su `omninode/nodes/node-local/tasks`.
2. `mqtt_service._on_message` intercetta l'evento `tasks`.
3. `handle_local_task` viene invocato con `node_id` e `task_envelope`.
4. Se `task_type == "workspace.write"`, `local_executor.write` esegue l'operazione.
5. Il risultato viene pubblicato su `omninode/nodes/node-local/results`.

## Sicurezza e Policy

- **Minimo privilegio**: Solo `workspace.write` è supportato.
- **Policy denial**: Capability non supportate restituiscono errore esplicito.
- **Workspace isolato**: Il workspace temporaneo è configurato in una directory isolata.

## Test

Per testare l'implementazione:

1. Avviare il gateway:
   ```bash
   cd node1-gateway
   python main.py
   ```

2. Pubblicare un task di test:
   ```bash
   mosquitto_pub -t "omninode/nodes/node-local/tasks" -m '{"task_id":"test-1","task_type":"workspace.write","payload":{"workspace_id":"temporary","path":"test.txt","content":"Hello World"}}'
   ```

3. Verificare il risultato su `omninode/nodes/node-local/results`.

## Prossimi Passi

- Estendere il supporto ad altre capability (es. `workspace.read`, `workspace.delete`).
- Implementare validazione avanzata dei path.
- Aggiungere logging e metriche per monitoraggio.
