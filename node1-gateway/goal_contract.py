"""
Omninode Goal Contract & Validation (Fase 10)
- Definizione del contratto formale di goal con vincoli, sorgente e criteri di accettazione
"""
from __future__ import annotations

from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field

GoalPriority = Literal["low", "normal", "high", "critical"]
GoalSource = Literal["mcp", "api", "webhook", "scheduler"]

class GoalConstraints(BaseModel):
    max_attempts: int = 3
    max_wall_clock_seconds: int = 900
    max_file_writes: int = 10
    allowed_capabilities: List[str] = Field(default_factory=lambda: ["python"])

class GoalContract(BaseModel):
    schema_version: Literal[1] = 1
    goal_id: str
    title: str
    priority: GoalPriority = "normal"
    risk_tier: int = 0
    source: GoalSource = "mcp"
    source_identity: str = "system-admin"
    workspace: str = "confined-workspace"
    constraints: GoalConstraints = Field(default_factory=GoalConstraints)
    acceptance_criteria: List[str] = Field(default_factory=list)

def validate_goal_contract(contract: GoalContract) -> Dict[str, Any]:
    if not contract.goal_id or not contract.title:
        return {"valid": False, "reason": "Goal ID e titolo sono obbligatori."}
    if contract.risk_tier >= 4:
        return {"valid": False, "reason": "Rifiutato: Tier 4 (policy/ACL/audit) vietato all'agente autonomo."}
    if not contract.acceptance_criteria:
        return {"valid": False, "reason": "Contratto rifiutato: assenza di criteri di accettazione (acceptance_criteria)."}
    return {"valid": True, "reason": "Contratto validato con successo."}