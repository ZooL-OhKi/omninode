"""
Omninode MCP Gateway (Oracle A) - FastAPI

File NUOVO, affiancato a main.py esistente (che non viene toccato).

Rotte:
  GET  /         dashboard "Bento Box" (protetta da Cloudflare Access a livello di edge)
  POST /mcp      MCP Streamable HTTP (JSON-RPC 2.0), autenticato con Bearer fisso
  GET  /healthz  stato del gateway e del bridge MQTT

Contratto MQTT con il worker Go (da implementare lato worker nello Step 4):
  comando:   omninode/nodes/{node_id}/cmd/{task_id}
             {"task_id","agent_id","action","params":{...}}
  risultato: omninode/nodes/{node_id}/result/{task_id}
             {"task_id","status":"success|error","output":"...","error":"..."}

Variabili d'ambiente:
  OMNI_MCP_TOKEN     obbligatoria, minimo 32 caratteri
  MQTT_HOST          obbligatoria (Oracle B)
  MQTT_PORT          default 8883
  MQTT_CA            percorso CA (PEM)
  MQTT_CERT          percorso certificato client (PEM)
  MQTT_KEY           percorso chiave client (PEM)
  DEFAULT_NODE_ID    nodo usato se il tool non specifica node_id
  RESULT_TIMEOUT     secondi di attesa del risultato (default 30)

Avvio (solo loopback: il traffico arriva da cloudflared):
  uvicorn mcp_gateway:app --host 127.0.0.1 --port 8000

Dipendenze: pip install fastapi uvicorn aiomqtt
"""

import asyncio
import hmac
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiomqtt
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

log = logging.getLogger("omninode.gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

MCP_TOKEN = os.environ.get("OMNI_MCP_TOKEN", "")
MQTT_HOST = os.environ.get("MQTT_HOST", "")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_CA = os.environ.get("MQTT_CA")
MQTT_CERT = os.environ.get("MQTT_CERT")
MQTT_KEY = os.environ.get("MQTT_KEY")
DEFAULT_NODE_ID = os.environ.get("DEFAULT_NODE_ID", "")
RESULT_TIMEOUT = float(os.environ.get("RESULT_TIMEOUT", "30"))
MAX_OUTPUT_CHARS = 60_000
RECONNECT_DELAY = 5.0
STATIC_DIR = Path(__file__).parent / "static"

# node_id e agent_id finiscono nei topic MQTT: niente '/', '+', '#'.
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Versioni del protocollo MCP che dichiariamo di supportare (da verificare con la spec corrente).
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26")


class BridgeUnavailable(Exception):
    """Il broker MQTT non e' raggiungibile."""


class MqttBridge:
    """Client MQTT persistente con correlazione task_id -> Future."""

    def __init__(self) -> None:
        self._client: aiomqtt.Client | None = None
        self._pending: dict[str, tuple[str, asyncio.Future]] = {}
        self._task: asyncio.Task | None = None

    @property
    def connected(self) -> bool:
        return self._client is not None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="mqtt-bridge")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def _tls(self) -> aiomqtt.TLSParameters | None:
        if not MQTT_CA:
            return None
        return aiomqtt.TLSParameters(ca_certs=MQTT_CA, certfile=MQTT_CERT, keyfile=MQTT_KEY)

    async def _run(self) -> None:
        """Loop di connessione con riconnessione automatica."""
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=MQTT_HOST,
                    port=MQTT_PORT,
                    tls_params=self._tls(),
                    identifier=f"omninode-gateway-{uuid.uuid4().hex[:8]}",
                    keepalive=30,
                ) as client:
                    # Sottoscrizione PRIMA di pubblicare qualsiasi comando.
                    await client.subscribe("omninode/nodes/+/result/+", qos=1)
                    self._client = client
                    log.info("MQTT connesso a %s:%s", MQTT_HOST, MQTT_PORT)
                    async for message in client.messages:
                        self._on_message(message)
            except aiomqtt.MqttError as exc:
                log.warning("MQTT disconnesso: %s", exc)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Errore inatteso nel bridge MQTT")
            finally:
                self._client = None
                # Sblocca subito chi sta aspettando un risultato.
                for _, fut in list(self._pending.values()):
                    if not fut.done():
                        fut.set_exception(BridgeUnavailable("connessione MQTT persa"))
            await asyncio.sleep(RECONNECT_DELAY)

    def _on_message(self, message: aiomqtt.Message) -> None:
        parts = str(message.topic).split("/")
        # Atteso: omninode/nodes/{node_id}/result/{task_id}
        if len(parts) != 5 or parts[0] != "omninode" or parts[1] != "nodes" or parts[3] != "result":
            return
        node_id, task_id = parts[2], parts[4]
        entry = self._pending.get(task_id)
        if entry is None:
            return  # risultato tardivo o non richiesto da questo gateway
        expected_node, fut = entry
        if node_id != expected_node:
            # Un nodo diverso non puo' rispondere al posto di quello interrogato.
            log.warning("Risultato per %s ricevuto da nodo inatteso %s: scartato", task_id, node_id)
            return
        try:
            payload = json.loads(message.payload)
        except (TypeError, ValueError):
            payload = {"status": "error", "error": "risposta del worker non e' JSON valido"}
        if not fut.done():
            fut.set_result(payload)

    async def call(
        self, node_id: str, agent_id: str, action: str, params: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        """Pubblica il task e attende il risultato (o timeout)."""
        client = self._client
        if client is None:
            raise BridgeUnavailable("broker MQTT non connesso")

        task_id = uuid.uuid4().hex
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[task_id] = (node_id, fut)
        try:
            payload = json.dumps(
                {"task_id": task_id, "agent_id": agent_id, "action": action, "params": params}
            )
            await client.publish(f"omninode/nodes/{node_id}/cmd/{task_id}", payload=payload, qos=1)
            return await asyncio.wait_for(fut, timeout=timeout)
        except aiomqtt.MqttError as exc:
            raise BridgeUnavailable(str(exc)) from exc
        finally:
            self._pending.pop(task_id, None)


bridge = MqttBridge()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if len(MCP_TOKEN) < 32:
        raise RuntimeError("OMNI_MCP_TOKEN mancante o troppo corto (minimo 32 caratteri)")
    if not MQTT_HOST:
        raise RuntimeError("MQTT_HOST mancante")
    bridge.start()
    yield
    await bridge.stop()


app = FastAPI(title="Omninode Gateway", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

# ---------------------------------------------------------------------------
# Dashboard e health
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def dashboard() -> Response:
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    return HTMLResponse("<h1>Omninode</h1><p>Dashboard non ancora installata (static/index.html).</p>")


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, Any]:
    return {"status": "ok", "mqtt_connected": bridge.connected}


# ---------------------------------------------------------------------------
# MCP (Streamable HTTP, JSON-RPC 2.0, modalita' stateless con risposte JSON)
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "web_snapshot",
        "description": (
            "Restituisce l'albero di accessibilita' compatto della pagina corrente dell'agente. "
            "Ogni elemento interattivo ha un ref numerico [N] valido solo fino al prossimo snapshot."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Identificativo della sessione browser dell'agente"},
                "node_id": {"type": "string", "description": "Nodo worker (opzionale se esiste un default)"},
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "web_click",
        "description": "Clic con mouse reale sul ref indicato (dall'ultimo web_snapshot).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "node_id": {"type": "string"},
                "ref": {"type": "integer", "minimum": 1, "description": "Ref numerico dello snapshot"},
            },
            "required": ["agent_id", "ref"],
        },
    },
]

