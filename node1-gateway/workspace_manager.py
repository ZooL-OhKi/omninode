import os
import re
import tempfile
from pathlib import Path
from policy_engine import PolicyEngine


class WorkspaceManager:
    def __init__(self, base_dir: str, policy: PolicyEngine, agent_id: str, goal_id: str):
        self.base_dir = Path(base_dir).resolve()
        self.policy = policy
        self.agent_id = agent_id
        self.goal_id = goal_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sensitive_patterns = [".env", ".ssh", "id_rsa", "id_ed25519", "credentials"]

    def _secure_path(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("Percorso non valido.")
        if "\x00" in relative_path:
            raise ValueError("Percorso non valido.")
        if relative_path.startswith("/") or relative_path.startswith("\\"):
            raise ValueError("Path Traversal bloccato.")

        parts = [part for part in re.split(r"[\\/]+", relative_path) if part not in ("", ".")]
        if not parts or ".." in parts:
            raise ValueError("Path Traversal bloccato.")

        # Check symlink before resolve(): after Path.resolve(), is_symlink() is always False.
        candidate = self.base_dir
        for part in parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise ValueError("Symlink non consentiti nel workspace.")

        full_path = candidate.resolve()
        try:
            if not full_path.is_relative_to(self.base_dir):
                raise ValueError("Tentativo di escape dal workspace bloccato.")
        except AttributeError:
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Tentativo di escape dal workspace bloccato.")

        relative_lower = "/".join(parts).lower()
        for pattern in self.sensitive_patterns:
            if pattern in relative_lower:
                raise ValueError(f"Accesso a risorsa sensibile bloccato: {pattern}")

        return full_path

    def write(self, relative_path: str, content: str) -> str:
        full_path = self._secure_path(relative_path)
        allowed, audit_id = self.policy.authorize(
            self.agent_id, self.goal_id, "workspace.write", str(full_path), "write"
        )

        if not allowed:
            raise PermissionError(f"Accesso negato. Audit ID: {audit_id}")

        full_path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")

        fd, temp_name = tempfile.mkstemp(prefix=".omninode-wm-", dir=str(full_path.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, full_path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

        return audit_id

    def read(self, relative_path: str) -> str:
        full_path = self._secure_path(relative_path)
        allowed, audit_id = self.policy.authorize(
            self.agent_id, self.goal_id, "workspace.read", str(full_path), "read"
        )

        if not allowed:
            raise PermissionError(f"Accesso negato. Audit ID: {audit_id}")

        return full_path.read_text(encoding="utf-8")
