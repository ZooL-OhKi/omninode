import pytest
from datetime import datetime, timezone, timedelta
from fleet_heartbeat import EnrichedHeartbeat, GoalLease

def test_enriched_heartbeat_valid():
    hb = EnrichedHeartbeat(node_id="worker-node-1")
    assert hb.schema_version == 1
    assert hb.status == "online"
    assert hb.capacity.max_goals == 10
    assert "python" in hb.capabilities

def test_goal_lease_expiration():
    future = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    lease = GoalLease(goal_id="g-1", node_id="worker-node-1", lease_expires_at=future)
    assert lease.is_expired() is False

    past = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    expired_lease = GoalLease(goal_id="g-2", node_id="worker-node-1", lease_expires_at=past)
    assert expired_lease.is_expired() is True