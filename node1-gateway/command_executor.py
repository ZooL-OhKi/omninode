import subprocess
from policy_engine import PolicyEngine

ALLOWED_COMMANDS = frozenset(
    {
        ("pytest", "-q"),
        ("python", "-m", "pytest", "-q"),
        ("python", "-m", "compileall", "-q", "."),
        ("go", "test", "./..."),
        ("go", "vet", "./..."),
        ("git", "diff", "--check"),
    }
)
OUTPUT_LIMIT = 16000


class TestExecutor:
    def __init__(self, policy: PolicyEngine, agent_id: str, goal_id: str, workspace_dir: str):
        self.policy = policy
        self.agent_id = agent_id
        self.goal_id = goal_id
        self.cwd = workspace_dir

    def run(self, cmd_args: list, timeout_seconds: int = 120) -> dict:
        if not isinstance(cmd_args, list) or not cmd_args:
            raise ValueError("Comando vuoto.")

        argv = tuple(str(arg) for arg in cmd_args)
        if argv not in ALLOWED_COMMANDS:
            raise ValueError("Comando non consentito: solo preset di verifica statici sono ammessi.")

        allowed, audit_id = self.policy.authorize(self.agent_id, self.goal_id, "process.run", self.cwd, "execute")
        if not allowed:
            return {"status": "blocked", "audit_id": audit_id}

        try:
            res = subprocess.run(
                list(argv), cwd=self.cwd, capture_output=True, text=True, timeout=timeout_seconds, shell=False
            )
            return {
                "status": "completed",
                "exit_code": res.returncode,
                "stdout": res.stdout[:OUTPUT_LIMIT],
                "stderr": res.stderr[:OUTPUT_LIMIT],
                "audit_id": audit_id,
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "timeout", "audit_id": audit_id}
