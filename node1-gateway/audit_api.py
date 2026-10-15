"""
Omninode Audit API Router
"""
from fastapi import APIRouter, Depends, Query
from audit_transparency import AuditTransparencyLog

audit_log = AuditTransparencyLog()


def build_audit_router(auth_dependency) -> APIRouter:
    router = APIRouter(prefix="/api/v1/audit", tags=["Audit Transparency Log"])

    @router.get("/events", dependencies=[Depends(auth_dependency)])
    def get_audit_events(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ):
        events = audit_log.get_events(limit=limit, offset=offset)
        total = audit_log.count_events()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": events,
        }

    @router.get("/verify", dependencies=[Depends(auth_dependency)])
    def verify_audit_chain():
        return audit_log.verify_chain()

    return router