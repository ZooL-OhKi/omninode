import pytest
from fleet_scheduler import CircuitBreaker, CapacityScheduler

def test_circuit_breaker_transitions():
    cb = CircuitBreaker(node_id="n-1", failure_threshold=2, recovery_timeout_seconds=0.1)
    assert cb.check_state() == "closed"

    cb.record_failure()
    assert cb.check_state() == "closed"

    cb.record_failure()
    assert cb.check_state() == "open"

    cb.record_success()
    assert cb.check_state() == "closed"

def test_capacity_scheduler_selection():
    scheduler = CapacityScheduler()
    nodes = [
        {
            "node_id": "worker-1",
            "status": "online",
            "capabilities": ["python"],
            "capacity": {"active_goals": 2, "max_goals": 10},
            "health": {"mqtt": True, "browser": True, "workspace": True, "executor": True}
        },
        {
            "node_id": "worker-2",
            "status": "degraded", # Scartato
            "capabilities": ["python"],
            "capacity": {"active_goals": 1, "max_goals": 10},
            "health": {"mqtt": True, "browser": True, "workspace": True, "executor": True}
        }
    ]

    selected = scheduler.select_best_node(nodes, required_capability="python")
    assert selected == "worker-1"