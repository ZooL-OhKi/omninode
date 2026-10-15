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
from audit_api import build_audit_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omninode.gateway")

MQTT_BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ["MQTT_PORT"])
MCP_SECRET = os.environ["MCP_SECRET"]
MQTT_CA_PATH = os.environ["MQTT_CA_PATH"]
MQTT_CERT_PATH = os.environ["MQTT_CERT_PATH"]
MQTT_KEY_PATH = os.environ["MQTT_KEY_PATH"]

active_nodes = {}
agent_routing = {}
pending_mcp_requests = {}
sse_clients = []
mqtt_ready = asyncio.Event()


def mqtt_tls_params() -> aiomqtt.TLSParameters:
    for path in (MQTT_CA_PATH, MQTT_CERT_PATH, MQTT_KEY_PATH):
        if not path or not os.path.isfile(path):
            raise RuntimeError(f"Certificato MQTT mancante o non leggibile: {path}")
    return aiomqtt.TLSParameters(
        ca_certs=MQTT_CA_PATH,
        certfile=MQTT_CERT_PATH,
        keyfile=MQTT_KEY_PATH,
    )


def mqtt_client() -> aiomqtt.Client:
    return aiomqtt.Client(
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        tls_params=mqtt_tls_params(),
    )


async def mqtt_listener_task() -> None:
    while True:
        try:
            async with mqtt_client() as client:
                await client.subscribe("omninode/v1/nodes/+/heartbeat", qos=1)
                await client.subscribe("omninode/v1/nodes/+/responses", qos=1)
                mqtt_ready.set()
                logger.info("MQTT connesso e sottoscritto ai topic v1")

                async for message in client.messages:
                    topic = str(message.topic)
                    try:
                        data = json.loads(message.payload.decode())
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        logger.warning("Payload JSON non valido da %s", topic)
                        continue

                    if topic.endswith("/heartbeat"):
                        node_id = topic.split("/")[3]
                        active_nodes[node_id] = {"last_seen": time.time(), "info": data}
                        for agent_id in data.get("supported_agents", []):
                            agent_routing[agent_id] = node_id
                        await broadcast("node_update", {n: d["info"] for n, d in active_nodes.items()})

                    elif topic.endswith("/responses"):
                        task_id = data.get("task_id")
                        future = pending_mcp_requests.get(task_id)
                        if future and not future.done():
                            future.set_result(data)

        except aiomqtt.MqttError as exc:
            mqtt_ready.clear()
            logger.warning("MQTT disconnesso: %s; reconnect tra 5 secondi", exc)
            await asyncio.sleep(5)


async def broadcast(event: str, payload: dict) -> None:
    message = f"event: {event}\ndata: {json.dumps(payload)}\n\n"
    for queue in list(sse_clients):
        await queue.put(message)


async def node_expiry_task() -> None:
    while True:
        now = time.time()
        expired = [node_id for node_id, data in active_nodes.items() if now - data.get("last_seen", 0) > 90]
        for node_id in expired:
            active_nodes.pop(node_id, None)
            for agent_id, node in list(agent_routing.items()):
                if node == node_id:
                    agent_routing.pop(agent_id, None)
        if expired:
            await broadcast("node_update", {n: d["info"] for n, d in active_nodes.items()})
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = asyncio.create_task(mqtt_listener_task())
    expiry = asyncio.create_task(node_expiry_task())
    yield
    listener.cancel()
    expiry.cancel()


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
    if not mqtt_ready.is_set():
        raise HTTPException(status_code=503, detail="MQTT non pronto")
    return {"status": "ready", "mqtt": True}


@app.get("/api/v1/stream")
async def sse_stream(request: Request):
    queue = asyncio.Queue()
    sse_clients.append(queue)
    await queue.put(f"event: node_update\ndata: {json.dumps({n: d['info'] for n, d in active_nodes.items()})}\n\n")

    async def generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                yield await queue.get()
        finally:
            sse_clients.remove(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")


@app.get("/api/v1/nodes")
def get_nodes():
    return {node_id: data["info"] for node_id, data in active_nodes.items()}


@app.post("/api/v1/approve", dependencies=[Depends(verify_mcp_auth)])
async def approve_task(payload: dict):
    task_id = payload.get("task_id")
    agent_id = payload.get("agent_id")
    decision = payload.get("decision")
    if not task_id or not agent_id or decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="task_id, agent_id e decision valida sono obbligatori")

    node_id = agent_routing.get(agent_id)
    if not node_id:
        raise HTTPException(status_code=409, detail="Nessun nodo online per l'agent richiesto")

    message = {
        "type": "task_approval",
        "task_id": task_id,
        "approved": decision == "approve",
    }
    async with mqtt_client() as client:
        await client.publish(f"omninode/v1/nodes/{node_id}/control", json.dumps(message), qos=1)
    return {"status": "ok", "node_id": node_id}


@app.post("/mcp", dependencies=[Depends(verify_mcp_auth)])
async def mcp_endpoint(request: Request):
    payload = await request.json()
    task_id = payload.get("id") or f"req-{os.urandom(8).hex()}"
    agent_id = payload.get("params", {}).get("agent_id", "agent_1")
    node_id = agent_routing.get(agent_id)
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
        async with mqtt_client() as client:
            await client.publish(MQTTTopics.tasks(node_id), json.dumps(envelope), qos=1)
            result = await asyncio.wait_for(future, timeout=20)
        return JSONResponse({"jsonrpc": "2.0", "id": task_id, "result": result})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "Timeout in attesa del worker"})
    finally:
        pending_mcp_requests.pop(task_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
