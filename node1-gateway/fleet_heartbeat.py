"""
Omninode Fleet Orchestration & Swarm Intelligence (Fase 7)
- Heartbeat arricchito con capacity, health e capabilities
- Modello di leasing per prevenire doppie esecuzioni e gestire goal orphaned
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator

NodeStatus = Literal["online", "degraded", "draining", "offline", "suspect", "unavailable"]

class NodeCapacity(BaseModel):
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_goals: int = 0
    max_goals: int = 10
    queued_tasks: int = 0

class NodeHealth(BaseModel):
    mqtt: bool = True
    browser: bool = True
    workspace: bool = True
    executor: bool = True

class EnrichedHeartbeat(BaseModel):
    schema_version: Literal[1] = 1
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: NodeStatus = "online"
    capacity: NodeCapacity = Field(default_factory=NodeCapacity)
    capabilities: List[str] = Field(default_factory=lambda: ["python", "go", "browser"])
    health: NodeHealth = Field(default_factory=NodeHealth)
    version: str = "5.0.0"

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, v: str) -> str:
        import re
        if not v or not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"node_id non valido: {v}")
        return v

class GoalLease(BaseModel):
    goal_id: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str
    lease_expires_at: str
    execution_version: int = 1
    status: Literal["active", "orphaned", "abandoned", "superseded", "completed"] = "active"

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.lease_expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return True