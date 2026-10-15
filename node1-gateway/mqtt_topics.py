"""
Omninode MQTT Topic Builder (v1 & Legacy)
- Gestione isolata delle versioni dei topic tramite OMNINODE_MQTT_TOPIC_VERSION
- Fail-fast all'avvio in caso di configurazione non valida
"""
from __future__ import annotations

import os
import re

SUPPORTED_VERSIONS = {"v1", "legacy"}
NODE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def get_topic_version() -> str:
    version = os.getenv("OMNINODE_MQTT_TOPIC_VERSION", "legacy").strip().lower()
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(f"Configurazione MQTT Topic non valida: OMNINODE_MQTT_TOPIC_VERSION='{version}' non è supportato. Usa 'v1' o 'legacy'.")
    return version


def validate_node_id(node_id: str) -> str:
    if not node_id or not NODE_ID_REGEX.match(node_id):
        raise ValueError(f"Node ID non valido per il routing MQTT: '{node_id}' contiene caratteri non sicuri o path traversal.")
    return node_id


class MQTTTopics:
    @staticmethod
    def tasks(node_id: str) -> str:
        nid = validate_node_id(node_id)
        version = get_topic_version()
        if version == "v1":
            return f"omninode/v1/nodes/{nid}/tasks"
        return f"omninode/nodes/{nid}/tasks"

    @staticmethod
    def responses(node_id: str) -> str:
        nid = validate_node_id(node_id)
        version = get_topic_version()
        if version == "v1":
            return f"omninode/v1/nodes/{nid}/responses"
        return f"omninode/nodes/{nid}/responses"

    @staticmethod
    def heartbeat(node_id: str) -> str:
        nid = validate_node_id(node_id)
        version = get_topic_version()
        if version == "v1":
            return f"omninode/v1/nodes/{nid}/heartbeat"
        return f"omninode/nodes/{nid}/heartbeat"