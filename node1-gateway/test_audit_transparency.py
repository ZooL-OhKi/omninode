import os
os.environ["MCP_SECRET"] = "test-mcp-secret"

import pytest
from fastapi.testclient import TestClient
from audit_transparency import AuditTransparencyLog
import main

@pytest.fixture
def temp_audit_log(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    return AuditTransparencyLog(db_path=db_file)

def test_audit_event_creation_and_chaining(temp_audit_log):
    r1 = temp_audit_log.append_event("agent-1", "workspace.write", "t-1", {"path": "a.txt"})
    r2 = temp_audit_log.append_event("agent-1", "command.run", "t-2", {"preset": "pytest"})

    assert r1["previous_hash"] == "0" * 64
    assert r2["previous_hash"] == r1["current_hash"]
    
    res = temp_audit_log.verify_chain()
    assert res["valid"] is True
    assert res["total_records"] == 2

def test_audit_tampering_detection(temp_audit_log):
    temp_audit_log.append_event("agent-1", "workspace.write", "t-1", {"path": "a.txt"})
    
    conn = temp_audit_log._get_conn()
    conn.execute("UPDATE audit_events SET payload_hash = 'tampered' WHERE rowid = 1")
    conn.close()

    res = temp_audit_log.verify_chain()
    assert res["valid"] is False
    assert "Tampering detected" in res["error"]

def test_audit_api_endpoints():
    client = TestClient(main.app)
    headers = {"Authorization": "Bearer test-mcp-secret"}

    resp = client.get("/api/v1/audit/events?limit=10&offset=0", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "total" in data

    resp_v = client.get("/api/v1/audit/verify", headers=headers)
    assert resp_v.status_code == 200
    assert resp_v.json()["valid"] is True