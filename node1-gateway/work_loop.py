import time
from workspace_manager import WorkspaceManager
from test_executor import CommandExecutor

class AutonomousWorkLoop:
    def __init__(self, workspace_manager: WorkspaceManager, test_executor: CommandExecutor):
        self.wm = workspace_manager
        self.executor = test_executor
        self.audit_ids = []

    def execute_goal(self, goal_data: dict) -> dict:
        commands = goal_data.get("commands", [["python", "-m", "pytest", "-q"]])
        max_iterations = goal_data.get("max_iterations", 3)
        max_duration = goal_data.get("max_duration_seconds", 900)

        start_time = time.time()
        goal_id = self.wm.goal_id

        test_results = []
        status = "failed"
        iteration = 0

        while iteration < max_iterations:
            if (time.time() - start_time) > max_duration:
                status = "failed"
                break

            iteration += 1
            all_passed = True

            for cmd in commands:
                res = self.executor.run(cmd)
                test_results.append(res)
                if res.get("status") == "blocked":
                    return {
                        "goal_id": goal_id,
                        "status": "blocked",
                        "changed_files": [],
                        "tests": test_results,
                        "artifacts": [],
                        "audit_ids": [res.get("audit_id")],
                        "next_action": "needs_capability_grant"
                    }
                if res.get("exit_code", 1) != 0:
                    all_passed = False

            if all_passed:
                status = "completed"
                break

        changed_files = [p.relative_to(self.wm.base_dir).as_posix() for p in self.wm.base_dir.rglob("*") if p.is_file()]

        return {
            "goal_id": goal_id,
            "status": status,
            "changed_files": changed_files,
            "tests": test_results,
            "artifacts": [],
            "audit_ids": self.audit_ids,
            "next_action": None if status == "completed" else "review_errors"
        }

import os

# ---------------------------------------------------------------------------
# Phase 2.5 - Self-Hosting Autonomy Bootstrap
# ---------------------------------------------------------------------------
import json
import re as _re
import urllib.request
from typing import Any, Callable, Optional

from autonomy_core import RepoWorkspace, VerificationExecutor

STATES = ("READ_CONTEXT", "GENERATE_OR_REFINE_PATCH", "WORKSPACE_WRITE", "VERIFY_SUITE", "SELF_HEAL", "COMMIT_OR_ROLLBACK")
_THINK = _re.compile(r"<think>.*?</think>", _re.S)
_FENCE = _re.compile(r"^```[A-Za-z0-9_+-]*\n(.*?)\n```\s*$", _re.S)


