"""
Omninode Goal DAG Driver & Cycle Detection (Fase 15)
- Gestione DAG, rilevamento cicli e validazione percorsi protetti basati su pattern precisi.
"""
from __future__ import annotations

from typing import List, Dict, Any, Set
import fnmatch

class GoalDAG:
    def __init__(self, tasks: List[Dict[str, Any]]):
        self.tasks = tasks
        self.protected_patterns = [
            "policy/**", "acl/**", "keys/**", "audit/**",
            ".env", "credentials/**", "secrets/**"
        ]

    def has_cycle(self) -> bool:
        graph: Dict[str, List[str]] = {}
        for t in self.tasks:
            tid = t.get("task_id")
            deps = t.get("dependencies", [])
            graph[tid] = deps

        visited: Dict[str, bool] = {}
        rec_stack: Dict[str, bool] = {}

        def dfs(node: str) -> bool:
            visited[node] = True
            rec_stack[node] = True
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif rec_stack.get(neighbor, False):
                    return True
            rec_stack[node] = False
            return False

        for task in self.tasks:
            tid = task.get("task_id")
            if tid not in visited:
                if dfs(tid):
                    return True
        return False

    def is_path_protected(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(normalized, pattern) or normalized.startswith(pattern.rstrip("/*")):
                return True
        return False