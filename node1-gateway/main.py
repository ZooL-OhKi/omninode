"""Omninode Gateway - FastAPI entry point."""
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from mqtt_service import MQTTService

# --- Configuration ---
OMNINODE_API_KEY = os.environ.get("OMNINODE_API_KEY", "omninode-super-secure-key-2026")

# --- FastAPI App ---
app = FastAPI(title="Omninode Gateway")

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

# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def startup() -> None:
    await mqtt_service.connect()
    # Start background work loop task here if needed

@app.on_event("shutdown")
async def shutdown() -> None:
    await mqtt_service.disconnect()

# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    # Mount static files (must be after all route definitions)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    uvicorn.run(app, host="0.0.0.0", port=8000)
