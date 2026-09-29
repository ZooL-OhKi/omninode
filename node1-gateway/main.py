import os
import tempfile
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mqtt_service import MQTTService
from local_executor import LocalWorkspaceExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configurazione del Workspace Temporaneo isolato per Phase 1
WORKSPACE_ROOT = os.getenv(
    "OMNINODE_WORKSPACE_ROOT",
    os.path.join(tempfile.gettempdir(), "omninode_workspace")
)
os.makedirs(WORKSPACE_ROOT, exist_ok=True)
logger.info(f"Registered local workspace 'temporary' at: {WORKSPACE_ROOT}")

local_executor = LocalWorkspaceExecutor(roots={"temporary": WORKSPACE_ROOT})


def handle_local_task(node_id: str, task_envelope: dict) -> None:
    """Intercetta il task da MQTT, lo esegue localmente e pubblica il risultato correlato."""
    if node_id != "node-local":
        return

    task_id = task_envelope.get("task_id")
    task_type = task_envelope.get("task_type")
    payload = task_envelope.get("payload", {})

    logger.info(f"Node '{node_id}' received task '{task_type}' (ID: {task_id})")

    response = {"task_id": task_id, "status": "error", "error": "Unknown error"}

    try:
        # Phase 1: Supportiamo ESCLUSIVAMENTE workspace.write
        if task_type == "workspace.write":
            result = local_executor.write(
                workspace_id=payload.get("workspace_id", "temporary"),
                relative_path=payload.get("path"),
                content=payload.get("content")
            )
            response["status"] = "completed"
            response["data"] = result
            response["error"] = None
        else:
            response["error"] = f"Capability '{task_type}' denied or unsupported on local node."

    except PermissionError as pe:
        response["error"] = f"Policy Denial: {str(pe)}"
    except Exception as e:
        response["error"] = f"Execution Error: {str(e)}"

    mqtt_service.client.publish(
        f"omninode/nodes/{node_id}/results",
        json.dumps(response),
        qos=1
    )


# Inizializzazione del servizio MQTT
mqtt_service = MQTTService(
    broker_host=os.getenv("MQTT_BROKER_HOST", "localhost"),
    broker_port=int(os.getenv("MQTT_BROKER_PORT", "1883")),
    client_id="node-local-gateway"
)
mqtt_service.connect()

# Registrazione della callback per i task locali
mqtt_service.set_task_handler(handle_local_task)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: il servizio MQTT è già connesso globalmente
    logger.info("Omninode gateway startup complete")
    yield
    # Shutdown
    logger.info("Shutting down Omninode gateway")
    mqtt_service.disconnect()


app = FastAPI(title="Omninode Gateway", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok", "node_id": "node-local"}


@app.post("/workspace/write")
async def workspace_write(workspace_id: str, path: str, content: str):
    """
    Endpoint diretto per testare LocalWorkspaceExecutor senza passare da MQTT.
    Utile per debug durante la Phase 1.
    """
    try:
        result = local_executor.write(
            workspace_id=workspace_id,
            relative_path=path,
            content=content
        )
        return {"status": "completed", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