class PerplexityHelper:
    """Autonomous API mode. Standard library only (urllib)."""

    ENDPOINT = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 timeout: int = 120, opener: Optional[Callable[..., Any]] = None):
        self.api_key = api_key if api_key is not None else os.getenv("PERPLEXITY_API_KEY", "")
        self.model = model or os.getenv("PERPLEXITY_MODEL", "sonar-reasoning-pro")
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def generate(self, prompt: str, target_file: str, context: dict[str, str],
                 failure: Optional[dict[str, Any]] = None) -> str:
        if not self.api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not configured")
        ctx = "\n\n".join(f"### {p}\n{c}" for p, c in context.items())
        user = f"Target file: {target_file}\n\nTask:\n{prompt}\n\nContext files:\n{ctx}"
        if failure:
            steps = failure.get("steps") or []
            bad = steps[-1] if steps else failure
            user += ("\n\nThe previous attempt FAILED verification. Fix it.\n"
                     f"preset={bad.get('preset')} exit_code={bad.get('exit_code')}\n"
                     f"stdout:\n{bad.get('stdout', '')}\nstderr:\n{bad.get('stderr', '')}")
        body = json.dumps({"model": self.model, "messages": [
            {"role": "system", "content": "Return ONLY the complete new content of the target file, no explanations."},
            {"role": "user", "content": user}]}).encode("utf-8")
        req = urllib.request.Request(self.ENDPOINT, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with self._open(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        text = _THINK.sub("", text).strip()
        m = _FENCE.match(text)
        return (m.group(1) if m else text) + "\n"


class SelfHostingWorkLoop:
    """READ_CONTEXT -> GENERATE_OR_REFINE_PATCH -> WORKSPACE_WRITE -> VERIFY_SUITE
    -> SELF_HEAL (max attempts) -> COMMIT_OR_ROLLBACK.

    External driver mode: pass `content`; one attempt, auto-rollback on failure.
    API mode: pass `prompt` and a helper; failures are fed back for up to max_attempts.
    """

    def __init__(self, workspace: RepoWorkspace, verifier: VerificationExecutor, audit: Any = None,
                 helper: Optional[PerplexityHelper] = None, max_attempts: int = 3,
                 recorder: Optional[Callable[[str, str, dict], None]] = None,
                 agent_id: str = "autonomy-agent"):
        self.ws = workspace
        self.verifier = verifier
        self.audit = audit
        self.helper = helper
        self.max_attempts = max(1, min(int(max_attempts), 3))
        self.recorder = recorder
        self.agent_id = agent_id

    def _audit(self, goal_id: str, decision: str, reason: str, resource: str) -> None:
        if self.audit is not None:
            self.audit.log_decision(decision, reason, self.agent_id, goal_id, resource, "autonomy.step")

    def _finish(self, goal_id: str, report: dict) -> dict:
        if self.recorder is not None:
            try:
                self.recorder(goal_id, report["status"], report)
            except Exception as exc:  # persistence must not mask the result
                report["recorder_error"] = str(exc)
        return report

    def run_step(self, goal_id: str, target_file: str, content: Optional[str] = None,
                 prompt: Optional[str] = None, context_files: Optional[list[str]] = None) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        report: dict[str, Any] = {"goal_id": goal_id, "target_file": target_file, "attempts": 0,
                                  "trace": trace, "verification": None, "rolled_back": False, "changed_files": []}

        context: dict[str, str] = {}
        for path in context_files or []:
            try:
                context[path] = self.ws.read(path)["content"]
                trace.append({"state": "READ_CONTEXT", "path": path, "ok": True})
            except Exception as exc:
                trace.append({"state": "READ_CONTEXT", "path": path, "ok": False, "error": str(exc)})

        if content is None and not (prompt and self.helper):
            report.update(status="rejected", error="content or (prompt + helper) required")
            return self._finish(goal_id, report)

        failure: Optional[dict[str, Any]] = None
        attempts_allowed = self.max_attempts if content is None else 1
        for attempt in range(1, attempts_allowed + 1):
            report["attempts"] = attempt
            try:
                if content is not None:
                    candidate = content
                else:
                    state = "GENERATE_OR_REFINE_PATCH" if failure is None else "SELF_HEAL"
                    candidate = self.helper.generate(prompt, target_file, context, failure)
                    trace.append({"state": state, "attempt": attempt})
                written = self.ws.write(target_file, candidate)
                trace.append({"state": "WORKSPACE_WRITE", "attempt": attempt, "sha256": written["sha256"]})
            except PermissionError as exc:
                self._audit(goal_id, "deny", "write_denied", target_file)
                self.ws.rollback_all()
                report.update(status="rejected", error=str(exc), rolled_back=True)
                return self._finish(goal_id, report)
            except Exception as exc:
                self.ws.rollback_all()
                report.update(status="error", error=str(exc), rolled_back=True)
                return self._finish(goal_id, report)

            verification = self.verifier.verify_all()
            report["verification"] = verification
            trace.append({"state": "VERIFY_SUITE", "attempt": attempt, "all_passed": verification["all_passed"]})
            if verification["all_passed"]:
                report["changed_files"] = self.ws.commit()
                trace.append({"state": "COMMIT_OR_ROLLBACK", "result": "commit"})
                self._audit(goal_id, "allow", "verified_commit", target_file)
                report["status"] = "committed"
                return self._finish(goal_id, report)
            failure = verification

        self.ws.rollback_all()
        report["rolled_back"] = True
        trace.append({"state": "COMMIT_OR_ROLLBACK", "result": "rollback"})
        self._audit(goal_id, "deny", "verification_failed_rollback", target_file)
        report["status"] = "rolled_back"
        return self._finish(goal_id, report)
