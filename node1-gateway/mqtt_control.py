"""
Omninode Distributed Control Plane MQTT (Fase 6)
- Gestione dei comandi di controllo distribuiti (pause, resume, stop, rollback, health_check)
- Validazione di request_id (idempotenza), expires_at (scadenza) e identità node_id
- Mapping degli stati e transizioni consentite
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

CommandType = Literal["pause", "resume", "stop", "rollback", "health_check"]
AllowedStates = Literal["running", "paused", "interrupted", "budget_exhausted", "completed", "failed", "rolled_back"]

STATE_TRANSITIONS = {
    "running": ["pause", "stop", "rollback"],
    "paused": ["resume", "stop", "rollback"],
    "interrupted": ["resume", "stop", "rollback"],
    "budget_exhausted": ["stop", "rollback"],
    "completed": [],
    "failed": ["stop", "rollback"],
    "rolled_back": []
}

class ControlCommandEnvelope(BaseModel):
    schema_version: Literal[1] = 1
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: Literal["control"] = "control"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    actor: Literal["gateway"] = "gateway"
    node_id: str
    goal_id: str
    command: CommandType
    reason: Literal["operator", "budget", "policy", "verification_failure"] = "operator"
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("node_id")
    @classmethod
    def validate_node_id_format(cls, v: str) -> str:
        import re
        if not v or not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"node_id non valido: {v}")
        return v

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return now > exp
        except Exception:
            return True

    def verify_identity(self, authenticated_client_id: str) -> bool:
        return authenticated_client_id == "gateway"

def validate_command_for_state(current_state: str, command: str) -> bool:
    allowed = STATE_TRANSITIONS.get(current_state, [])
    return command in allowed