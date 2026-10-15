import os
import sys
from pathlib import Path

import pytest

from audit import AuditEventEngine
from autonomy_core import (PROTECTED_PATHS, RepoWorkspace, VERIFICATION_PRESETS,
                           VerificationExecutor, redact)
from work_loop import PerplexityHelper, SelfHostingWorkLoop
from workspace_manager import WorkspaceManager


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "node1-gateway").mkdir()
    (tmp_path / "node1-gateway" / "policy_engine.py").write_text("x = 1\n")
    (tmp_path / "node1-gateway" / "workspace_manager.py").write_text("y = 1\n")
    (tmp_path / "node1-gateway" / "ok.py").write_text("VALUE = 1\n")
    (tmp_path / "SECURITY.md").write_text("# sec\n")
    (tmp_path / ".env").write_text("OMNINODE_API_KEY=supersecretvalue\n")
    (tmp_path / "tasks.db").write_bytes(b"\x00\x01")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n")
    (tmp_path / "keys").mkdir()
    (tmp_path / "keys" / "a.pem").write_text("pem")
    return tmp_path


def test_list_ignores_secrets_and_flags_protected(repo):
    files = {f["path"]: f for f in RepoWorkspace(repo).list()["files"]}
    assert "node1-gateway/ok.py" in files
    assert files["SECURITY.md"]["protected"] is True
    assert files["node1-gateway/ok.py"]["protected"] is False
    for hidden in (".env", "tasks.db", ".git/config", "keys/a.pem"):
        assert hidden not in files


def test_list_subpath(repo):
    paths = [f["path"] for f in RepoWorkspace(repo).list("node1-gateway")["files"]]
    assert paths and all(p.startswith("node1-gateway/") for p in paths)


def test_read_returns_sha_and_redacts(repo):
    ws = RepoWorkspace(repo)
    (repo / "notes.txt").write_text("api_key = abcdef123456\nghp_" + "a" * 30 + "\n")
    res = ws.read("notes.txt")
    assert len(res["sha256"]) == 64 and res["size_bytes"] > 0
    assert "abcdef123456" not in res["content"] and "ghp_" not in res["content"]


@pytest.mark.parametrize("bad", ["../x", "a/../../x", "/etc/passwd", "\\windows", "C:\\x", ".env", ".git/config", "tasks.db", "keys/a.pem", ""])
def test_confinement_rejects(repo, bad):
    ws = RepoWorkspace(repo)
    with pytest.raises((PermissionError, ValueError)):
        ws.read(bad)
    with pytest.raises((PermissionError, ValueError)):
        ws.write(bad, "x")


