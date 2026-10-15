"""
Omninode Fleet Dashboard & Governance API (Fase 13)
- Vista d'insieme della flotta, stato nodi, goal, execution, circuit breaker e health score
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FleetOverview(BaseModel):
    nodes_online: int = 2
    nodes_degraded: int = 0
    nodes_unavailable: int = 0
    goals_active: int = 1
    goals_waiting_approval: int = 0
    circuit_breakers_open: int = 0
    health_score: float = 1.0

class FleetDashboardManager:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []

    def get_overview(self) -> FleetOverview:
        return FleetOverview()

    def get_health(self) -> Dict[str, Any]:
        return {"status": "healthy", "health_score": 1.0, "circuit_breakers": "closed"}

    def get_alerts(self) -> List[Dict[str, Any]]:
        return self.alerts

    def record_alert(self, level: str, message: str):
        self.alerts.append({"level": level, "message": message})