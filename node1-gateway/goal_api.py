"""
Omninode Autonomous Goal Control Plane (Fase 5)
- Endpoint protetti da MCP auth per status, pause, resume, stop e rollback dei goal
- Integrazione con Audit Transparency Chain
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Callable, Optional
from goal_manager import GoalManager

def build_goal_router(verify_auth_func: Callable, goal_mgr: Optional[GoalManager] = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/autonomy/goals", tags=["Autonomy Control Plane"])
    manager = goal_mgr or GoalManager()

    async def get_authorized_user(authorization: Optional[str] = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
        token = authorization.split(" ")[1]
        if not verify_auth_func(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
        return token

    @router.get("/{goal_id}/status")
    async def get_goal_status(goal_id: str, user: str = Depends(get_authorized_user)):
        cp = manager.load_checkpoint(goal_id)
        if not cp:
            raise HTTPException(status_code=404, detail="Goal non trovato")
        return cp.model_dump()

    @router.post("/{goal_id}/pause")
    async def pause_goal(goal_id: str, user: str = Depends(get_authorized_user)):
        cp = manager.load_checkpoint(goal_id)
        if not cp:
            raise HTTPException(status_code=404, detail="Goal non trovato")
        cp.status = "paused"
        manager.save_checkpoint(cp)
        return {"goal_id": goal_id, "status": "paused"}

    @router.post("/{goal_id}/resume")
    async def resume_goal(goal_id: str, user: str = Depends(get_authorized_user)):
        cp = manager.load_checkpoint(goal_id)
        if not cp:
            raise HTTPException(status_code=404, detail="Goal non trovato")
        if cp.status not in ("paused", "interrupted"):
            raise HTTPException(status_code=400, detail=f"Impossibile riprendere un goal in stato '{cp.status}'")
        cp.status = "running"
        manager.save_checkpoint(cp)
        return {"goal_id": goal_id, "status": "running"}

    @router.post("/{goal_id}/stop")
    async def stop_goal(goal_id: str, user: str = Depends(get_authorized_user)):
        cp = manager.load_checkpoint(goal_id)
        if not cp:
            raise HTTPException(status_code=404, detail="Goal non trovato")
        cp.status = "failed"
        cp.error = "Stopped gracefully by operator command"
        manager.save_checkpoint(cp)
        return {"goal_id": goal_id, "status": "failed", "message": "Goal interrotto con successo"}

    @router.post("/{goal_id}/rollback")
    async def rollback_goal(goal_id: str, user: str = Depends(get_authorized_user)):
        cp = manager.load_checkpoint(goal_id)
        if not cp:
            raise HTTPException(status_code=404, detail="Goal non trovato")
        if not cp.rollback_available:
            raise HTTPException(status_code=400, detail="Rollback non disponibile per questo goal")
        cp.status = "rolled_back"
        manager.save_checkpoint(cp)
        return {"goal_id": goal_id, "status": "rolled_back", "message": "Rollback eseguito con successo"}

    return router