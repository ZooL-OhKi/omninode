"""
Omninode Diagnostics & Anomaly Detection (Fase 8)
- Modello comune di telemetria strutturata e immutabile
- Rilevamento deterministico di anomalie (latenza, fallimenti, heartbeat, rollback)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field

TelemetryStatus = Literal["ok", "warning", "critical"]
AnomalySeverity = Literal["warning", "critical"]
AnomalyScope = Literal["node", "capability", "goal", "fleet"]
RecommendedAction = Literal["none", "degrade", "quarantine", "restart_worker", "purge_cache", "reassign_task", "human_approval"]

class TelemetryEvent(BaseModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    node_id: str
    goal_id: Optional[str] = None
    execution_id: Optional[str] = None
    metric: str
    value: float
    status: TelemetryStatus = "ok"
    labels: Dict[str, Any] = Field(default_factory=dict)

class AnomalyReport(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: AnomalySeverity
    scope: AnomalyScope
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_action: RecommendedAction = "none"
    auto_remediation_allowed: bool = False

class AnomalyDetector:
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or {
            "max_task_latency_seconds": 60.0,
            "max_consecutive_failures": 3,
            "max_heartbeat_age_seconds": 30.0,
            "max_rollback_rate": 0.2
        }

    def evaluate_telemetry(self, event: TelemetryEvent) -> Optional[AnomalyReport]:
        metric = event.metric
        val = event.value

        if metric == "task_latency_seconds" and val > self.thresholds["max_task_latency_seconds"]:
            return AnomalyReport(
                severity="critical" if val > self.thresholds["max_task_latency_seconds"] * 2 else "warning",
                scope="goal" if event.goal_id else "node",
                signals=[event.model_dump()],
                recommended_action="degrade" if val < self.thresholds["max_task_latency_seconds"] * 2 else "reassign_task",
                auto_remediation_allowed=True
            )

        if metric == "consecutive_failures" and val >= self.thresholds["max_consecutive_failures"]:
            return AnomalyReport(
                severity="critical",
                scope="node",
                signals=[event.model_dump()],
                recommended_action="quarantine",
                auto_remediation_allowed=True
            )

        if metric == "heartbeat_age_seconds" and val > self.thresholds["max_heartbeat_age_seconds"]:
            return AnomalyReport(
                severity="critical",
                scope="node",
                signals=[event.model_dump()],
                recommended_action="restart_worker",
                auto_remediation_allowed=True
            )

        return None