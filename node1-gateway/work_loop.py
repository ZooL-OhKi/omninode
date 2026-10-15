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
import json
import threading
import urllib.error
import urllib.request
import uuid

import re as _re
from typing import Any, Callable, Optional

from autonomy_core import RepoWorkspace, VerificationExecutor

STATES = ("READ_CONTEXT", "GENERATE_OR_REFINE_PATCH", "WORKSPACE_WRITE", "VERIFY_SUITE", "SELF_HEAL", "COMMIT_OR_ROLLBACK")
_THINK = _re.compile(r"</think>", _re.S)
_FENCE = _re.compile(r"^```[A-Za-z0-9_+-]*\n(.*?)\n```\s*$", _re.S)
_PRE_CODE = _re.compile(r"<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>", _re.S | _re.I)


def _decode_html(value: str) -> str:
    return (
        value.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&amp;", "&")
    )


def _extract_code(text: str) -> str:
    text = _THINK.sub("", text).strip()
    code_blocks = _PRE_CODE.findall(text)
    if code_blocks:
        text = _decode_html(code_blocks[-1]).strip()
    match = _FENCE.match(text)
    return (match.group(1) if match else text) + "\n"


class BrowserPromptBridge:
    """Inbox/Outbox bridge for a browser extension or external Web UI driver."""

    def __init__(self):
        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}
        self._responses: dict[str, str] = {}
        self._events: dict[str, threading.Event] = {}

    def create(self, goal_id: str, prompt: str) -> None:
        with self._lock:
            self._pending[goal_id] = {"goal_id": goal_id, "prompt": prompt, "created_at": time.time()}
            self._responses.pop(goal_id, None)
            self._events[goal_id] = threading.Event()

    def pending(self, goal_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        with self._lock:
            item = self._pending.get(goal_id) if goal_id else next(iter(self._pending.values()), None)
            return dict(item) if item else None

    def submit(self, goal_id: str, response: str) -> None:
        with self._lock:
            if goal_id not in self._pending:
                raise KeyError(f"no pending browser prompt for {goal_id}")
            self._responses[goal_id] = response
            self._pending.pop(goal_id, None)
            event = self._events[goal_id]
        event.set()

    def wait(self, goal_id: str, timeout: float) -> str:
        event = self._events.get(goal_id)
        if event is None:
            raise KeyError(f"no pending browser prompt for {goal_id}")
        if not event.wait(timeout):
            raise TimeoutError("browser DOM response timeout")
        with self._lock:
            response = self._responses.pop(goal_id, None)
            self._events.pop(goal_id, None)
        if response is None:
            raise RuntimeError("browser DOM response missing")
        return response


browser_bridge = BrowserPromptBridge()


class BrowserWebAIHelper:
    """Zero-API browser Web UI bridge.

    Transport priority:
    1. Browser RPC (OMNINODE_BROWSER_RPC_URL or omniclient browser endpoint).
    2. MQTT browser.chat_prompt dispatch.
    3. Inbox/Outbox BrowserPromptBridge for a browser extension / external driver.
    """

    DEFAULT_RPC_URL = "http://127.0.0.1:8080/browser/chat-prompt"
    DEFAULT_MQTT_TOPIC = "omninode/nodes/node-local/tasks"

    def __init__(self, rpc_url: Optional[str] = None, mqtt_topic: Optional[str] = None,
                 mqtt_publish: Optional[Callable[[str, str], Any]] = None,
                 bridge: Optional[BrowserPromptBridge] = None, timeout: int = 180,
                 opener: Optional[Callable[..., Any]] = None):
        self.rpc_url = rpc_url or os.getenv("OMNINODE_BROWSER_RPC_URL", self.DEFAULT_RPC_URL)
        self.mqtt_topic = mqtt_topic or self.DEFAULT_MQTT_TOPIC
        self.mqtt_publish = mqtt_publish
        self.bridge = bridge or browser_bridge
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def _build_prompt(self, prompt: str, target_file: str, context: dict[str, str],
                      failure: Optional[dict[str, Any]]) -> str:
        ctx = "\n\n".join(f"### {path}\n{content}" for path, content in context.items())
        user = f"Target file: {target_file}\n\nTask:\n{prompt}\n\nContext files:\n{ctx}"
        if failure:
            steps = failure.get("steps") or []
            bad = steps[-1] if steps else failure
            user += (
                "\n\nThe previous attempt FAILED verification. Fix it.\n"
                f"preset={bad.get('preset')} exit_code={bad.get('exit_code')}\n"
                f"stdout:\n{bad.get('stdout', '')}\nstderr:\n{bad.get('stderr', '')}"
            )
        return user

    def _rpc_generate(self, prompt: str) -> str:
        body = json.dumps({"prompt": prompt, "wait_for_dom_complete": True,
                           "dom_stable_ms": 1800}).encode("utf-8")
        request = urllib.request.Request(
            self.rpc_url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with self._open(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("response") or data.get("code") or data.get("raw") or ""
        if not raw:
            raise ValueError("browser RPC returned an empty response")
        return raw

    def generate(self, prompt: str, target_file: str, context: dict[str, str],
                 failure: Optional[dict[str, Any]] = None) -> str:
        structured_prompt = self._build_prompt(prompt, target_file, context, failure)

        try:
            return _extract_code(self._rpc_generate(structured_prompt))
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            pass

        bridge_goal_id = f"browser-{uuid.uuid4().hex[:12]}"
        self.bridge.create(bridge_goal_id, structured_prompt)

        if self.mqtt_publish is not None:
            payload = json.dumps({
                "type": "browser.chat_prompt",
                "goal_id": bridge_goal_id,
                "prompt": structured_prompt,
                "target_file": target_file,
                "wait_for_dom_complete": True,
                "dom_stable_ms": 1800,
            })
            self.mqtt_publish(self.mqtt_topic, payload)

        try:
            response = self.bridge.wait(bridge_goal_id, timeout=self.timeout)
        except TimeoutError:
            if self.mqtt_publish is None:
                raise RuntimeError("Browser Web Bridge unavailable: RPC failed and no MQTT publisher configured")
            raise
        return _extract_code(response)


# Retrocompatible alias: OmniNode no longer calls the paid Perplexity HTTP API.
PerplexityHelper = BrowserWebAIHelper


class SelfHostingWorkLoop:
    """READ_CONTEXT -> GENERATE_OR_REFINE_PATCH -> WORKSPACE_WRITE -> VERIFY_SUITE
    -> SELF_HEAL (max attempts) -> COMMIT_OR_ROLLBACK.

    External driver mode: pass `content`; one attempt, auto-rollback on failure.
    Browser bridge mode: pass `prompt` and a helper; failures are fed back for up to max_attempts.
    """

    def __init__(self, workspace: RepoWorkspace, verifier: VerificationExecutor, audit: Any = None,
                 helper: Optional[BrowserWebAIHelper] = None, max_attempts: int = 3,
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
            except Exception as exc:
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
