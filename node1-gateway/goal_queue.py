"""
Omninode Goal Queue & Operational Queue (Fase 9 & 15)
- Supporto retrocompatibile, persistenza e transizioni operative complete.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class TaskItem(BaseModel):
    task_id: str
    goal_id: str
    status: str = "pending"
    execution_id: str = ""
    risk_tier: int = 1
    dependencies: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)

class GoalItem(BaseModel):
    goal_id: str
    description: str = ""
    status: str = "pending"
    risk_tier: int = 1
    priority: int = 1

class GoalQueueDB:
    def __init__(self, db_path: str = "goals_queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS op_goals (
                    goal_id TEXT PRIMARY KEY,
                    description TEXT,
                    status TEXT,
                    risk_tier INTEGER,
                    priority INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS op_tasks (
                    task_id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    status TEXT,
                    execution_id TEXT,
                    risk_tier INTEGER
                )
            """)
            conn.commit()

    def add_goal(self, goal: GoalItem, tasks: Optional[List[TaskItem]] = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO op_goals VALUES (?, ?, ?, ?, ?)",
                         (goal.goal_id, goal.description, goal.status, goal.risk_tier, goal.priority))
            conn.commit()
        if tasks:
            for t in tasks:
                self.add_task(t)

    def get_goal(self, goal_id: str) -> Optional[GoalItem]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT goal_id, description, status, risk_tier, priority FROM op_goals WHERE goal_id = ?", (goal_id,))
            row = cursor.fetchone()
            if row:
                return GoalItem(goal_id=row[0], description=row[1], status=row[2], risk_tier=row[3], priority=row[4])
        return None

    def add_task(self, task: TaskItem):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO op_tasks VALUES (?, ?, ?, ?, ?)",
                         (task.task_id, task.goal_id, task.status, task.execution_id, task.risk_tier))
            conn.commit()

    def update_task_status(self, task_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE op_tasks SET status = ? WHERE task_id = ?", (status, task_id))
            conn.commit()

    def get_tasks_for_goal(self, goal_id: str) -> List[TaskItem]:
        tasks = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT task_id, goal_id, status, execution_id, risk_tier FROM op_tasks WHERE goal_id = ?", (goal_id,))
            for row in cursor.fetchall():
                tasks.append(TaskItem(task_id=row[0], goal_id=row[1], status=row[2], execution_id=row[3], risk_tier=row[4]))
        return tasks

class OperationalGoalQueue(GoalQueueDB):
    def claim_ready_task(self, task_id: str, execution_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT status FROM op_tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row and row[0] in ("ready", "pending", "queued"):
                conn.execute("UPDATE op_tasks SET status = 'assigned', execution_id = ? WHERE task_id = ?", (execution_id, task_id))
                conn.commit()
                return True
        return False

    def complete_task(self, task_id: str):
        self.update_task_status(task_id, "completed")

    def fail_task(self, task_id: str):
        self.update_task_status(task_id, "failed")

    def block_dependents(self, goal_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE op_tasks SET status = 'blocked' WHERE goal_id = ? AND status = 'pending'", (goal_id,))
            conn.commit()