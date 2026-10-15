import pytest
from always_on_operator import AlwaysOnOperator

def test_always_on_operator_execution():
    operator = AlwaysOnOperator()
    res = operator.poll_and_execute_once("g-oracle-1", risk_tier=1)
    assert res["success"] is True
    assert res["status"] == "pull_request_opened"
    assert "g-oracle-1" in operator.processed_goals

def test_always_on_operator_tier4_block():
    operator = AlwaysOnOperator()
    res = operator.poll_and_execute_once("g-oracle-forbidden", risk_tier=4)
    assert res["success"] is False
    assert "Tier 4" in res["reason"]