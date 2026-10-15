"""
Omninode Multi-AI Coordinator (Fase 11)
- Coordinamento di più IA (planner, coder, reviewer, tester, integrator) in workspace confinati
- Prevenzione conflitti sui file e verifica patch prima dell'integrazione
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

AIRole = Literal["planner", "coder", "reviewer", "tester", "integrator"]

class AIProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    role: AIRole
    assigned_files: List[str] = Field(default_factory=list)
    diff_hash: str = ""
    tests_passed: bool = False
    risk_tier: int = 0
    status: str = "proposed" # proposed, verified, rejected, merged

class MultiAICoordinator:
    def __init__(self):
        self.proposals: Dict[str, AIProposal] = {}
        self.locked_files: set = set()

    def submit_proposal(self, goal_id: str, role: AIRole, assigned_files: List[str], diff_hash: str, risk_tier: int) -> Dict[str, Any]:
        # Verifica conflitti sui file assegnati
        for f in assigned_files:
            if f in self.locked_files:
                return {"success": False, "error": f"Conflitto: il file '{f}' è già bloccato da un'altra IA."}

        proposal = AIProposal(
            goal_id=goal_id,
            role=role,
            assigned_files=assigned_files,
            diff_hash=diff_hash,
            risk_tier=risk_tier
        )
        self.proposals[proposal.proposal_id] = proposal
        for f in assigned_files:
            self.locked_files.add(f)

        return {"success": True, "proposal_id": proposal.proposal_id}

    def verify_proposal(self, proposal_id: str, tests_passed: bool) -> Dict[str, Any]:
        prop = self.proposals.get(proposal_id)
        if not prop:
            return {"success": False, "error": "Proposta non trovata."}

        prop.tests_passed = tests_passed
        if tests_passed:
            prop.status = "verified"
        else:
            prop.status = "rejected"
            # Rilascia i file bloccati in caso di rifiuto
            for f in prop.assigned_files:
                if f in self.locked_files:
                    self.locked_files.remove(f)

        return {"success": True, "status": prop.status}