from mqtt_topics import MQTTTopics
import json
import logging
import os
import ssl
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import paho.mqtt.client as mqtt

import task_store

logger = logging.getLogger(__name__)


class TaskTimeoutError(Exception):
    pass


class TaskRemoteError(Exception):
    pass


class TaskPublishError(Exception):
    pass


@dataclass
class PendingTask:
    event: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class NodeRecord:
    node_id: str
    status: str
    load: int
    last_seen: int
    metadata: dict[str, Any]


class MQTTService:
    """Thread-safe mTLS MQTT bridge using the OmniNode v1 contract."""

    def __init__(self) -> None:
        self.host = os.environ["MQTT_HOST"]
        self.port = int(os.environ["MQTT_PORT"])
        self.username = os.environ["MQTT_USERNAME"]
        self.password = os.environ["MQTT_PASSWORD"]
        self.ca_path = os.environ["MQTT_CA_PATH"]
        self.cert_path = os.environ["MQTT_CERT_PATH"]
        self.key_path = os.environ["MQTT_KEY_PATH"]
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.node_ttl = int(os.getenv("NODE_TTL_SECONDS", "90"))
        self.nodes: dict[str, NodeRecord] = {}
        self.pending_tasks: dict[str, PendingTask] = {}
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self.task_handler = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="omninode-gateway")
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.username_pw_set(self.username, self.password)

    def start(self) -> None:
        for path in (self.ca_path, self.cert_path, self.key_path):
            if not path or not os.path.isfile(path):
                raise RuntimeError(f"Certificato MQTT mancante o non leggibile: {path}")

        self.client.tls_set(
            ca_certs=self.ca_path,
            certfile=self.cert_path,
            keyfile=self.key_path,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        self.client.connect_async(self.host, self.port, self.keepalive)
        self.client.loop_start()
        logger.info("MQTT mTLS client avviato per %s:%s", self.host, self.port)

    def stop(self) -> None:
        self._ready.clear()
        self.client.loop_stop()
        self.client.disconnect()

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def set_task_handler(self, handler) -> None:
        self.task_handler = handler

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        if reason_code != 0:
            logger.error("Connessione MQTT fallita: %s", reason_code)
            return
        client.subscribe("omninode/v1/nodes/+/heartbeat", qos=1)
        client.subscribe("omninode/v1/nodes/+/responses", qos=1)
        self._ready.set()
        logger.info("MQTT connesso e sottoscritto ai topic v1")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, disconnect_flags: Any, reason_code: Any, properties: Any = None) -> None:
        self._ready.clear()
        if reason_code != 0:
            logger.warning("MQTT disconnesso in modo imprevisto (%s); reconnect automatico", reason_code)

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        parts = message.topic.split("/")
        if len(parts) != 5 or parts[0] != "omninode" or parts[1] != "v1" or parts[2] != "nodes":
            return

        node_id, event = parts[3], parts[4]
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("JSON non valido da %s", message.topic)
            return

        if event == "responses":
            task_id = payload.get("task_id")
            status = payload.get("status")
            if not task_id or not status:
                logger.warning("Risposta senza task_id/status da %s", node_id)
                return

            error_message = None
            if status == "completed":
                task_store.update_task_status(task_id, "completed", result=payload)
            elif status == "error":
                error = payload.get("error")
                error_message = error.get("message", "unknown remote error") if isinstance(error, dict) else str(error or "unknown remote error")
                task_store.update_task_status(task_id, "error", error=error_message)
            else:
                task_store.update_task_status(task_id, status)

            with self._lock:
                pending = self.pending_tasks.get(task_id)
                if pending:
                    if status == "completed":
                        pending.result = payload
                    elif status == "error":
                        pending.error = error_message
                    pending.event.set()
            return

        if event == "heartbeat":
            self.update_node(node_id, payload)

    def update_node(self, node_id: str, payload: dict[str, Any]) -> None:
        status = str(payload.get("status", "online"))
        try:
            load = max(0, min(100, int(payload.get("load", 0))))
        except (TypeError, ValueError):
            load = 0
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        with self._lock:
            self.nodes[node_id] = NodeRecord(node_id, status, load, int(time.time()), metadata)

    def get_nodes(self) -> list[dict[str, Any]]:
        self._expire_nodes()
        with self._lock:
            return [asdict(node) for node in self.nodes.values()]

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        self._expire_nodes()
        with self._lock:
            node = self.nodes.get(node_id)
            return asdict(node) if node else None

    def dispatch_task(self, node_id: str, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        node = self.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        if node["status"] == "offline":
            raise RuntimeError(f"node {node_id} is offline")

        task_id = f"task-{int(time.time() * 1000)}"
        task_store.create_task(task_id, task_type, payload)
        envelope = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "submitted_at": int(time.time()),
        }
        info = self.client.publish(MQTTTopics.tasks(node_id), json.dumps(envelope, separators=(",", ":")), qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            task_store.update_task_status(task_id, "error", error="unable to publish task to MQTT broker")
            raise RuntimeError("unable to publish task to MQTT broker")

        task_store.update_task_status(task_id, "dispatched")
        return {"status": "dispatched", "node_id": node_id, **envelope}

    def dispatch_task_sync(self, node_id: str, task_type: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        node = self.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        if node["status"] == "offline":
            raise RuntimeError(f"node {node_id} is offline")

        task_id = f"task-{int(time.time() * 1000)}"
        envelope = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "submitted_at": int(time.time()),
        }
        pending = PendingTask()
        with self._lock:
            self.pending_tasks[task_id] = pending

        try:
            info = self.client.publish(MQTTTopics.tasks(node_id), json.dumps(envelope, separators=(",", ":")), qos=1)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                raise TaskPublishError("unable to publish task to MQTT broker")
            if not pending.event.wait(timeout):
                raise TaskTimeoutError("task execution timed out")
            if pending.error:
                raise TaskRemoteError(pending.error)
            return pending.result or {}
        finally:
            with self._lock:
                self.pending_tasks.pop(task_id, None)

    def fabric_health(self) -> dict[str, Any]:
        nodes = self.get_nodes()
        online = [node for node in nodes if node["status"] == "online"]
        average_load = round(sum(node["load"] for node in online) / len(online)) if online else 0
        status = "healthy"
        if nodes and not online:
            status = "critical"
        elif average_load > 80:
            status = "warning"
        return {
            "total_nodes": len(nodes),
            "online_nodes": len(online),
            "offline_nodes": len(nodes) - len(online),
            "average_load": average_load,
            "health_status": status,
            "fabric_version": "1.0.0",
            "mqtt_ready": self.is_ready(),
        }

    def _expire_nodes(self) -> None:
        deadline = int(time.time()) - self.node_ttl
        with self._lock:
            for node in self.nodes.values():
                if node.last_seen < deadline:
                    node.status = "offline"
