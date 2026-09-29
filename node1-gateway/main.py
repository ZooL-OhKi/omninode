import logging
import os
import tempfile
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import AnyHttpUrl, BaseModel, Field

from mqtt_service import MQTTService, TaskPublishError, TaskRemoteError, TaskTimeoutError, NodeRecord
import task_store

from audit import AuditEventEngine
from policy_engine import PolicyEngine
from workspace_manager import WorkspaceManager
from test_executor import CommandExecutor
from work_loop import AutonomousWorkLoop
from browser_runtime import BiometricBrowserRuntime
from playwright.async_api import async_playwright
from local_executor import LocalWorkspaceExecutor

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

API_KEY = os.getenv("OMNINODE_API_KEY")
if not API_KEY or API_KEY == "replace-with-a-long-random-secret":
    logger.warning("OMNINODE_API_KEY is not configured; protected endpoints will reject requests")

mqtt_service = MQTTService()
audit_engine = AuditEventEngine()
policy_engine = PolicyEngine(audit_engine)

# ==========================================
# PHASE 1: LOOPBACK LOCAL VERTICAL SLICE
# ==========================================

# 1. Configurazione del Workspace Temporaneo isolato per Phase 1
WORKSPACE_ROOT = os.getenv("OMNINODE_WORKSPACE_ROOT", os.path.join(tempfile.gettempdir(), "omninode_workspace"))
os.makedirs(WORKSPACE_ROOT, exist_ok=True)
logger.info(f"Registered local workspace 'temporary' at: {WORKSPACE_ROOT}")

local_executor = LocalWorkspaceExecutor(roots={"temporary": WORKSPACE_ROOT})

# 2. Handler per l'esecuzione sicura dei task locali via MQTT
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
        # Supportiamo ESCLUSIVAMENTE workspace.write per questa fase
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

mqtt_service.set_task_handler(handle_local_task)

# 3. Registrazione FORZATA del nodo locale (evita errore 404 Node Not Found per i test loopback)
# Impostiamo last_seen a 24h nel futuro per non farlo espellere mai
mqtt_service.nodes["node-local"] = NodeRecord(
    node_id="node-local",
    status="online",
    load=0,
    last_seen=int(time.time()) + 86400,
    metadata={"type": "local-executor"}
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task_store.init_db()  # Inizializzazione DB SQLite per Phase 2
    mqtt_service.start()
    yield
    mqtt_service.stop()

app = FastAPI(title="Omninode Node1 Gateway", version="0.1.0", lifespan=lifespan)

class TaskRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)

class BrowseRequest(BaseModel):
    url: AnyHttpUrl
    extract_content: Literal["markdown", "text", "html"] = "markdown"
    timeout_seconds: int = Field(default=30, ge=1, le=120)

class BrowseResponse(BaseModel):
    title: str
    content: str
    node_id: str
    format: Literal["markdown", "text", "html"]
    request_id: str
    status: Literal["completed"]

class GoalRequest(BaseModel):
    objective: str = Field(..., description="Obiettivo operativo assegnato all'agente")
    workspace_id: str = Field(..., description="ID univoco del workspace isolato")
    commands: list[list[str]] = Field(default=[["python", "-m", "pytest", "-q"]])
    max_iterations: int = Field(default=3, ge=1, le=10)
    max_duration_seconds: int = Field(default=900, ge=10, le=3600)

class AutonomousBrowseGoalRequest(BaseModel):
    url: AnyHttpUrl = Field(..., description="URL di destinazione per l'agente")
    action_type: Literal["extract", "click_and_type"] = "extract"
    target_selector: str | None = Field(default=None, description="Selettore CSS per interazioni mirate")
    input_text: str | None = Field(default=None, description="Testo da digitare eventualmente")

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

