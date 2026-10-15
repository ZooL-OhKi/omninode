"""
Omninode Persistent Goal Queue (Fase 9)
- Coda persistente su SQLite per goal, task e dipendenze DAG
- Gestione priorità, ripresa dopo riavvio, timeout e audit
"""
from __future__ import annotations

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

TaskStatus = Literal["queued", "ready", "assigned", "running", "waiting_approval", "verification_failed", "blocked", "completed", "failed", "cancelled"]
GoalStatus = Literal["queued", "in_progress", "paused", "completed", "failed", "blocked"]

class TaskItem(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    depends_on: List[str] = Field(default_factory=list)
    capability: str = "python"
    risk_tier: int = 0
    input_hash: str = ""
    expected_output: str = ""
    timeout_seconds: int = 300
    max_attempts: int = 3
    verification_commands: List[str] = Field(default_factory=list)
    rollback_plan: str = "revert_changes"
    status: TaskStatus = "queued"

class GoalItem(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 5
    status: GoalStatus = "queued"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    depends_on: List[str] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    budget: Dict[str, Any] = Field(default_factory=lambda: {"max_attempts": 3, "wall_clock_seconds": 600})
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    assigned_node_id: Optional[str] = None
    execution_id: Optional[str] = None

class GoalQueueDB:
    def __init__(self, db_path: str = "goals_queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    priority INTEGER,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    data TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    status TEXT,
                    data TEXT,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                )
            """)
            conn.commit()

    def add_goal(self, goal: GoalItem, tasks: List[TaskItem]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO goals (goal_id, priority, status, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, ?)",
                (goal.goal_id, goal.priority, goal.status, goal.created_at, goal.updated_at, goal.model_dump_json())
            )
            for t in tasks:
                conn.execute(
                    "INSERT OR REPLACE INTO tasks (task_id, goal_id, status, data) VALUES (?, ?, ?, ?)",
                    (t.task_id, goal.goal_id, t.status, t.model_dump_json())
                )
            conn.commit()

    def get_goal(self, goal_id: str) -> Optional[GoalItem]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM goals WHERE goal_id = ?", (goal_id,))
            row = cur.fetchone()
            if row:
                return GoalItem(**json.loads(row[0]))
        return None

    def get_tasks_for_goal(self, goal_id: str) -> List[TaskItem]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM tasks WHERE goal_id = ?", (goal_id,))
            rows = cur.fetchall()
            return [TaskItem(**json.loads(r[0])) for r in rows]

    def update_task_status(self, task_id: str, status: TaskStatus):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM tasks WHERE task_id = ?", (task_id,))
            row = cur.fetchone()
            if row:
                t = TaskItem(**json.loads(row[0]))
                t.status = status
                conn.execute("UPDATE tasks SET status = ?, data = ? WHERE task_id = ?", (status, t.model_dump_json(), task_id))
                conn.commit()