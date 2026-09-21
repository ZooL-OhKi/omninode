import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


@dataclass
class NodeRecord:
    node_id: str
    status: str
    load: int
    last_seen: int
    metadata: dict[str, Any]


class MQTTService:
    """Thread-safe MQTT bridge between distributed nodes and the HTTP gateway."""

    def __init__(self) -> None:
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.tls_enabled = os.getenv("MQTT_TLS_ENABLED", "false").lower() == "true"
        self.node_ttl = int(os.getenv("NODE_TTL_SECONDS", "90"))
        self.nodes: dict[str, NodeRecord] = {}
        self._lock = threading.RLock()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="omninode-node1-gateway")
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if self.username:
            self.client.username_pw_set(self.username, self.password)
        if self.tls_enabled:
            self.client.tls_set()

    def start(self) -> None:
        """Connect asynchronously so application startup does not block."""
        self.client.connect_async(self.host, self.port, self.keepalive)
        self.client.loop_start()
        logger.info("MQTT client started for broker %s:%s", self.host, self.port)

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client stopped")

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        if reason_code != 0:
            logger.error("MQTT connection failed: %s", reason_code)
            return
        client.subscribe("omninode/nodes/+/heartbeat", qos=1)
        client.subscribe("omninode/nodes/+/status", qos=1)
        client.subscribe("omninode/nodes/+/results", qos=1)
        logger.info("MQTT connected and subscribed to node topics")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, disconnect_flags: Any, reason_code: Any, properties: Any = None) -> None:
        if reason_code != 0:
            logger.warning("MQTT disconnected unexpectedly (%s); reconnecting", reason_code)

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        parts = message.topic.split("/")
        if len(parts) != 4 or parts[0] != "omninode" or parts[1] != "nodes":
            return
        node_id, event = parts[2], parts[3]
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Discarding invalid JSON from %s", message.topic)
            return

        if event in {"heartbeat", "status"}:
            self.update_node(node_id, payload)
        elif event == "results":
            logger.info("Task result received from node %s", node_id)

    def update_node(self, node_id: str, payload: dict[str, Any]) -> None:
        status = str(payload.get("status", "online"))
        load = payload.get("load", 0)
        try:
            load = max(0, min(100, int(load)))
        except (TypeError, ValueError):
            load = 0

        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        with self._lock:
            self.nodes[node_id] = NodeRecord(
                node_id=node_id,
                status=status,
                load=load,
                last_seen=int(time.time()),
                metadata=metadata,
            )

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
        envelope = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "submitted_at": int(time.time()),
        }
        info = self.client.publish(
            f"omninode/nodes/{node_id}/tasks",
            json.dumps(envelope, separators=(",", ":")),
            qos=1,
        )
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError("unable to publish task to MQTT broker")
        return {"status": "dispatched", "node_id": node_id, **envelope}

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
            "fabric_version": "0.1.0",
        }

    def _expire_nodes(self) -> None:
        deadline = int(time.time()) - self.node_ttl
        with self._lock:
            for node in self.nodes.values():
                if node.last_seen < deadline:
                    node.status = "offline"