@app.get("/api/v1/tasks/{task_id}")
def get_task_status(task_id: str, x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    
    task_record = task_store.get_task(task_id)
    if not task_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    # Ripristiniamo i JSON salvati come stringhe in dizionari Python per la formattazione della risposta API
    if task_record.get("payload") and isinstance(task_record["payload"], str):
        try:
            task_record["payload"] = json.loads(task_record["payload"])
        except json.JSONDecodeError:
            pass
            
    if task_record.get("result") and isinstance(task_record["result"], str):
        try:
            task_record["result"] = json.loads(task_record["result"])
        except json.JSONDecodeError:
            pass

    return task_record

@app.post("/api/v1/browse", response_model=BrowseResponse)
async def browse_webpage(request: BrowseRequest, x_omninode_key: str | None = Header(default=None)):
    require_api_key(x_omninode_key)

    nodes = mqtt_service.get_nodes()
    online_nodes = [n for n in nodes if n.get("status") == "online"]
    if not online_nodes:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="no online nodes available")

    best_node = min(online_nodes, key=lambda n: n.get("load", 0))
    node_id = best_node["node_id"]

    payload = {
        "url": str(request.url),
        "extract_content": request.extract_content,
    }

    try:
        res = await run_in_threadpool(
            mqtt_service.dispatch_task_sync,
            node_id,
            "browse_webpage",
            payload,
            float(request.timeout_seconds),
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="node not found")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except TaskPublishError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except TaskTimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="task timeout exceeded")
    except TaskRemoteError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    data = res.get("data", {})
    return BrowseResponse(
        title=data.get("title", ""),
        content=data.get("content", ""),
        node_id=data.get("node_id", node_id),
        format=request.extract_content,
        request_id=res.get("task_id", "unknown"),
        status="completed",
    )

@app.post("/api/v1/goals")
def run_autonomous_goal(goal: GoalRequest, x_omninode_key: str | None = Header(default=None)):
    require_api_key(x_omninode_key)

    agent_id = "oracle-agent-01"
    goal_id = f"goal-{goal.workspace_id}"
    workspace_path = os.path.abspath(f"./workspaces/{goal.workspace_id}")

    policy_engine.grant({
        "agent_id": agent_id,
        "goal_id": goal_id,
        "capability": "workspace.write",
        "workspace": workspace_path
    })
    policy_engine.grant({
        "agent_id": agent_id,
        "goal_id": goal_id,
        "capability": "workspace.read",
        "workspace": workspace_path
    })
    policy_engine.grant({
        "agent_id": agent_id,
        "goal_id": goal_id,
        "capability": "process.run",
        "workspace": workspace_path
    })

    wm = WorkspaceManager(workspace_path, policy_engine, agent_id, goal_id)
    executor = CommandExecutor(policy_engine, agent_id, goal_id, workspace_path)
    loop = AutonomousWorkLoop(wm, executor)

    result = loop.execute_goal(goal.dict())
    return result

@app.post("/api/v1/autonomous-browse")
async def run_autonomous_browse(goal: AutonomousBrowseGoalRequest, x_omninode_key: str | None = Header(default=None)):
    """Esegue una sessione di navigazione web biometrica e anti-detection in autonomia."""
    require_api_key(x_omninode_key)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Applica le patch anti-detection avanzate
            await BiometricBrowserRuntime.apply_stealth_patches(page)

            # Navigazione verso l'obiettivo
            await page.goto(str(goal.url), timeout=60000)

            result_data = {"status": "success", "url": str(goal.url)}

            if goal.action_type == "click_and_type" and goal.target_selector:
                if goal.input_text:
                    await BiometricBrowserRuntime.human_type(page, goal.target_selector, goal.input_text)
                else:
                    await BiometricBrowserRuntime.human_move_and_click(page, goal.target_selector)
                result_data["action_performed"] = goal.action_type

            # Estrazione del contenuto testuale o HTML della pagina
            content = await page.content()
            title = await page.title()

            result_data["title"] = title
            result_data["content_snippet"] = content[:1000]

            await browser.close()
            return result_data

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Autonomous browse failed: {str(exc)}")

@app.get("/fabric/health")
def fabric_health(x_omninode_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_omninode_key)
    return mqtt_service.fabric_health()
