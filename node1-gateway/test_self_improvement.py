import pytest
from self_improvement import evaluate_trust_tier, validate_proposal

def test_trust_tier_assignment():
    assert evaluate_trust_tier("README.md", "docs") == 0
    assert evaluate_trust_tier("node1-gateway/test_foo.py", "bugfix") == 0
    assert evaluate_trust_tier("node1-gateway/service.py", "refactor") == 1
    assert evaluate_trust_tier("requirements.txt", "deps") == 3
    assert evaluate_trust_tier("config/acl_rules.txt", "policy") == 4

def test_proposal_validation_rules():
    # Tier 0 approvato automaticamente
    res_t0 = validate_proposal("README.md", "docs")
    assert res_t0["approved"] is True
    assert res_t0["requires_human"] is False

    # Tier 4 rifiutato tassativamente
    res_t4 = validate_proposal("config/acl_rules.txt", "policy")
    assert res_t4["approved"] is False
    assert res_t4["trust_tier"] == 4

    # Tier 3 richiede intervento umano
    res_t3 = validate_proposal("requirements.txt", "deps")
    assert res_t3["approved"] is False
    assert res_t3["requires_human"] is True