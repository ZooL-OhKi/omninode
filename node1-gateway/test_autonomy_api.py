import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")

import task_store
from autonomy_api import AutonomyService, GoalRequest, RunStepRequest, build_router


class _H:
    api_key = "k"

    def __init__(self, outputs):
        self.outputs = list(outputs)

    def generate(self, prompt, target_file, context, failure=None):
        return self.outputs.pop(0)


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "node1-gateway").mkdir(parents=True)
    (repo / "node1-gateway" / "ok.py").write_text("V = 1\n")
    (repo / "SECURITY.md").write_text("# s\n")
    monkeypatch.setattr(task_store, "DB_PATH", str(tmp_path / "tasks.db"))
    presets = {"python_compile": ("node1-gateway", ("{python}", "-m", "compileall", "-q", "."))}
    svc = AutonomyService(repo_root=repo, presets=presets, helper_factory=lambda: _H(["V = 9\n"]))
    return repo, svc


def test_run_step_commit_persists_status(env):
    repo, svc = env
    res = svc.run_step(RunStepRequest(target_file="node1-gateway/ok.py", content="V = 2\n", goal_id="s1"))
    assert res["status"] == "committed"
    assert (repo / "node1-gateway" / "ok.py").read_text() == "V = 2\n"
    assert task_store.get_task("s1")["status"] == "committed"


def test_run_step_failure_rolls_back(env):
    repo, svc = env
    res = svc.run_step(RunStepRequest(target_file="node1-gateway/ok.py", content="def (:\n", goal_id="s2"))
    assert res["status"] == "rolled_back"
    assert (repo / "node1-gateway" / "ok.py").read_text() == "V = 1\n"
    assert task_store.get_task("s2")["status"] == "rolled_back"


def test_run_step_protected_rejected_and_audited(env):
    repo, svc = env
    res = svc.run_step(RunStepRequest(target_file="SECURITY.md", content="x", goal_id="s3"))
    assert res["status"] == "rejected"
    assert (repo / "SECURITY.md").read_text() == "# s\n"
    assert any(e["decision"] == "deny" for e in svc.audit.logs)


def test_run_step_prompt_mode_uses_helper(env):
    repo, svc = env
    res = svc.run_step(RunStepRequest(target_file="node1-gateway/ok.py", prompt="change", goal_id="s4"))
    assert res["status"] == "committed"
    assert (repo / "node1-gateway" / "ok.py").read_text() == "V = 9\n"


def test_endpoints_require_auth_and_work(env):
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.testclient import TestClient

    repo, svc = env

    async def auth(authorization: str = Header(None)):
        if authorization != "Bearer t":
            raise HTTPException(401, "no")

    app = FastAPI()
    app.include_router(build_router(auth, svc))
    client = TestClient(app)
    body = {"target_file": "node1-gateway/ok.py", "content": "V = 3\n"}
    assert client.post("/api/v1/autonomy/run-step", json=body).status_code == 401
    r = client.post("/api/v1/autonomy/run-step", json=body, headers={"Authorization": "Bearer t"})
    assert r.status_code == 200 and r.json()["status"] == "committed"
    r = client.post("/api/v1/autonomy/run-step", json={"target_file": "x.py"}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 400
    assert client.get("/api/v1/autonomy/goals/missing", headers={"Authorization": "Bearer t"}).status_code == 404
