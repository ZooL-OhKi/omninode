import json
import logging
import os
from typing import Callable, Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(self, broker_host: str, broker_port: int, client_id: str):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id

        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.task_handler = None

    def set_task_handler(self, handler):
        self.task_handler = handler

    def connect(self) -> None:
        logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()

    def disconnect(self) -> None:
        logger.info("Disconnecting from MQTT broker")
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Sottoscrizione ai topic di stato e risultati per tutti i nodi
            client.subscribe("omninode/nodes/+/status", qos=1)
            client.subscribe("omninode/nodes/+/results", qos=1)
            # Sottoscrizione al topic tasks per il nodo locale (Phase 1)
            client.subscribe("omninode/nodes/node-local/tasks", qos=1)
        else:
            logger.error(f"Failed to connect to MQTT broker, result code: {rc}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON payload from topic: {topic}")
            return

        # Estrai node_id ed event type dal topic
        # Topic pattern: omninode/nodes/{node_id}/{event}
        parts = topic.split("/")
        if len(parts) != 4 or parts[0] != "omninode" or parts[1] != "nodes":
            logger.warning(f"Unexpected topic format: {topic}")
            return

        node_id = parts[2]
        event = parts[3]

        # Intercettazione evento tasks per il nodo locale
        if event == "tasks":
            if self.task_handler:
                try:
                    self.task_handler(node_id, payload)
                except Exception as e:
                    logger.error(f"Task handler error for {node_id}: {e}")
            return

        # Log degli altri eventi (status, results, ecc.)
        logger.debug(f"Received {event} from node '{node_id}': {payload}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection, result code: {rc}")
        else:
            logger.info("MQTT client disconnected cleanly")

    def publish_status(self, node_id: str, status: str, details: Optional[dict] = None) -> None:
        topic = f"omninode/nodes/{node_id}/status"
        message = {
            "node_id": node_id,
            "status": status,
            "details": details or {}
        }
        self.client.publish(topic, json.dumps(message), qos=1)
        logger.debug(f"Published status to {topic}: {message}")

    def publish_result(self, node_id: str, result: dict) -> None:
        topic = f"omninode/nodes/{node_id}/results"
        self.client.publish(topic, json.dumps(result), qos=1)
        logger.debug(f"Published result to {topic}: {result}")
