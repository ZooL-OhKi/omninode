"""
Omninode Workspace Pool (Fase 12)
- Gestione di workspace isolati per goal, task e worker IA
"""
from __future__ import annotations

import os
from pathlib import Path

class WorkspacePool:
    def __init__(self, base_dir: str = "workspaces"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def allocate_workspace(self, goal_id: str, task_id: str, ai_worker: str) -> str:
        ws_path = self.base_dir / goal_id / task_id / ai_worker
        ws_path.mkdir(parents=True, exist_ok=True)
        return str(ws_path.resolve())