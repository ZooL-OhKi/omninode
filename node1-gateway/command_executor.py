import subprocess
from policy_engine import PolicyEngine

try:
    from autonomy_core import VERIFICATION_PRESETS
    _DYNAMIC_PRESETS = tuple(
        tuple(spec["cmd"]) for spec in VERIFICATION_PRESETS.values()
        if isinstance(spec, dict) and "cmd" in spec
    )
except Exception:
    VERIFICATION_PRESETS = {}
    _DYNAMIC_PRESETS = ()

ALLOWED_STATIC_ARGV: tuple[tuple[str, ...], ...] = _DYNAMIC_PRESETS + (
    ("python", "-m", "pytest", "-q"),
    ("pytest", "-q"),
    ("python", "-m", "compileall", "-q", "."),
    ("go", "test", "./..."),
    ("go", "vet", "./..."),
    ("git", "diff", "--check"),
)

MAX_OUTPUT_CHARS = 16000


class TestExecutor:
    """Executor confinato esclusivamente ai preset statici di verifica (Zero Arbitrary Code Execution)."""

    def __init__(self, policy: PolicyEngine, agent_id: str, goal_id: str, workspace_dir: str):
        self.policy = policy
        self.agent_id = agent_id
        self.goal_id = goal_id
        self.cwd = workspace_dir

    def run(self, cmd_args: list | str, timeout_seconds: int = 60) -> dict:
        if isinstance(cmd_args, str):
            if cmd_args not in VERIFICATION_PRESETS or "cmd" not in VERIFICATION_PRESETS[cmd_args]:
                raise ValueError(f"Preset '{cmd_args}' non autorizzato.")
            argv = list(VERIFICATION_PRESETS[cmd_args]["cmd"])
        elif isinstance(cmd_args, list) and cmd_args:
            if tuple(cmd_args) not in ALLOWED_STATIC_ARGV:
                raise ValueError(f"Comando non in allowlist statica: {cmd_args}")
            argv = list(cmd_args)
        else:
            raise ValueError("Comando vuoto o non valido.")

        allowed, audit_id = self.policy.authorize(
            self.agent_id, self.goal_id, "process.run", self.cwd, "execute"
        )
        if not allowed:
            return {"status": "blocked", "audit_id": audit_id}

        try:
            res = subprocess.run(
                argv,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False,
            )
            return {
                "status": "completed",
                "exit_code": res.returncode,
                "stdout": res.stdout[:MAX_OUTPUT_CHARS],
                "stderr": res.stderr[:MAX_OUTPUT_CHARS],
                "audit_id": audit_id,
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "timeout", "audit_id": audit_id}