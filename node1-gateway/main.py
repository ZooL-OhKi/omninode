"""Omninode Gateway - FastAPI entry point.

Integra:
- MCP endpoint (/mcp) con auth Bearer
- SSE per aggiornamenti real-time della dashboard
- Listener MQTT (mTLS) per alert, heartbeat e risultati
- Routing dinamico agent_id -> node_id
- Endpoint /api/v1/approve per approvazioni human-in-the-loop
"""
import os
import ssl
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import aiomqtt
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

log = logging.getLogger("omninode.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# --- Configurazione ---
MQTT_BROKER = os.getenv("MQTT_BROKER", "oracle-b.plini.net")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_CA = os.getenv("MQTT_CA", "certs/ca.crt")
MQTT_CERT = os.getenv("MQTT_CERT", "certs/client.crt")
MQTT_KEY = os.getenv("MQTT_KEY", "certs/client.key")
MCP_SECRET = os.getenv("MCP_SECRET", "super-secret-mcp-token")
BIND_HOST = os.getenv("OMNI_BIND", "127.0.0.1")
BIND_PORT = int(os.getenv("OMNI_PORT", "8000"))

# --- Stato in memoria ---
active_nodes: Dict[str, Any] = {}
agent_routing: Dict[str, str] = {}
pending_mcp_requests: Dict[str, asyncio.Future] = {}
sse_clients: List[asyncio.Queue] = []


def _mqtt_tls_context() -> ssl.SSLContext:
    """Costruisce il contesto TLS per MQTT mTLS."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(MQTT_CA)
    ctx.load_cert_chain(MQTT_CERT, MQTT_KEY)
    return ctx


async def mqtt_listener_task() -> None:
    """Ascolta alert, heartbeat e risultati MQTT e inoltra ai client SSE."""
    async with aiomqtt.Client(
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        tls_context=_mqtt_tls_context(),
        identifier="omninode-gateway-listener",
    ) as client:
        await client.subscribe("omninode/alerts/approval")
        await client.subscribe("omninode/nodes/+/heartbeat")
        await client.subscribe("omninode/nodes/+/result/+")

        async for msg in client.messages:
            topic = str(msg.topic)
            try:
                data = json.loads(msg.payload.decode())
            except Exception:
                continue

            if topic == "omninode/alerts/approval":
                # Inoltra a tutti i client SSE
                sse_msg = f"event: approval_alert\ndata: {json.dumps(data)}\n\n"
                for q in sse_clients:
                    await q.put(sse_msg)

            elif topic.startswith("omninode/nodes/") and topic.endswith("/heartbeat"):
                node_id = topic.split("/")[2]
                active_nodes[node_id] = data
                for agent_id in data.get("supported_agents", []):
                    agent_routing[agent_id] = node_id
                nodes_msg = f"event: node_update\ndata: {json.dumps(active_nodes)}\n\n"
                for q in sse_clients:
                    await q.put(nodes_msg)

            elif "/result/" in topic:
                task_id = topic.split("/")[-1]
                if task_id in pending_mcp_requests:
                    fut = pending_mcp_requests[task_id]
                    if not fut.done():
                        fut.set_result(data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(mqtt_listener_task())
    yield
    task.cancel()


app = FastAPI(title="Omninode Gateway", lifespan=lifespan)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


async def verify_mcp_auth(authorization: str = Header(None)) -> None:
    if not authorization or authorization != f"Bearer {MCP_SECRET}":
        raise HTTPException(status_code=401, detail="Token non valido")


# --- Endpoints ---


@app.get("/")
def serve_dashboard() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/v1/stream")
async def sse_stream(request: Request) -> StreamingResponse:
    """SSE per aggiornamenti real-time della Bento Box UI."""
    q: asyncio.Queue = asyncio.Queue()
    sse_clients.append(q)
    await q.put(f"event: node_update\ndata: {json.dumps(active_nodes)}\n\n")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = await q.get()
                yield msg
        finally:
            sse_clients.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/v1/nodes")
def get_nodes() -> Dict[str, Any]:
    return active_nodes


@app.post("/api/v1/approve")
async def approve_task(payload: dict) -> dict:
    """Riceve la decisione dalla UI e la invia al worker Go via MQTT."""
    task_id = payload.get("task_id")
    decision = payload.get("decision")
    if decision not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Decisione non valida")

    msg = {"task_id": task_id, "approved": decision == "approve"}
    async with aiomqtt.Client(
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        tls_context=_mqtt_tls_context(),
    ) as client:
        await client.publish("omninode/approvals/in", json.dumps(msg))
    return {"status": "ok", "message": "Decisione inviata al fabric"}


@app.post("/mcp", dependencies=[Depends(verify_mcp_auth)])
async def mcp_endpoint(request: Request) -> JSONResponse:
    """Endpoint per chiamate MCP Remote da Claude/ChatGPT/Gemini."""
    payload = await request.json()
    task_id = payload.get("id", f"req_{os.urandom(4).hex()}")
    params = payload.get("params", {})
    agent_id = params.get("agent_id", "agent_1")
    target_node = agent_routing.get(agent_id, "ryzen")

    method = payload.get("method", "")
    action = "web_snapshot" if method == "web_snapshot" else "web_click" if method == "web_click" else method
    ref = params.get("ref")

    cmd_payload = {"task_id": task_id, "agent_id": agent_id, "action": action, "ref": ref}

    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    pending_mcp_requests[task_id] = fut

    try:
        async with aiomqtt.Client(
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            tls_context=_mqtt_tls_context(),
        ) as client:
            await client.publish(f"omninode/nodes/{target_node}/cmd/{task_id}", json.dumps(cmd_payload))
            result = await asyncio.wait_for(fut, timeout=20.0)
            if result.get("status") == "pending_approval":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": task_id,
                    "result": {"content": [{"type": "text", "text": result.get("output")}]},
                })
            return JSONResponse({"jsonrpc": "2.0", "id": task_id, "result": result})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "Timeout worker locale"})
    finally:
        pending_mcp_requests.pop(task_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
