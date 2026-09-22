import time
from datetime import datetime
from audit import AuditEventEngine

class PolicyEngine:
    def __init__(self, audit_engine: AuditEventEngine):
        self.audit = audit_engine
        self.capabilities = []

    def grant(self, capability: dict):
        self.capabilities.append(capability)

    def authorize(self, agent_id: str, goal_id: str, capability: str, resource: str, action: str) -> tuple[bool, str]:
        now = time.time()
        for cap in self.capabilities:
            if cap.get("agent_id") == agent_id and cap.get("goal_id") == goal_id:
                if cap.get("capability") == capability and resource.startswith(cap.get("workspace")):
                    expires_at = cap.get("expires_at")
                    if expires_at:
                        try:
                            if isinstance(expires_at, str):
                                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                                if now > exp_dt.timestamp():
                                    continue
                        except Exception:
                            pass

                    audit_id = self.audit.log_decision("allow", "capability_match", agent_id, goal_id, resource, action)
                    return True, audit_id

        audit_id = self.audit.log_decision("deny", "default_deny", agent_id, goal_id, resource, action)
        return False, audit_id
