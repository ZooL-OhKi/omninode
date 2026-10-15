import pytest
from self_healing import calculate_node_health, RemediationWorkflow, evaluate_remediation_safety

def test_health_score_calculation():
    hs = calculate_node_health(heartbeat_age=5.0, success_rate=0.95, p95_latency=10.0, rollback_rate=0.0)
    assert hs.score > 80.0
    assert hs.status == "healthy"

    hs_crit = calculate_node_health(heartbeat_age=45.0, success_rate=0.40, p95_latency=70.0, rollback_rate=0.5)
    assert hs_crit.score < 50.0
    assert hs_crit.status == "critical"

def test_remediation_safety_evaluation():
    # Azione sicura consentita
    res_safe = evaluate_remediation_safety("purge_cache", "low")
    assert res_safe["allowed"] is True
    assert res_safe["requires_human"] is False

    # Azione vietata bloccata
    res_bad = evaluate_remediation_safety("modify_acl", "high")
    assert res_bad["allowed"] is False
    assert res_bad["requires_human"] is True