def test_symlink_escape_denied(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    (outside / "f.txt").write_text("secret")
    try:
        os.symlink(outside, repo / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(PermissionError):
        RepoWorkspace(repo).read("link/f.txt")


def test_read_size_limit(repo):
    (repo / "big.txt").write_text("a" * (256 * 1024 + 1))
    with pytest.raises(ValueError):
        RepoWorkspace(repo).read("big.txt")


@pytest.mark.parametrize("protected", sorted(PROTECTED_PATHS))
def test_write_protected_denied(repo, protected):
    before = (repo / protected).read_text()
    with pytest.raises(PermissionError):
        RepoWorkspace(repo).write(protected, "pwned")
    assert (repo / protected).read_text() == before


def test_write_protected_case_variants_denied(repo):
    with pytest.raises(PermissionError):
        RepoWorkspace(repo).write("security.md", "pwned")


def test_write_and_rollback_existing_and_new(repo):
    ws = RepoWorkspace(repo)
    ws.write("node1-gateway/ok.py", "VALUE = 2\n")
    ws.write("node1-gateway/new.py", "A = 1\n")
    ws.write("node1-gateway/ok.py", "VALUE = 3\n")
    assert ws.pending_changes() == ["node1-gateway/new.py", "node1-gateway/ok.py"]
    ws.rollback_all()
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 1\n"
    assert not (repo / "node1-gateway" / "new.py").exists()
    assert not list((repo / "node1-gateway").glob(".omninode-*"))


def test_rollback_without_snapshot(repo):
    with pytest.raises(KeyError):
        RepoWorkspace(repo).rollback("node1-gateway/ok.py")


def test_guard_denies(repo):
    def guard(cap, res, act):
        raise PermissionError("denied")
    ws = RepoWorkspace(repo, guard=guard)
    with pytest.raises(PermissionError):
        ws.write("node1-gateway/ok.py", "x")
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 1\n"


def test_redact_private_key():
    pem = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"
    assert "abc" not in redact(pem)


def test_non_allowlisted_preset_rejected_and_audited(repo):
    audit = AuditEventEngine()
    ex = VerificationExecutor(repo, audit=audit)
    for bad in ("rm -rf /", "pytest -q; ls", "python -c 'print(1)'", "", None):
        with pytest.raises(ValueError):
            ex.run(bad)
    assert [e["reason"] for e in audit.logs].count("preset_not_allowlisted") == 5


def test_presets_are_static_and_match_spec():
    assert set(VERIFICATION_PRESETS) == {"python_compile", "python_tests", "go_vet", "go_tests", "git_diff_check"}
    assert VERIFICATION_PRESETS["go_tests"] == ("omniclient", ("go", "test", "./..."))


def _fake_presets(codes):
    return {name: ("node1-gateway", ("{python}", "-c", f"import sys; print('{name}'); sys.exit({codes.get(name, 0)})"))
            for name in VERIFICATION_PRESETS}


def test_verify_all_runs_in_order_and_passes(repo):
    ex = VerificationExecutor(repo, presets=_fake_presets({}))
    res = ex.verify_all()
    assert res["all_passed"] is True and res["exit_code"] == 0
    assert [s["preset"] for s in res["steps"]] == ["python_compile", "python_tests", "go_vet", "go_tests", "git_diff_check"]


def test_verify_all_fail_fast(repo):
    ex = VerificationExecutor(repo, presets=_fake_presets({"python_tests": 3}))
    res = ex.verify_all()
    assert res["all_passed"] is False and res["exit_code"] == 3
    assert [s["preset"] for s in res["steps"]] == ["python_compile", "python_tests"]


def test_output_truncated(repo):
    presets = {"python_compile": ("node1-gateway", ("{python}", "-c", "print('x'*50000)"))}
    res = VerificationExecutor(repo, presets=presets).run("python_compile")
    assert len(res["stdout"]) == 16000


def test_timeout(repo):
    presets = {"python_compile": ("node1-gateway", ("{python}", "-c", "import time; time.sleep(5)"))}
    res = VerificationExecutor(repo, presets=presets, timeout_seconds=1).run("python_compile")
    assert res["status"] == "timeout" and not res["passed"]


def _loop(repo, **kw):
    presets = {"python_compile": ("node1-gateway", ("{python}", "-m", "compileall", "-q", "."))}
    ws = RepoWorkspace(repo)
    ex = VerificationExecutor(repo, presets=presets)
    return SelfHostingWorkLoop(ws, ex, audit=AuditEventEngine(), **kw), ws


def test_loop_valid_patch_is_kept(repo):
    loop, ws = _loop(repo)
    res = loop.run_step("g1", "node1-gateway/ok.py", content="VALUE = 42\n", context_files=["SECURITY.md"])
    assert res["status"] == "committed" and res["changed_files"] == ["node1-gateway/ok.py"]
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 42\n"
    assert ws.pending_changes() == []
    assert [t["state"] for t in res["trace"]][:1] == ["READ_CONTEXT"]


def test_loop_syntax_error_rolls_back(repo):
    loop, ws = _loop(repo)
    res = loop.run_step("g2", "node1-gateway/ok.py", content="def broken(:\n")
    assert res["status"] == "rolled_back" and res["rolled_back"] is True
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 1\n"
    assert res["verification"]["all_passed"] is False


def test_loop_new_file_with_error_is_removed(repo):
    loop, _ = _loop(repo)
    res = loop.run_step("g3", "node1-gateway/new_mod.py", content="def (:\n")
    assert res["status"] == "rolled_back"
    assert not (repo / "node1-gateway" / "new_mod.py").exists()


def test_loop_protected_target_rejected(repo):
    loop, _ = _loop(repo)
    res = loop.run_step("g4", "SECURITY.md", content="x\n")
    assert res["status"] == "rejected"
    assert (repo / "SECURITY.md").read_text() == "# sec\n"


def test_loop_requires_content_or_prompt(repo):
    loop, _ = _loop(repo)
    assert loop.run_step("g5", "node1-gateway/ok.py")["status"] == "rejected"


class FakeHelper:
    def __init__(self, outputs):
        self.outputs, self.failures = list(outputs), []

    def generate(self, prompt, target_file, context, failure=None):
        self.failures.append(failure)
        return self.outputs.pop(0)


def test_loop_self_heals_with_feedback(repo):
    helper = FakeHelper(["def broken(:\n", "VALUE = 7\n"])
    loop, _ = _loop(repo, helper=helper)
    res = loop.run_step("g6", "node1-gateway/ok.py", prompt="fix")
    assert res["status"] == "committed" and res["attempts"] == 2
    assert helper.failures[0] is None and helper.failures[1]["all_passed"] is False
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 7\n"


def test_loop_gives_up_after_three_and_restores(repo):
    helper = FakeHelper(["def a(:\n"] * 3)
    loop, _ = _loop(repo, helper=helper, max_attempts=5)
    res = loop.run_step("g7", "node1-gateway/ok.py", prompt="fix")
    assert res["status"] == "rolled_back" and res["attempts"] == 3
    assert (repo / "node1-gateway" / "ok.py").read_text() == "VALUE = 1\n"


def test_loop_recorder_called(repo):
    seen = []
    loop, _ = _loop(repo, recorder=lambda g, s, r: seen.append((g, s)))
    loop.run_step("g8", "node1-gateway/ok.py", content="VALUE = 5\n")
    assert seen == [("g8", "committed")]


class _AllowPolicy:
    def authorize(self, *args, **kwargs):
        return True, "audit-test"


def test_workspace_manager_atomic_write(tmp_path):
    manager = WorkspaceManager(str(tmp_path), _AllowPolicy(), "agent-test", "goal-test")
    manager.write("nested/report.txt", "atomic content")

    assert (tmp_path / "nested" / "report.txt").read_text() == "atomic content"
    assert not list((tmp_path / "nested").glob(".omninode-wm-*"))


def test_workspace_manager_blocks_symlink_before_resolve(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")

    link = tmp_path / "link"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    manager = WorkspaceManager(str(tmp_path), _AllowPolicy(), "agent-test", "goal-test")
    with pytest.raises(ValueError, match="Symlink"):
        manager.write("link/file.txt", "blocked")


def test_perplexity_helper_parses_response():
    import io, json

    captured = {}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def opener(req, timeout=0):
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = json.loads(req.data)
        payload = {"choices": [{"message": {"content": "```python\nX = 1\n```"}}]}
        return Resp(json.dumps(payload).encode())

    h = PerplexityHelper(api_key="k-test", opener=opener)
    out = h.generate("do it", "a.py", {"b.py": "B"}, failure={"steps": [{"preset": "python_tests", "exit_code": 1, "stdout": "o", "stderr": "e"}]})
    assert out == "X = 1\n"
    assert captured["auth"] == "Bearer k-test"
    assert captured["body"]["model"] == "sonar-reasoning-pro"
    assert "FAILED" in captured["body"]["messages"][1]["content"]


def test_perplexity_helper_requires_key(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        PerplexityHelper(api_key="").generate("p", "a.py", {})
