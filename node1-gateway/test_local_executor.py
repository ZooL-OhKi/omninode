from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from local_executor import LocalWorkspaceExecutor
from mqtt_task_protocol import validate_task


def valid_task(node_id="node-local"):
    now = datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "task_id": str(uuid4()),
        "goal_id": str(uuid4()),
        "agent_id": "agent-test",
        "node_id": node_id,
        "task_type": "workspace.write",
        "capability": "workspace.write",
        "deadline_at": (now + timedelta(seconds=30)).isoformat(),
    }


def test_valid_task():
    validate_task(valid_task(), "node-local")


def test_wrong_node_is_rejected():
    with pytest.raises(ValueError, match="another node"):
        validate_task(valid_task("other-node"), "node-local")


def test_expired_task_is_rejected():
    task = valid_task()
    task["deadline_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    with pytest.raises(ValueError, match="expired"):
        validate_task(task, "node-local")


def test_workspace_write_is_confined(tmp_path: Path):
    executor = LocalWorkspaceExecutor({"workspace": str(tmp_path)})

    result = executor.write("workspace", "Desktop/report.txt", "ok")

    assert result["path"] == "Desktop/report.txt"
    assert (tmp_path / "Desktop/report.txt").read_text() == "ok"


def test_absolute_path_is_rejected(tmp_path: Path):
    executor = LocalWorkspaceExecutor({"workspace": str(tmp_path)})

    with pytest.raises(PermissionError):
        executor.write("workspace", str(tmp_path / "outside.txt"), "blocked")


def test_traversal_is_rejected(tmp_path: Path):
    executor = LocalWorkspaceExecutor({"workspace": str(tmp_path)})

    with pytest.raises(PermissionError):
        executor.write("workspace", "../outside.txt", "blocked")


def test_unknown_workspace_is_rejected(tmp_path: Path):
    executor = LocalWorkspaceExecutor({"workspace": str(tmp_path)})

    with pytest.raises(PermissionError):
        executor.write("unknown", "file.txt", "blocked")


def test_sensitive_path_is_rejected(tmp_path: Path):
    executor = LocalWorkspaceExecutor({"workspace": str(tmp_path)})

    with pytest.raises(PermissionError):
        executor.write("workspace", ".env/file", "blocked")
