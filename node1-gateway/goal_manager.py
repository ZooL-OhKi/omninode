"""
Omninode Autonomous WorkLoop Safety & Budget Engine (Fase 5)
- Gestione budget espliciti per goal (max_attempts, wall clock, file writes, ecc.)
- Checkpoint persistenti e gestione stati (running, paused, budget_exhausted, interrupted, completed)
"""
from __future__ import annotations

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class GoalBudget(BaseModel):
    max_attempts: int = 5
    max_wall_clock_seconds: int = 300
    max_file_writes: int = 20
    max_child_processes: int = 5
    max_command_executions: int = 10
    max_browser_interactions: int = 15
    max_audit_events: int = 100

class GoalCheckpoint(BaseModel):
    goal_id: str
    status: str = "running" # running, paused, budget_exhausted, interrupted, completed, failed, rolled_back
    attempt: int = 1
    budget_used: Dict[str, int] = Field(default_factory=lambda: {
        "attempts": 0,
        "file_writes": 0,
        "child_processes": 0,
        "command_executions": 0,
        "browser_interactions": 0,
        "audit_events": 0
    })
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target_file: str = "none"
    changed_files: list[str] = Field(default_factory=list)
    last_verification: str = "pending"
    pending_approval: bool = False
    rollback_available: bool = True
    error: Optional[str] = None

class GoalManager:
    def __init__(self, db_path: str = "workloop_goals.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goal_checkpoints (
                    goal_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    budget_used TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    target_file TEXT,
                    changed_files TEXT,
                    last_verification TEXT,
                    pending_approval INTEGER,
                    rollback_available INTEGER,
                    error TEXT
                )
            """)
            conn.commit()

    def save_checkpoint(self, cp: GoalCheckpoint):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO goal_checkpoints 
                (goal_id, status, attempt, budget_used, created_at, updated_at, target_file, changed_files, last_verification, pending_approval, rollback_available, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cp.goal_id,
                cp.status,
                cp.attempt,
                json.dumps(cp.budget_used),
                cp.created_at,
                datetime.now(timezone.utc).isoformat(),
                cp.target_file,
                json.dumps(cp.changed_files),
                cp.last_verification,
                1 if cp.pending_approval else 0,
                1 if cp.rollback_available else 0,
                cp.error
            ))
            conn.commit()

    def load_checkpoint(self, goal_id: str) -> Optional[GoalCheckpoint]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM goal_checkpoints WHERE goal_id = ?", (goal_id,)).fetchone()
            if not row:
                return None
            return GoalCheckpoint(
                goal_id=row["goal_id"],
                status=row["status"],
                attempt=row["attempt"],
                budget_used=json.loads(row["budget_used"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                target_file=row["target_file"] or "none",
                changed_files=json.loads(row["changed_files"] or "[]"),
                last_verification=row["last_verification"],
                pending_approval=bool(row["pending_approval"]),
                rollback_available=bool(row["rollback_available"]),
                error=row["error"]
            )