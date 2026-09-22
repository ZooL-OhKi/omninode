import os
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
        if ".." in relative_path or relative_path.startswith("/") or relative_path.startswith("\\"):
            raise ValueError("Path Traversal bloccato.")

        full_path = (self.base_dir / relative_path).resolve()

        if full_path.is_symlink():
            raise ValueError("Symlink non consentiti nel workspace.")

        for pattern in self.sensitive_patterns:
            if pattern in str(full_path).lower():
                raise ValueError(f"Accesso a risorsa sensibile bloccato: {pattern}")

        try:
            if not full_path.is_relative_to(self.base_dir):
                raise ValueError("Tentativo di escape dal workspace bloccato.")
        except AttributeError:
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Tentativo di escape dal workspace bloccato.")

        return full_path

    def write(self, relative_path: str, content: str) -> str:
        full_path = self._secure_path(relative_path)
        allowed, audit_id = self.policy.authorize(self.agent_id, self.goal_id, "workspace.write", str(full_path), "write")

        if not allowed:
            raise PermissionError(f"Accesso negato. Audit ID: {audit_id}")

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return audit_id

    def read(self, relative_path: str) -> str:
        full_path = self._secure_path(relative_path)
        allowed, audit_id = self.policy.authorize(self.agent_id, self.goal_id, "workspace.read", str(full_path), "read")

        if not allowed:
            raise PermissionError(f"Accesso negato. Audit ID: {audit_id}")

        return full_path.read_text(encoding="utf-8")