TOOL_ACTIONS = {"web_snapshot": "web_snapshot", "web_click": "web_click"}


def rpc_result(req_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def rpc_error(req_id: Any, code: int, message: str, status: int = 200) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}, status_code=status)


def tool_text(text: str, is_error: bool = False) -> dict[str, Any]:
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS] + "\n# ...output troncato dal gateway"
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def authorized(request: Request) -> bool:
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return False
    return hmac.compare_digest(value.strip().encode(), MCP_TOKEN.encode())


async def run_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    action = TOOL_ACTIONS.get(name)
    if action is None:
        return tool_text(f"Tool sconosciuto: {name}", True)

    agent_id = str(args.get("agent_id", ""))
    node_id = str(args.get("node_id") or DEFAULT_NODE_ID)
    if not SAFE_ID.match(agent_id):
        return tool_text("agent_id mancante o non valido (ammessi: lettere, cifre, _ e -)", True)
    if not SAFE_ID.match(node_id):
        return tool_text("node_id mancante o non valido", True)

    params: dict[str, Any] = {}
    if name == "web_click":
        ref = args.get("ref")
        if not isinstance(ref, int) or isinstance(ref, bool) or ref < 1:
            return tool_text("ref deve essere un intero >= 1", True)
        params["ref"] = ref

    try:
        result = await bridge.call(node_id, agent_id, action, params, timeout=RESULT_TIMEOUT)
    except asyncio.TimeoutError:
        return tool_text(f"Timeout: nessuna risposta dal nodo '{node_id}' entro {RESULT_TIMEOUT:.0f}s", True)
    except BridgeUnavailable as exc:
        return tool_text(f"Broker MQTT non disponibile: {exc}", True)

    if result.get("status") == "success":
        return tool_text(str(result.get("output", "")))
    return tool_text(f"Errore dal worker: {result.get('error') or 'sconosciuto'}", True)


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    if not authorized(request):
        return JSONResponse(
            {"error": "non autorizzato"}, status_code=401, headers={"WWW-Authenticate": 'Bearer realm="omninode"'}
        )

    try:
        msg = await request.json()
    except ValueError:
        return rpc_error(None, -32700, "JSON non valido", 400)
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return rpc_error(None, -32600, "Richiesta JSON-RPC 2.0 non valida", 400)

    method = msg.get("method")
    req_id = msg.get("id")

    # Notifiche (senza id): nessuna risposta, 202 come da spec.
    if "id" not in msg:
        return Response(status_code=202)

    if method == "initialize":
        requested = (msg.get("params") or {}).get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
        return rpc_result(
            req_id,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "omninode-gateway", "version": "0.1.0"},
            },
        )

    if method == "ping":
        return rpc_result(req_id, {})

    if method == "tools/list":
        return rpc_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(args, dict):
            return rpc_error(req_id, -32602, "Parametri tools/call non validi")
        log.info("tools/call %s agent=%s", name, args.get("agent_id"))
        return rpc_result(req_id, await run_tool(name, args))

    return rpc_error(req_id, -32601, f"Metodo non supportato: {method}")


@app.get("/mcp", include_in_schema=False)
async def mcp_get() -> Response:
    # Nessun flusso SSE server->client: la spec consente 405.
    return Response(status_code=405, headers={"Allow": "POST"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mcp_gateway:app", host="127.0.0.1", port=8000)
