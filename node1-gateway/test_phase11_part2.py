import pytest
from multi_ai_coordinator import MultiAICoordinator

def test_multi_ai_coordination_and_conflict_prevention():
    coord = MultiAICoordinator()

    # IA Coder propone una modifica a un file
    res1 = coord.submit_proposal(
        goal_id="g-ai-1",
        role="coder",
        assigned_files=["node1-gateway/utils.py"],
        diff_hash="abc123hash",
        risk_tier=1
    )
    assert res1["success"] is True
    prop_id = res1["proposal_id"]

    # Seconda IA tenta di modificare lo stesso file (conflitto)
    res_conflict = coord.submit_proposal(
        goal_id="g-ai-1",
        role="reviewer",
        assigned_files=["node1-gateway/utils.py"],
        diff_hash="xyz789hash",
        risk_tier=1
    )
    assert res_conflict["success"] is False

    # Verifica e test superati
    verify_res = coord.verify_proposal(prop_id, tests_passed=True)
    assert verify_res["success"] is True
    assert verify_res["status"] == "verified"