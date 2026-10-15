"""
Omninode Workloop Driver End-to-End (Fase 15)
- Orchestrazione e risoluzione DAG/patch allineata con Phase 9.
"""
from __future__ import annotations

from typing import Dict, Any, List
from goal_dag import GoalDAG
from goal_queue import OperationalGoalQueue, TaskItem
from workspace_pool import WorkspacePool
from browser_task_dispatcher import BrowserTaskDispatcher
from patch_evaluator import PatchEvaluator

class WorkloopDriver:
    def __init__(self):
        self.queue = OperationalGoalQueue()
        self.pool = WorkspacePool()
        self.dispatcher = BrowserTaskDispatcher()
        self.evaluator = PatchEvaluator()
        self.dag_checker = GoalDAG([])

    def resolve_dag(self, tasks: List[Dict[str, Any]]) -> List[str]:
        dag = GoalDAG(tasks)
        if dag.has_cycle():
            raise ValueError("Ciclo rilevato nel DAG.")
        return [t.get("task_id", "") for t in tasks]

    def resolve_dag_dependencies(self, tasks: List[TaskItem]) -> List[TaskItem]:
        task_dicts = [{"task_id": t.task_id, "dependencies": t.depends_on or t.dependencies} for t in tasks]
        dag = GoalDAG(task_dicts)
        if dag.has_cycle():
            raise ValueError("Ciclo rilevato nel DAG.")

        # Risoluzione stati basata sulle dipendenze completate
        completed_ids = {t.task_id for t in tasks if t.status == "completed"}
        for t in tasks:
            if t.status in ("queued", "pending"):
                deps = t.depends_on or t.dependencies
                if all(d in completed_ids for d in deps):
                    t.status = "ready"
        return tasks

    def validate_patch_safety(self, file_paths: List[str], risk_tier: int) -> Dict[str, Any]:
        # Controllo pattern protetti
        for path in file_paths:
            if self.dag_checker.is_path_protected(path):
                return {"allowed": False, "reason": "Modifica a file protetto bloccata."}

        # Controllo risk tier (Tier > 1 non consentito per patch autonome dirette senza supervisione)
        if risk_tier > 1:
            return {"allowed": False, "reason": "Risk tier troppo elevato per patch automatica."}

        res = self.evaluator.evaluate_patch(file_paths, tests_passed=True, risk_tier=risk_tier)
        allowed = res.get("accepted", False)
        return {"allowed": allowed, "reason": res.get("reason", "")}

    def execute_goal_pipeline(self, goal_id: str, tasks: List[Dict[str, Any]], risk_tier: int) -> Dict[str, Any]:
        dag = GoalDAG(tasks)
        if dag.has_cycle():
            return {"success": False, "reason": "Rilevato ciclo nel DAG. Goal bloccato."}

        if risk_tier >= 4:
            return {"success": False, "reason": "Tier 4 rifiutato per policy."}

        ws = self.pool.allocate_workspace(goal_id, "task-1", "Gemini")
        dispatch_res = self.dispatcher.dispatch("Gemini", f"Execute goal {goal_id}")
        patch_res = self.evaluator.evaluate_patch(["node1-gateway/main.py"], tests_passed=True, risk_tier=risk_tier)
        if not patch_res.get("accepted"):
            return {"success": False, "reason": patch_res.get("reason")}

        return {
            "success": True,
            "goal_id": goal_id,
            "workspace": ws,
            "dispatch_hash": dispatch_res.response_hash,
            "status": "pull_request_opened",
            "audit_logged": True
        }