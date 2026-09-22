from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any


class LocalWorkspaceExecutor:
    def __init__(
        self,
        roots: dict[str, str],
        max_bytes: int = 1_048_576,
    ) -> None:
        self.roots = {
            workspace_id: Path(root).resolve()
            for workspace_id, root in roots.items()
        }
        self.max_bytes = max_bytes

    def _target(self, workspace_id: str, relative_path: str) -> tuple[Path, Path]:
        if workspace_id not in self.roots:
            raise PermissionError("workspace not allowed")

        if not relative_path:
            raise ValueError("path is required")

        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise PermissionError("invalid relative path")

        root = self.roots[workspace_id]
        target = (root / candidate).resolve()

        if not target.is_relative_to(root):
            raise PermissionError("workspace escape denied")

        if any(part in {".ssh", ".env", "secrets"} for part in target.parts):
            raise PermissionError("sensitive path denied")

        return root, target

    def write(
        self,
        workspace_id: str,
        relative_path: str,
        content: str,
    ) -> dict[str, Any]:
        if len(content.encode("utf-8")) > self.max_bytes:
            raise ValueError("content exceeds limit")

        root, target = self._target(workspace_id, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            prefix=".omninode-write-",
            dir=str(target.parent),
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_name, target)

        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

        return {
            "workspace_id": workspace_id,
            "path": target.relative_to(root).as_posix(),
            "bytes_written": len(content.encode("utf-8")),
        }
