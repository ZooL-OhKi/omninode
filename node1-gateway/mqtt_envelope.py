"""
Omninode MQTT Canonical Message Envelope (v5.0)
- Schema version: 1 obbligatoria
- Idempotenza tramite message_id (UUID v4)
- Validazione rigorosa node_id contro identità MQTT autenticata
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal
from pydantic import BaseModel, Field, field_validator


class MQTTEnvelope(BaseModel):
    schema_version: Literal[1] = 1
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: Literal["task", "response", "heartbeat"]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: Literal["gateway", "node"]
    node_id: str
    task_id: str = "none"
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("node_id")
    @classmethod
    def validate_node_id_format(cls, v: str) -> str:
        import re
        if not v or not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"node_id non valido o contenente caratteri non sicuri: {v}")
        return v

    def verify_identity(self, authenticated_client_id: str) -> bool:
        """Verifica che il node_id dichiarato corrisponda all'identità MQTT autenticata."""
        expected_id = f"node-{self.node_id}" if self.actor == "node" else "gateway"
        # Se l'attore è gateway, l'utente autenticato deve essere gateway
        if self.actor == "gateway":
            return authenticated_client_id == "gateway"
        # Se l'attore è node, l'utente deve corrispondere rigorosamente
        return authenticated_client_id == expected_id