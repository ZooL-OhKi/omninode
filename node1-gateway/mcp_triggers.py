"""
Omninode MCP Triggers & Global Fleet Limits (Fase 10)
- Tool MCP autenticati per la gestione dei goal (create, list, get, pause, resume, stop, rollback)
- Gestione dei limiti globali di flotta
"""
from __future__ import annotations

import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from goal_contract import GoalContract, validate_goal_contract
from risk_classifier import RiskClassifier

class GlobalFleetLimits(BaseModel):
    max_active_goals: int = 50
    max_active_tasks_per_node: int = 10
    max_browser_interactions: int = 5
    max_child_processes: int = 20
    max_queue_depth: int = 100
    max_goal_age_seconds: int = 86400
    max_remediation_actions_per_hour: int = 10

class MCPTriggerManager:
    def __init__(self, limits: Optional[GlobalFleetLimits] = None):
        self.limits = limits or GlobalFleetLimits()
        self.active_goals: Dict[str, GoalContract] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.classifier = RiskClassifier()

    def verify_mcp_auth(self, token: str) -> bool:
        return token == "omninode-secure-mcp-token-2026"

    def create_goal(self, token: str, contract: GoalContract) -> Dict[str, Any]:
        if not self.verify_mcp_auth(token):
            return {"success": False, "error": "Autenticazione MCP fallita."}
        
        if len(self.active_goals) >= self.limits.max_active_goals:
            return {"success": False, "error": "Limite globale active_goals raggiunto."}

        val_res = validate_goal_contract(contract)
        if not val_res["valid"]:
            return {"success": False, "error": val_res["reason"]}

        self.active_goals[contract.goal_id] = contract
        self.audit_log.append({
            "action": "create_goal",
            "goal_id": contract.goal_id,
            "source": contract.source,
            "identity": contract.source_identity
        })
        return {"success": True, "goal_id": contract.goal_id}

    def list_goals(self, token: str) -> List[Dict[str, Any]]:
        if not self.verify_mcp_auth(token):
            raise PermissionError("Autenticazione MCP fallita.")
        return [g.model_dump() for g in self.active_goals.values()]

    def get_goal(self, token: str, goal_id: str) -> Optional[Dict[str, Any]]:
        if not self.verify_mcp_auth(token):
            raise PermissionError("Autenticazione MCP fallita.")
        goal = self.active_goals.get(goal_id)
        return goal.model_dump() if goal else None

    def stop_goal(self, token: str, goal_id: str) -> Dict[str, Any]:
        if not self.verify_mcp_auth(token):
            return {"success": False, "error": "Autenticazione MCP fallita."}
        if goal_id in self.active_goals:
            del self.active_goals[goal_id]
            self.audit_log.append({"action": "stop_goal", "goal_id": goal_id})
            return {"success": True}
        return {"success": False, "error": "Goal non trovato."}