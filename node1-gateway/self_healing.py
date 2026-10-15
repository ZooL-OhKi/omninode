"""
Omninode Self-Healing & Health Score Engine (Fase 8)
- Calcolo dell'Health Score multi-fattoriale per nodi e flotta
- Workflow di remediation limitato, sicuro e auditato
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
RemediationStatus = Literal["pending", "approved", "executing", "completed", "failed", "rolled_back"]

class HealthScore(BaseModel):
    scope_id: str
    score: float = 100.0 # Scala 0.0 - 100.0
    status: Literal["healthy", "degraded", "critical"] = "healthy"
    components: Dict[str, float] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def calculate_node_health(heartbeat_age: float, success_rate: float, p95_latency: float, rollback_rate: float) -> HealthScore:
    """Calcola l'health score di un nodo basato su metriche chiave."""
    score = 100.0
    components = {}

    # Penalità età heartbeat
    hb_penalty = min(25.0, (heartbeat_age / 30.0) * 25.0)
    components["heartbeat_age"] = hb_penalty
    score -= hb_penalty

    # Penalità tasso di successo (success_rate 0.0 - 1.0)
    success_penalty = (1.0 - success_rate) * 40.0
    components["success_rate"] = success_penalty
    score -= success_penalty

    # Penalità latenza P95 (> 30s)
    lat_penalty = min(20.0, max(0.0, (p95_latency - 30.0) / 3.0))
    components["p95_latency"] = lat_penalty
    score -= lat_penalty

    # Penalità rollback rate
    rb_penalty = rollback_rate * 15.0
    components["rollback_rate"] = rb_penalty
    score -= rb_penalty

    score = max(0.0, min(100.0, score))
    status = "healthy"
    if score < 50.0:
        status = "critical"
    elif score < 80.0:
        status = "degraded"

    return HealthScore(
        scope_id="node",
        score=score,
        status=status,
        components=components
    )

class RemediationWorkflow(BaseModel):
    remediation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    anomaly_id: str
    scope: str
    risk_level: RiskLevel
    actions: List[str]
    max_duration_seconds: int = 60
    max_actions: int = 3
    verification_required: bool = True
    rollback_plan: str = "restore_previous_state"
    approval_required: bool = False
    status: RemediationStatus = "pending"

def evaluate_remediation_safety(action: str, risk_level: RiskLevel) -> Dict[str, Any]:
    """Valuta se un'azione di remediation è consentita o richiede blocco/approvazione."""
    forbidden_actions = [
        "modify_policy", "modify_acl", "modify_keys", "modify_audit",
        "install_dependencies", "update_dependencies", "unauthorized_command",
        "delete_checkpoint", "restart_gateway", "fleet_wide_propagation"
    ]

    if action in forbidden_actions or risk_level in ("high", "critical"):
        return {
            "allowed": False,
            "requires_human": True,
            "reason": f"Azione '{action}' o livello di rischio '{risk_level}' vietati senza esplicita approvazione umana."
        }

    allowed_safe_actions = ["restart_worker", "purge_cache", "reassign_task", "reduce_concurrency", "quarantine_capability"]
    if action not in allowed_safe_actions:
        return {
            "allowed": False,
            "requires_human": True,
            "reason": f"Azione '{action}' non riconosciuta nel perimetro di sicurezza sicuro."
        }

    return {
        "allowed": True,
        "requires_human": False,
        "reason": f"Azione '{action}' autorizzata per esecuzione automatica controllata."
    }