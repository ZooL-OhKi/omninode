import pytest
from self_test_runner import SelfTestRunner
from browser_executor import SecureBrowserExecutor, BrowserSessionRequest

def test_self_test_runner_execution():
    runner = SelfTestRunner()
    report = runner.start_run()
    assert report.status == "passed"
    assert len(report.stages_passed) > 0

    fetched = runner.get_run_report(report.run_id)
    assert fetched is not None
    assert fetched.run_id == report.run_id

def test_secure_browser_redaction_and_execution():
    executor = SecureBrowserExecutor()
    req = BrowserSessionRequest(target_url="https://example.com", prompt="Test prompt")
    res = executor.execute_session(req)

    assert res.status == "success"
    assert "secret_dummy_123" not in res.redacted_content
    assert "[REDACTED]" in res.redacted_content
    assert res.raw_response_hash != ""