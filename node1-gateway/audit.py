import uuid
import time
import threading

class AuditEventEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self.logs = []

    def log_decision(self, decision: str, reason: str, agent_id: str, goal_id: str, resource: str, action: str) -> str:
        audit_id = f"audit-{uuid.uuid4().hex[:8]}"
        entry = {
            "audit_id": audit_id,
            "timestamp": time.time(),
            "decision": decision,
            "reason": reason,
            "agent_id": agent_id,
            "goal_id": goal_id,
            "resource": resource,
            "action": action
        }
        with self._lock:
            self.logs.append(entry)
        return audit_id
