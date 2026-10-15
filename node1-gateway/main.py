import os
import json
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import aiomqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "oracle-b.plini.net")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MCP_SECRET = os.getenv("MCP_SECRET", "super-secret-mcp-token")

# Stato globale in memoria
active_nodes = {}      # node_id -> {"last_seen": float, "info": dict}
agent_routing = {}     # agent_id -> node_id
pending_mcp_requests = {}
sse_clients = []       # Code asyncio.Queue per i client SSE connessi


async def mqtt_listener_task():
    async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
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
                sse_msg = f"event: approval_alert\ndata: {msg.payload.decode()}\n\n"
                for q in sse_clients:
                    await q.put(sse_msg)

            elif topic.startswith("omninode/nodes/") and topic.endswith("/heartbeat"):
                node_id = topic.split("/")[2]
                active_nodes[node_id] = {"last_seen": time.time(), "info": data}
                for agent_id in data.get("supported_agents", []):
                    agent_routing[agent_id] = node_id

                nodes_payload = {n_id: d["info"] for n_id, d in active_nodes.items()}
                nodes_msg = f"event: node_update\ndata: {json.dumps(nodes_payload)}\n\n"
                for q in sse_clients:
                    await q.put(nodes_msg)

            elif "/result/" in topic:
                task_id = topic.split("/")[-1]
                if task_id in pending_mcp_requests:
                    fut = pending_mcp_requests[task_id]
                    if not fut.done():
                        fut.set_result(data)


async def node_expiry_task():
    while True:
        now = time.time()
        expired_nodes = [n_id for n_id, d in active_nodes.items() if now - d.get("last_seen", 0) > 90]

        for node_id in expired_nodes:
            del active_nodes[node_id]
            keys_to_delete = [k for k, v in agent_routing.items() if v == node_id]
            for k in keys_to_delete:
                del agent_routing[k]

        if expired_nodes:
            nodes_payload = {n_id: d["info"] for n_id, d in active_nodes.items()}
            nodes_msg = f"event: node_update\ndata: {json.dumps(nodes_payload)}\n\n"
            for q in sse_clients:
                await q.put(nodes_msg)

        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener_task = asyncio.create_task(mqtt_listener_task())
    expiry_task = asyncio.create_task(node_expiry_task())
    yield
    listener_task.cancel()
    expiry_task.cancel()


app = FastAPI(title="Omninode Gateway", lifespan=lifespan)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


async def verify_mcp_auth(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {MCP_SECRET}":
        raise HTTPException(status_code=401, detail="Token MCP non valido o mancante")


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


@app.get("/api/v1/stream")
async def sse_stream(request: Request):
    q = asyncio.Queue()
    sse_clients.append(q)
    nodes_payload = {n_id: d["info"] for n_id, d in active_nodes.items()}
    await q.put(f"event: node_update\ndata: {json.dumps(nodes_payload)}\n\n")

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
def get_nodes():
    return {n_id: d["info"] for n_id, d in active_nodes.items()}


@app.post("/api/v1/approve")
async def approve_task(payload: dict):
    task_id = payload.get("task_id")
    decision = payload.get("decision")
    if decision not in ["approve", "reject"]:
        raise HTTPException(400, "Decisione non valida")
    msg = {"task_id": task_id, "approved": decision == "approve"}
    async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
        await client.publish("omninode/approvals/in", json.dumps(msg))
    return {"status": "ok", "message": "Decisione inoltrata al fabric"}


@app.post("/mcp", dependencies=[Depends(verify_mcp_auth)])
async def mcp_endpoint(request: Request):
    payload = await request.json()
    task_id = payload.get("id", f"req_{os.urandom(4).hex()}")
    agent_id = payload.get("params", {}).get("agent_id", "agent_1")
    target_node = agent_routing.get(agent_id, "ryzen")
    cmd_payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "action": payload.get("method"),
        "ref": payload.get("params", {}).get("subcmd", ""),
    }
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    pending_mcp_requests[task_id] = fut
    try:
        async with aiomqtt.Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
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
        return JSONResponse(status_code=504, content={"error": "Timeout in attesa del worker locale"})
    finally:
        pending_mcp_requests.pop(task_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
