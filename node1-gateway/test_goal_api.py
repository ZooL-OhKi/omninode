import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from goal_manager import GoalManager, GoalCheckpoint
from goal_api import build_goal_router

@pytest.fixture
def test_client(tmp_path):
    db = str(tmp_path / "api_goals.db")
    mgr = GoalManager(db_path=db)
    # Pre-popoliamo un goal di test
    cp = GoalCheckpoint(goal_id="test-goal-1", status="running", target_file="foo.py")
    mgr.save_checkpoint(cp)

    app = FastAPI()
    def mock_auth(token: str) -> bool:
        return token == "secret-token"

    app.include_router(build_goal_router(mock_auth, goal_mgr=mgr))
    return TestClient(app)

def test_goal_status_endpoint(test_client):
    headers = {"Authorization": "Bearer secret-token"}
    resp = test_client.get("/api/v1/autonomy/goals/test-goal-1/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"

def test_goal_pause_and_resume(test_client):
    headers = {"Authorization": "Bearer secret-token"}
    
    # Pausa
    resp_p = test_client.post("/api/v1/autonomy/goals/test-goal-1/pause", headers=headers)
    assert resp_p.status_code == 200
    assert resp_p.json()["status"] == "paused"

    # Ripresa
    resp_r = test_client.post("/api/v1/autonomy/goals/test-goal-1/resume", headers=headers)
    assert resp_r.status_code == 200
    assert resp_r.json()["status"] == "running"