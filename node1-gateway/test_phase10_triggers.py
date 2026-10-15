import pytest
import time
import hmac
import hashlib
from risk_classifier import RiskClassifier
from goal_contract import GoalContract, GoalConstraints, validate_goal_contract
from mcp_triggers import MCPTriggerManager, GlobalFleetLimits
from secure_webhook import SecureWebhookVerifier

def test_risk_classification():
    clf = RiskClassifier()
    assert clf.classify_task("add unit test for parser", ["node1-gateway/parser.py"]) == 0
    assert clf.classify_task("refactor local module", ["node1-gateway/utils.py"]) == 1
    assert clf.classify_task("modify security ACL rules", ["config/acl.conf"]) == 4

def test_goal_contract_validation():
    contract = GoalContract(
        goal_id="g-100",
        title="Test Goal",
        risk_tier=1,
        acceptance_criteria=["tests pass"]
    )
    res = validate_goal_contract(contract)
    assert res["valid"] is True

    bad_contract = GoalContract(
        goal_id="g-101",
        title="Bad Goal",
        risk_tier=4,
        acceptance_criteria=["none"]
    )
    res_bad = validate_goal_contract(bad_contract)
    assert res_bad["valid"] is False

def test_mcp_triggers_lifecycle():
    manager = MCPTriggerManager()
    token = "omninode-secure-mcp-token-2026"
    bad_token = "invalid-token"

    contract = GoalContract(
        goal_id="g-mcp-1",
        title="MCP Goal Test",
        risk_tier=0,
        acceptance_criteria=["done"]
    )

    # Auth fallita
    res_bad = manager.create_goal(bad_token, contract)
    assert res_bad["success"] is False

    # Auth riuscita
    res_ok = manager.create_goal(token, contract)
    assert res_ok["success"] is True

    # List & Get
    goals = manager.list_goals(token)
    assert len(goals) == 1

    g_data = manager.get_goal(token, "g-mcp-1")
    assert g_data is not None

    # Stop goal
    stop_res = manager.stop_goal(token, "g-mcp-1")
    assert stop_res["success"] is True

def test_secure_webhook_verification():
    secret = "my-secret-webhook-key"
    verifier = SecureWebhookVerifier(secret_key=secret, max_age_seconds=60)

    body = b'{"event":"task_complete"}'
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode("utf-8"), body + ts.encode("utf-8"), hashlib.sha256).hexdigest()

    res = verifier.verify_request(body, sig, ts)
    assert res["valid"] is True

    # Replay attack bloccato
    res_replay = verifier.verify_request(body, sig, ts)
    assert res_replay["valid"] is False