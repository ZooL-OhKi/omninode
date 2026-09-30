"""Omninode Gateway - FastAPI entry point.

Novita': espone l'endpoint MCP /mcp (Streamable HTTP, JSON-RPC) implementato in
mcp_gateway.py. L'endpoint si attiva SOLO se sono impostate OMNI_MCP_TOKEN
(minimo 32 caratteri) e MQTT_HOST; altrimenti il gateway parte come prima,
senza /mcp (fail closed).
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from mqtt_service import MQTTService
import task_store
import mcp_gateway

log = logging.getLogger("omninode.main")

# --- Configuration ---
# ATTENZIONE: il valore di default e' pubblico nel repository. Impostare
# OMNINODE_API_KEY nell'ambiente di produzione (vedi nota di sicurezza).
OMNINODE_API_KEY = os.environ.get("OMNINODE_API_KEY", "omninode-super-secure-key-2026")

# Indirizzo di ascolto: loopback, perche' il traffico arriva da cloudflared.
BIND_HOST = os.environ.get("OMNI_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("OMNI_PORT", "8000"))

MCP_ENABLED = len(mcp_gateway.MCP_TOKEN) >= 32 and bool(mcp_gateway.MQTT_HOST)


# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(_: FastAPI):
    task_store.init_db()
    mqtt_service.start()
    if MCP_ENABLED:
        mcp_gateway.bridge.start()
        log.info("Endpoint /mcp attivo")
    else:
        log.warning("Endpoint /mcp DISATTIVATO: impostare OMNI_MCP_TOKEN (>=32 caratteri) e MQTT_HOST")
    try:
        yield
    finally:
        if MCP_ENABLED:
            await mcp_gateway.bridge.stop()
        mqtt_service.stop()


# --- FastAPI App ---
app = FastAPI(title="Omninode Gateway", lifespan=lifespan)

# --- Services ---
mqtt_service = MQTTService()


# --- Auth Helper ---
def require_api_key(x_omninode_key: str | None) -> None:
    if x_omninode_key != OMNINODE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# --- API Endpoints ---
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- MCP (registrato solo se configurato) ---
if MCP_ENABLED:
    app.add_api_route("/mcp", mcp_gateway.mcp_endpoint, methods=["POST"])
    app.add_api_route("/mcp", mcp_gateway.mcp_get, methods=["GET"], include_in_schema=False)


# --- Frontend & Dashboard Endpoints ---

# Endpoint per recuperare lo stato dei nodi connessi al broker MQTT
@app.get("/api/v1/nodes")
def get_active_nodes(x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    return {"nodes": mqtt_service.get_nodes()}


# Endpoint per servire la dashboard
@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


# --- Static files (anche con "uvicorn main:app", non solo con __main__) ---
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn

    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
