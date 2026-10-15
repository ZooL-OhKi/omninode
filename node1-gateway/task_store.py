import sqlite3
import json
import os
from typing import Any, Dict, Optional

DB_PATH = os.getenv("OMNINODE_DB_PATH", "tasks.db")

def get_connection():
    return sqlite3.connect(DB_PATH, isolation_level=None)

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                payload TEXT,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def create_task(task_id: str, task_type: str, payload: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tasks (task_id, task_type, payload, status) VALUES (?, ?, ?, ?)",
            (task_id, task_type, json.dumps(payload), "queued")
        )

def update_task_status(task_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, result = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
            (status, json.dumps(result) if result else None, error, task_id)
        )

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
