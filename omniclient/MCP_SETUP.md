# MCP Setup Guide per Omninode

Questa guida spiega come configurare agenti IA esterni (Gemini, Claude, etc.) per connettersi al server MCP di Omninode.

## Panoramica

Omninode espone 4 tools tramite MCP (Model Context Protocol):

| Tool | Descrizione | Input |
|------|-------------|-------|
| `list_nodes` | Lista tutti i nodi connessi | Nessuno |
| `get_node_status` | Stato di un nodo specifico | `node_id` (string) |
| `dispatch_task` | Invia task computazionale | `node_id`, `task_type`, `payload` |
| `get_fabric_health` | Salute complessiva del fabric | Nessuno |

## Modalità¹¹ di Connessione

### 1. Stdio (Locale)

Il server MCP viene eseguito come processo locale, comunicando via stdin/stdout.

**Avvio:**
```bash
cd omniclient
./omniclient --mcp-stdio
```

### 2. SSE (Remoto/HTTP)

Il server MCP espone endpoint HTTP SSE su porta 8080.

**Avvio:**
```bash
cd omniclient
wails dev
# MCP SSE disponibile su http://localhost:8080/sse
```

---

## Configurazione per Gemini Desktop

### Prerequisiti
- Gemini Desktop installato
- Omninode compilato (`wails build` o `go build`)

### Step 1: Configura MCP Server

Apri le impostazioni di Gemini Desktop e aggiungi un nuovo MCP server:

```json
{
  "mcpServers": {
    "omninode": {
      "command": "/path/to/omniclient",
      "args": ["--mcp-stdio"],
      "cwd": "/path/to/omniclient"
    }
  }
}
```

### Step 2: Verifica Connessione

Nel chat di Gemini, prova:

```
Mostrami lo stato del fabric Omninode
```

Gemini dovrebbe usare il tool `get_fabric_health` automaticamente.

### Step 3: Prompt di Test

Ecco alcuni prompt per testare i tools:

**Test list_nodes:**
```
Quali nodi sono connessi a Omninode?
```

**Test get_node_status:**
```
Qual è lo stato del nodo gateway?
```

**Test dispatch_task:**
```
Invia un task di tipo 'compute' al nodo 'node-1' per sommare i valori [1,2,3,4,5]
```

**Test get_fabric_health:**
```
Come sta la salute complessiva del fabric?
```

---

## Configurazione per Claude Desktop

### Prerequisiti
- Claude Desktop installato
- Node.js 18+ (per MCP SDK)

### Step 1: Installa MCP Client

```bash
npm install -g @anthropic-ai/mcp-client
```

### Step 2: Configura claude_desktop_config.json

Crea/modifica `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "omninode": {
      "command": "/path/to/omniclient",
      "args": ["--mcp-stdio"],
      "cwd": "/path/to/omniclient"
    }
  }
}
```

### Step 3: Riavvia Claude Desktop

Claude ora può usare i tools Omninode.

---

## Configurazione per Cursor IDE

### Step 1: Imposta MCP in Cursor

Vai su Settings → MCP → Add Server:

- **Name**: `omninode`
- **Type**: `Local`
- **Command**: `/path/to/omniclient --mcp-stdio`

### Step 2: Usa nei Prompt

Nei prompt di Cursor (Cmd+K o Cmd+L), chiedi:

```
@omninode Qual è lo stato del fabric?
```

---

## Test con Client Python

Se vuoi testare senza agenti IA, usa lo script Python incluso:

```bash
cd omniclient

# Test via stdio
python test_mcp_client.py --stdio

# Test via SSE (richiede wails dev in esecuzione)
python test_mcp_client.py --sse
```

---

## Troubleshooting

### Il client non vede i tools

1. Verifica che il server sia in esecuzione
2. Controlla i log: `./omniclient --mcp-stdio 2>&1 | tee mcp.log`
3. Assicurati che il percorso nel config sia corretto

### Errori di connessione SSE

1. Verifica che la porta 8080 sia libera
2. Controlla firewall/antivirus
3. Prova `curl http://localhost:8080/sse`

### Tools non vengono chiamati

Alcuni agenti richiedono prompt espliciti. Prova:

```
Usa il tool list_nodes per mostrare i nodi
```

---

## Esempio di Integrazione Avanzata

Puoi usare Omninode per orchestrare task complessi:

```
1. Usa get_fabric_health per verificare lo stato
2. Usa list_nodes per trovare il nodo con load minore
3. Usa dispatch_task per inviare un task computazionale
4. Usa get_node_status per monitorare l'esecuzione
```

Questo permette agli agenti IA di usare Omninode come fabric di calcolo distribuito.
