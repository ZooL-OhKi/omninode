"""Modulo di metriche Prometheus per il gateway OmniNode."""
from __future__ import annotations

import time
from typing import Dict, Any

class GatewayMetrics:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.counters: Dict[str, int] = {
            "omninode_gateway_requests_total": 0,
            "omninode_gateway_tasks_dispatched_total": 0,
            "omninode_gateway_tasks_completed_total": 0,
            "omninode_gateway_tasks_failed_total": 0,
        }

    def increment(self, metric_name: str, value: int = 1) -> None:
        if metric_name in self.counters:
            self.counters[metric_name] += value

    def render(self, active_nodes_count: int, mqtt_ready: bool) -> str:
        uptime = time.time() - self.start_time
        lines = [
            "# HELP omninode_gateway_uptime_seconds Uptime del gateway in secondi",
            "# TYPE omninode_gateway_uptime_seconds gauge",
            f"omninode_gateway_uptime_seconds {uptime:.2f}",
            "# HELP omninode_active_nodes_count Numero di nodi attivi nel fabric",
            "# TYPE omninode_active_nodes_count gauge",
            f"omninode_active_nodes_count {active_nodes_count}",
            "# HELP omninode_mqtt_ready Stato della connessione MQTT mTLS (1=pronto, 0=non pronto)",
            "# TYPE omninode_mqtt_ready gauge",
            f"omninode_mqtt_ready {1 if mqtt_ready else 0}",
        ]
        for name, val in self.counters.items():
            lines.extend([
                f"# TYPE {name} counter",
                f"{name} {val}",
            ])
        return "\n".join(lines) + "\n"

metrics = GatewayMetrics()
