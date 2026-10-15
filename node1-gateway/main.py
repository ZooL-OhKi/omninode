"""Omninode Gateway - FastAPI entry point with unified MQTTService."""
import os
import json
import asyncio
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import aiomqtt

from mqtt_topics import MQTTTopics
from mqtt_service import mqtt_service
from audit_api import build_audit_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omninode.gateway")

MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MCP_SECRET = os.environ["MCP_SECRET"]
MQTT_CA_PATH = os.environ["MQTT_CA_PATH"]
MQTT_CERT_PATH = os.environ["MQTT_CERT_PATH"]
MQTT_KEY_PATH = os.environ["MQTT_KEY_PATH"]

pending_mcp_requests = mqtt_service.pending_requests
sse_clients_list: list[asyncio.Queue] = []


def mqtt_tls_params() -> aiomqtt.TLSParameters:
    for path in (MQTT_CA_PATH, MQTT_CERT_PATH, MQTT_KEY_PATH):
        if not path or not os.path.isfile(path):
            raise RuntimeError(f"Certificato MQTT mancante o non leggibile: {path}")
    return aiomqtt.TLSParameters(
        ca_certs=MQTT_CA_PATH,
        certfile=MQTT_CERT_PATH,
        keyfile=MQTT_KEY_PATH,
    )


async def broadcast_handler(event: str, payload: dict) -> None:
    message = f"event: {event}\ndata: {json.dumps(payload)}\n\n"
    for queue in list(sse_clients_list):
        await queue.put(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_store.init_db() if hasattr(task_store, "init_db") else None
    mqtt_service.set_broadcast_callback(broadcast_handler)
    await mqtt_service.start()
    yield
    await mqtt_service.stop()


app = FastAPI(title="OmniNode Gateway", lifespan=lifespan)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


async def verify_mcp_auth(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {MCP_SECRET}":
        raise HTTPException(status_code=401, detail="Token MCP non valido o mancante")


app.include_router(build_audit_router(verify_mcp_auth))


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if not mqtt_service.is_ready():
        raise HTTPException(status_code=503, detail="MQTT non pronto")
    return {"status": "ready", "mqtt": True}


@app.get("/api/v1/stream")
async def sse_stream(request: Request):
    queue = asyncio.Queue()
    sse_clients_list.append(queue)
    await queue.put(f"event: node_update\ndata: {json.dumps({n: d['info'] for n, d in mqtt_service.active_nodes.items()})}\\n\\n")

    async def generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                yield await queue.get()
        finally:
            sse_clients_list.remove(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")


@app.get("/api/v1/nodes")
def get_nodes():
    return {node_id: data["info"] for node_id, data in mqtt_service.active_nodes.items()}


@app.post("/api/v1/approve", dependencies=[Depends(verify_mcp_auth)])
async def approve_task(payload: dict):
    task_id = payload.get("task_id")
    agent_id = payload.get("agent_id")
    decision = payload.get("decision")
    if not task_id or not agent_id or decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="task_id, agent_id e decision valida sono obbligatori")

    node_id = mqtt_service.agent_routing.get(agent_id)
    if not node_id:
        raise HTTPException(status_code=409, detail="Nessun nodo online per l'agent richiesto")

    message = {
        "type": "task_approval",
        "task_id": task_id,
        "approved": decision == "approve",
    }
    control_topic = MQTTTopics.control(node_id) if hasattr(MQTTTopics, "control") else f"omninode/v1/nodes/{node_id}/control"
    await mqtt_service.publish(control_topic, json.dumps(message), qos=1)
    return {"status": "ok", "node_id": node_id}


@app.post("/mcp", dependencies=[Depends(verify_mcp_auth)])
async def mcp_endpoint(request: Request):
    payload = await request.json()
    task_id = payload.get("id") or f"req-{os.urandom(8).hex()}"
    agent_id = payload.get("params", {}).get("agent_id", "agent_1")
    node_id = mqtt_service.agent_routing.get(agent_id)
    if not node_id:
        raise HTTPException(status_code=409, detail="Nessun nodo online per l'agent richiesto")

    envelope = {
        "task_id": task_id,
        "task_type": payload.get("method", "unknown"),
        "payload": payload.get("params", {}),
        "submitted_at": int(time.time()),
    }
    future = asyncio.get_running_loop().create_future()
    pending_mcp_requests[task_id] = future

    try:
        task_topic = MQTTTopics.tasks(node_id)
        await mqtt_service.publish(task_topic, json.dumps(envelope), qos=1)
        result = await asyncio.wait_for(future, timeout=20)
        return JSONResponse({"jsonrpc": "2.0", "id": task_id, "result": result})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "Timeout in attesa del worker"})
    finally:
        pending_mcp_requests.pop(task_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
