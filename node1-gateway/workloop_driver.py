"""
Omninode Autonomous Workloop Driver (Fase 9)
- Orchestratore DAG e risoluzione dipendenze tra task
- Workflow di Safe Patching (branch temporanei, verifiche statiche, divieto accesso a main e file protetti)
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from goal_queue import TaskItem, GoalItem

class WorkloopDriver:
    def __init__(self):
        self.protected_files = [
            "policy", "acl", "keys", "audit", "main", ".env", "credentials", "secrets"
        ]

    def resolve_dag_dependencies(self, tasks: List[TaskItem]) -> List[TaskItem]:
        """Aggiorna lo stato dei task in base al completamento delle dipendenze (DAG)."""
        task_map = {t.task_id: t for t in tasks}
        completed_ids = {t.task_id for t in tasks if t.status == "completed"}

        for t in tasks:
            if t.status == "queued":
                if not t.depends_on:
                    t.status = "ready"
                else:
                    if all(dep_id in completed_ids for dep_id in t.depends_on):
                        t.status = "ready"
                    elif any(task_map.get(dep_id) and task_map[dep_id].status in ("failed", "cancelled", "blocked") for dep_id in t.depends_on):
                        t.status = "blocked"
        return tasks

    def validate_patch_safety(self, file_paths: List[str], risk_tier: int) -> Dict[str, Any]:
        """Verifica che la patch non tocchi file protetti e rispetti i Trust Tiers."""
        if risk_tier >= 4:
            return {"allowed": False, "reason": "Trust Tier 4 è severamente vietato all'agente autonomo."}
        
        if risk_tier >= 2:
            return {"allowed": False, "reason": f"Trust Tier {risk_tier} richiede esplicita approvazione umana."}

        for path in file_paths:
            path_lower = path.lower()
            for prot in self.protected_files:
                if prot in path_lower:
                    return {"allowed": False, "reason": f"Tentativo di modifica a file protetto o risorsa critica: '{path}' (match: {prot})."}

        return {"allowed": True, "reason": "Patch conforme ai guardrail di sicurezza e Trust Tier 0-1."}