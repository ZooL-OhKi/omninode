"""Phase 2.5 autonomy endpoints (APIRouter). Wired into main.py with include_router."""
from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import task_store
from audit import AuditEventEngine
from autonomy_core import RepoWorkspace, VerificationExecutor
from policy_engine import PolicyEngine
from work_loop import BrowserWebAIHelper, SelfHostingWorkLoop, browser_bridge

AGENT_ID = "autonomy-agent"
NODE_ID = "node-local"
CAPABILITIES = ("workspace.list", "workspace.read", "workspace.write", "workspace.rollback", "command.run")
_RUN_LOCK = threading.Lock()


def default_repo_root() -> Path:
    env = os.getenv("OMNINODE_REPO_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


class RunStepRequest(BaseModel):
    target_file: str = Field(min_length=1, max_length=512)
    content: Optional[str] = None
    prompt: Optional[str] = Field(default=None, max_length=20000)
    context_files: list[str] = Field(default_factory=list, max_length=20)
    goal_id: Optional[str] = Field(default=None, max_length=64)


class GoalRequest(BaseModel):
    target_file: str = Field(min_length=1, max_length=512)
    prompt: str = Field(min_length=1, max_length=20000)
    context_files: list[str] = Field(default_factory=list, max_length=20)
    max_attempts: int = Field(default=3, ge=1, le=3)


class DomResponseRequest(BaseModel):
    goal_id: str = Field(min_length=1, max_length=128)
    raw_dom_markdown_or_code: str = Field(min_length=1, max_length=1000000)


class RollbackRequest(BaseModel):
    path: str = Field(min_length=1, max_length=512)


class CommandVerifyRequest(BaseModel):
    preset: str = Field(min_length=1, max_length=64)


class AutonomyService:
    def __init__(self, repo_root: Optional[Path] = None, audit: Optional[AuditEventEngine] = None,
                 helper_factory: Optional[Callable[[], BrowserWebAIHelper]] = None,
                 presets: Optional[dict] = None, persist: bool = True):
        self.repo_root = Path(repo_root) if repo_root else default_repo_root()
        self.audit = audit or AuditEventEngine()
        self.policy = PolicyEngine(self.audit)
        self.helper_factory = helper_factory or BrowserWebAIHelper
        self.presets = presets
        self.persist = persist
        if persist:
            task_store.init_db()

    def _grant(self, goal_id: str) -> None:
        expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        for cap in CAPABILITIES:
            self.policy.grant({"agent_id": AGENT_ID, "goal_id": goal_id, "capability": cap,
                               "workspace": str(self.repo_root.resolve()), "expires_at": expires, "node_id": NODE_ID})

    def _guard(self, goal_id: str):
        def guard(capability: str, resource: str, action: str) -> None:
            allowed, audit_id = self.policy.authorize(AGENT_ID, goal_id, capability, resource, action)
            if not allowed:
                raise PermissionError(f"denied by policy ({capability}), audit {audit_id}")
        return guard

    def _workspace(self, goal_id: str) -> RepoWorkspace:
        self._grant(goal_id)
        return RepoWorkspace(self.repo_root, guard=self._guard(goal_id))

    def _verifier(self, goal_id: str) -> VerificationExecutor:
        self._grant(goal_id)
        return VerificationExecutor(self.repo_root, guard=self._guard(goal_id), audit=self.audit,
                                    agent_id=AGENT_ID, goal_id=goal_id, presets=self.presets)

    def _loop(self, goal_id: str, use_helper: bool, max_attempts: int) -> SelfHostingWorkLoop:
        self._grant(goal_id)

        ws = RepoWorkspace(self.repo_root, guard=self._guard(goal_id))
        ver = VerificationExecutor(self.repo_root, guard=self._guard(goal_id), audit=self.audit, agent_id=AGENT_ID,
                                   goal_id=goal_id, presets=self.presets)
        helper = self.helper_factory() if use_helper else None
        return SelfHostingWorkLoop(ws, ver, audit=self.audit, helper=helper, max_attempts=max_attempts,
                                   recorder=self._record if self.persist else None, agent_id=AGENT_ID)

    @staticmethod
    def _record(goal_id: str, status: str, report: dict[str, Any]) -> None:
        summary = {k: report.get(k) for k in ("status", "attempts", "target_file", "changed_files", "rolled_back", "error")}
        verification = report.get("verification") or {}
        summary["all_passed"] = verification.get("all_passed")
        summary["exit_code"] = verification.get("exit_code")
        task_store.update_task_status(goal_id, status, result=summary, error=report.get("error"))

    def run_step(self, req: RunStepRequest) -> dict[str, Any]:
        goal_id = req.goal_id or f"step-{uuid.uuid4().hex[:12]}"
        if self.persist:
            task_store.create_task(goal_id, "autonomy.run_step", {"target_file": req.target_file, "mode": "browser" if req.content is None else "external"})
        with _RUN_LOCK:
            loop = self._loop(goal_id, use_helper=req.content is None, max_attempts=3)
            return loop.run_step(goal_id, req.target_file, content=req.content, prompt=req.prompt,
                                 context_files=req.context_files)

    def start_goal(self, req: GoalRequest) -> str:
        goal_id = f"goal-{uuid.uuid4().hex[:12]}"
        if self.persist:
            task_store.create_task(goal_id, "autonomy.goal", {"target_file": req.target_file, "max_attempts": req.max_attempts})
        loop = self._loop(goal_id, use_helper=True, max_attempts=req.max_attempts)

        def worker() -> None:
            with _RUN_LOCK:
                try:
                    loop.run_step(goal_id, req.target_file, prompt=req.prompt, context_files=req.context_files)
                except Exception as exc:
                    if self.persist:
                        task_store.update_task_status(goal_id, "error", error=str(exc))

        if self.persist:
            task_store.update_task_status(goal_id, "running")
        threading.Thread(target=worker, name=goal_id, daemon=True).start()
        return goal_id

    def workspace_list(self, subpath: str = "") -> dict[str, Any]:
        return self._workspace(f"ws-list-{uuid.uuid4().hex[:12]}").list(subpath)

    def workspace_read(self, path: str) -> dict[str, Any]:
        return self._workspace(f"ws-read-{uuid.uuid4().hex[:12]}").read(path)

    def workspace_rollback(self, path: str) -> dict[str, Any]:
        return self._workspace(f"ws-rollback-{uuid.uuid4().hex[:12]}").rollback(path)

    def command_verify(self, preset: str) -> dict[str, Any]:
        return self._verifier(f"verify-{uuid.uuid4().hex[:12]}").run(preset)


def build_router(auth_dependency: Callable[..., Any], service: Optional[AutonomyService] = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/autonomy", tags=["autonomy"], dependencies=[Depends(auth_dependency)])
    holder: dict[str, Optional[AutonomyService]] = {"svc": service}

    def svc() -> AutonomyService:
        if holder["svc"] is None:
            holder["svc"] = AutonomyService()
        return holder["svc"]

    @router.post("/run-step")
    def run_step(req: RunStepRequest) -> dict[str, Any]:
        if req.content is None and not req.prompt:
            raise HTTPException(400, "content or prompt required")
        return svc().run_step(req)

    @router.post("/goals", status_code=202)
    def start_goal(req: GoalRequest) -> dict[str, Any]:
        return {"goal_id": svc().start_goal(req), "status": "running"}

    @router.get("/goals/{goal_id}")
    def goal_status(goal_id: str) -> dict[str, Any]:
        row = task_store.get_task(goal_id)
        if row is None:
            raise HTTPException(404, "goal not found")
        return row

    @router.get("/pending-prompt")
    def pending_prompt(goal_id: Optional[str] = None) -> dict[str, Any]:
        prompt = browser_bridge.pending(goal_id)
        if prompt is None:
            raise HTTPException(404, "no pending browser prompt")
        return prompt

    @router.post("/submit-dom-response")
    def submit_dom_response(req: DomResponseRequest) -> dict[str, Any]:
        try:
            browser_bridge.submit(req.goal_id, req.raw_dom_markdown_or_code)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            row = task_store.get_task(req.goal_id)
            if row and row.get("status") in ("committed", "rolled_back", "rejected", "error"):
                return row
            time.sleep(0.25)

        return {"goal_id": req.goal_id, "status": "accepted", "detail": "browser response submitted; autonomy step still running"}

    @router.get("/workspace/list")
    def workspace_list(subpath: str = "") -> dict[str, Any]:
        try:
            return svc().workspace_list(subpath)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.get("/workspace/read")
    def workspace_read(path: str) -> dict[str, Any]:
        try:
            return svc().workspace_read(path)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.post("/workspace/rollback")
    def workspace_rollback(req: RollbackRequest) -> dict[str, Any]:
        try:
            return svc().workspace_rollback(req.path)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.post("/command/verify")
    def command_verify(req: CommandVerifyRequest) -> dict[str, Any]:
        try:
            return svc().command_verify(req.preset)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    return router
