"""Omninode MQTT Service - Unified async owner for mTLS communication."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from typing import Any, Callable, Optional

import aiomqtt

from mqtt_topics import MQTTTopics
import task_store

logger = logging.getLogger("omninode.mqtt_service")


class TaskTimeoutError(Exception):
    pass


class TaskRemoteError(Exception):
    pass


class TaskPublishError(Exception):
    pass


class MQTTService:
    """Unified async MQTT bridge and connection manager for the gateway."""

    def __init__(self) -> None:
        self.broker = os.environ["MQTT_BROKER"]
        self.port = int(os.environ["MQTT_PORT"])
        self.ca_path = os.environ["MQTT_CA_PATH"]
        self.cert_path = os.environ["MQTT_CERT_PATH"]
        self.key_path = os.environ["MQTT_KEY_PATH"]
        
        self.active_nodes: dict[str, dict[str, Any]] = {}
        self.agent_routing: dict[str, str] = {}
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.sse_clients: list[asyncio.Queue] = []  # type: ignore[assignment]
        self.mqtt_ready = asyncio.Event()

        self._client: Optional[aiomqtt.Client] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._expiry_task: Optional[asyncio.Task] = None
        self._broadcast_callback: Optional[Callable[[str, dict[str, Any]], Any]] = None

    def _tls_params(self) -> aiomqtt.TLSParameters:
        for path in (self.ca_path, self.cert_path, self.key_path):
            if not path or not os.path.isfile(path):
                raise RuntimeError(f"Certificato MQTT mancante o non leggibile: {path}")
        return aiomqtt.TLSParameters(
            ca_certs=self.ca_path,
            certfile=self.cert_path,
            keyfile=self.key_path,
        )

    def is_ready(self) -> bool:
        return self.mqtt_ready.is_set()

    def set_broadcast_callback(self, cb: Callable[[str, dict[str, Any]], Any]) -> None:
        self._broadcast_callback = cb

    async def _broadcast(self, event: str, payload: dict[str, Any]) -> None:
        if self._broadcast_callback:
            await self._broadcast_callback(event, payload)

    async def start(self) -> None:
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listener_loop())
        if self._expiry_task is None or self._expiry_task.done():
            self._expiry_task = asyncio.create_task(self._node_expiry_loop())
        logger.info("MQTTService avviato.")

    async def stop(self) -> None:
        self.mqtt_ready.clear()
        if self._listener_task:
            self._listener_task.cancel()
        if self._expiry_task:
            self._expiry_task.cancel()
        logger.info("MQTTService fermato.")

    async def publish(self, topic: str, payload: str | dict[str, Any], qos: int = 1) -> None:
        if isinstance(payload, dict):
            data = json.dumps(payload)
        else:
            data = payload

        if self._client is not None:
            await self._client.publish(topic, data, qos=qos)
        else:
            async with aiomqtt.Client(
                hostname=self.broker,
                port=self.port,
                tls_params=self._tls_params(),
            ) as client:
                await client.publish(topic, data, qos=qos)

    async def _listener_loop(self) -> None:
        backoff = 1
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=self.broker,
                    port=self.port,
                    tls_params=self._tls_params(),
                ) as client:
                    self._client = client
                    await client.subscribe("omninode/v1/nodes/+/heartbeat", qos=1)
                    await client.subscribe("omninode/v1/nodes/+/responses", qos=1)
                    self.mqtt_ready.set()
                    logger.info("MQTT connesso e sottoscritto ai topic v1 con mTLS.")
                    backoff = 1

                    async for message in client.messages:
                        await self._handle_message(message)

            except (aiomqtt.MqttError, asyncio.CancelledError) as exc:
                self._client = None
                self.mqtt_ready.clear()
                if isinstance(exc, asyncio.CancelledError):
                    break
                logger.warning("MQTT disconnesso: %s; riconnessione tra %ds", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(30, backoff * 2 + random.uniform(0, 1))
            except Exception as exc:
                self._client = None
                self.mqtt_ready.clear()
                logger.error("Errore imprevisto nel listener MQTT: %s; riprova tra 5s", exc)
                await asyncio.sleep(5)

    async def _handle_message(self, message: aiomqtt.Message) -> None:
        topic = str(message.topic)
        parts = topic.split("/")
        if len(parts) < 5 or parts[0] != "omninode" or parts[1] != "v1" or parts[2] != "nodes":
            return

        node_id, event = parts[3], parts[4]
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Payload JSON non valido da %s", topic)
            return

        if event == "heartbeat":
            self.active_nodes[node_id] = {"last_seen": asyncio.get_running_loop().time(), "info": payload}
            for agent_id in payload.get("supported_agents", []):
                self.agent_routing[agent_id] = node_id
            nodes_info = {n: d["info"] for n, d in self.active_nodes.items()}
            await self._broadcast("node_update", nodes_info)

        elif event == "responses":
            task_id = payload.get("task_id")
            status = payload.get("status")
            if not task_id or not status:
                logger.warning("Risposta priva di task_id o status da %s", node_id)
                return

            if status == "completed":
                task_store.update_task_status(task_id, "completed", result=payload)
            elif status == "error":
                err = payload.get("error")
                err_msg = err.get("message", "unknown remote error") if isinstance(err, dict) else str(err or "unknown remote error")
                task_store.update_task_status(task_id, "error", error=err_msg)
            else:
                task_store.update_task_status(task_id, status)

            future = self.pending_requests.get(task_id)
            if future and not future.done():
                future.set_result(payload)

    async def _node_expiry_loop(self) -> None:
        while True:
            await asyncio.sleep(15)
            now = asyncio.get_running_loop().time()
            expired = [nid for nid, data in self.active_nodes.items() if now - data.get("last_seen", 0) > 90]
            for nid in expired:
                self.active_nodes.pop(nid, None)
                for aid, node in list(self.agent_routing.items()):
                    if node == nid:
                        self.agent_routing.pop(aid, None)
            if expired:
                nodes_info = {n: d["info"] for n, d in self.active_nodes.items()}
                await self._broadcast("node_update", nodes_info)


mqtt_service = MQTTService()
