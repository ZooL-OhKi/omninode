import subprocess
from policy_engine import PolicyEngine

class TestExecutor:
    def __init__(self, policy: PolicyEngine, agent_id: str, goal_id: str, workspace_dir: str):
        self.policy = policy
        self.agent_id = agent_id
        self.goal_id = goal_id
        self.cwd = workspace_dir
        self.allowlist = ["pytest", "go"]

    def run(self, cmd_args: list, timeout_seconds: int = 120) -> dict:
        base_cmd = cmd_args[0]
        if base_cmd not in self.allowlist:
            raise ValueError(f"Comando '{base_cmd}' non in allowlist.")

        allowed, audit_id = self.policy.authorize(self.agent_id, self.goal_id, "process.run", self.cwd, "execute")
        if not allowed:
            return {"status": "blocked", "audit_id": audit_id}

        try:
            res = subprocess.run(
                cmd_args, cwd=self.cwd, capture_output=True, text=True, timeout=timeout_seconds, shell=False
            )
            return {
                "status": "completed",
                "exit_code": res.returncode,
                "stdout": res.stdout[:1048576],
                "stderr": res.stderr[:1048576],
                "audit_id": audit_id
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "timeout", "audit_id": audit_id}
