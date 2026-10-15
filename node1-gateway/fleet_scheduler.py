"""
Omninode Fleet Scheduler & Circuit Breaker (Fase 7)
- Selezione intelligente del nodo basata su salute, capacità e carico
- Gestione dello stato del Circuit Breaker (closed, open, half_open) per nodo
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class CircuitBreaker(BaseModel):
    node_id: str
    state: str = "closed" # closed, open, half_open
    failure_count: int = 0
    failure_threshold: int = 5
    last_failure_time: float = 0.0
    recovery_timeout_seconds: float = 60.0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        if self.state in ("open", "half_open"):
            self.state = "closed"
            self.failure_count = 0
        elif self.state == "closed":
            if self.failure_count > 0:
                self.failure_count -= 1

    def check_state(self) -> str:
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout_seconds:
                self.state = "half_open"
        return self.state

class CapacityScheduler:
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create_cb(self, node_id: str) -> CircuitBreaker:
        if node_id not in self.circuit_breakers:
            self.circuit_breakers[node_id] = CircuitBreaker(node_id=node_id)
        return self.circuit_breakers[node_id]

    def select_best_node(self, nodes_heartbeats: List[Dict[str, Any]], required_capability: str = "python") -> Optional[str]:
        best_node = None
        highest_score = -1.0

        for hb in nodes_heartbeats:
            node_id = hb.get("node_id")
            status = hb.get("status", "offline")
            capabilities = hb.get("capabilities", [])
            capacity = hb.get("capacity", {})
            health = hb.get("health", {})

            # Filtri di esclusione tassativi
            if status in ("degraded", "suspect", "unavailable", "draining", "offline"):
                continue
            if required_capability not in capabilities:
                continue
            if not all(health.values()):
                continue

            cb = self.get_or_create_cb(node_id)
            if cb.check_state() in ("open", "half_open"):
                continue

            active_goals = capacity.get("active_goals", 0)
            max_goals = capacity.get("max_goals", 10)
            if active_goals >= max_goals:
                continue

            # Calcolo punteggio basato su capacità residua
            available_slots = max_goals - active_goals
            score = float(available_slots) / float(max_goals)

            if score > highest_score:
                highest_score = score
                best_node = node_id

        return best_node