import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from mqtt_service import MQTTService

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

API_KEY = os.getenv("OMNINODE_API_KEY")
if not API_KEY or API_KEY == "replace-with-a-long-random-secret":
    logger.warning("OMNINODE_API_KEY is not configured; protected endpoints will reject requests")

mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    mqtt_service.start()
    yield
    mqtt_service.stop()


app = FastAPI(title="Omninode Node1 Gateway", version="0.1.0", lifespan=lifespan)


class TaskRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


def require_api_key(x_omninode_key: str | None = Header(default=None)) -> None:
    if not API_KEY or x_omninode_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid Omninode key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "omninode-node1-gateway"}


@app.get("/nodes")
def list_nodes(x_omninode_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    require_api_key(x_omninode_key)
    return mqtt_service.get_nodes()


@app.get("/nodes/{node_id}")
def get_node(node_id: str, x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    node = mqtt_service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found")
    return node


@app.post("/nodes/{node_id}/tasks", status_code=status.HTTP_202_ACCEPTED)
def dispatch_task(node_id: str, request: TaskRequest, x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    try:
        return mqtt_service.dispatch_task(node_id, request.task_type, request.payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found") from None
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.get("/fabric/health")
def fabric_health(x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    return mqtt_service.fabric_health()
