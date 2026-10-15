import pytest
from autonomous_phase_driver import AutonomousPhaseDriver
from ai_worker_router import AIWorkerRouter
from browser_task_dispatcher import BrowserTaskDispatcher
from workspace_pool import WorkspacePool
from patch_evaluator import PatchEvaluator
from autonomous_certification import AutonomousCertification

def test_autonomous_phase_driver():
    driver = AutonomousPhaseDriver()
    phase = driver.execute_phase("g-12", risk_tier=1)
    assert phase.status == "waiting_approval"
    assert phase.pull_request_url is not None

def test_ai_worker_router():
    router = AIWorkerRouter()
    assert router.route_task("planner") == "Gemini"
    assert router.route_task("reviewer") == "Perplexity"

def test_browser_task_dispatcher():
    dispatcher = BrowserTaskDispatcher()
    res = dispatcher.dispatch("Gemini", "Analyze code. Secret: token_abc_xyz")
    assert "[REDACTED]" in res.redacted_response
    assert res.response_hash != ""

def test_workspace_pool(tmp_path):
    pool = WorkspacePool(base_dir=str(tmp_path / "workspaces"))
    ws = pool.allocate_workspace("g-1", "t-1", "Gemini")
    assert ws is not None

def test_patch_evaluator():
    evaluator = PatchEvaluator()
    res_ok = evaluator.evaluate_patch(["node1-gateway/main.py"], tests_passed=True, risk_tier=1)
    assert res_ok["accepted"] is True

    res_bad = evaluator.evaluate_patch(["config/acl.conf"], tests_passed=True, risk_tier=1)
    assert res_bad["accepted"] is False

def test_autonomous_certification():
    cert = AutonomousCertification()
    assert cert.run_certification("g-cert-1") is True