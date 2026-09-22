from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_uuid(value: str, field: str) -> str:
    try:
        UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field} must be a UUID") from exc
    return value


def validate_task(task: dict[str, Any], local_node_id: str) -> None:
    if task.get("schema_version") != 1:
        raise ValueError("unsupported schema version")

    for field in ("task_id", "goal_id", "agent_id", "node_id", "task_type", "capability"):
        if not isinstance(task.get(field), str) or not task[field]:
            raise ValueError(f"missing {field}")

    require_uuid(task["task_id"], "task_id")
    require_uuid(task["goal_id"], "goal_id")

    if task["node_id"] != local_node_id:
        raise ValueError("task addressed to another node")

    if task["task_type"] != "workspace.write":
        raise ValueError("unsupported task type")

    if task["capability"] != "workspace.write":
        raise ValueError("unsupported capability")

    deadline = task.get("deadline_at")
    if not isinstance(deadline, str):
        raise ValueError("missing deadline_at")

    parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    if parsed <= utc_now():
        raise ValueError("task expired")
