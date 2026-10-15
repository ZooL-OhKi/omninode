"""
Omninode Patch Evaluator (Fase 12)
- Valutazione patch, esecuzione test, controllo file protetti e selezione della migliore proposta
"""
from __future__ import annotations

from typing import Dict, Any, List

class PatchEvaluator:
    def __init__(self):
        self.protected_files = ["acl.conf", "policy", "keys", "audit"]

    def evaluate_patch(self, file_paths: List[str], tests_passed: bool, risk_tier: int) -> Dict[str, Any]:
        if risk_tier >= 4:
            return {"accepted": False, "reason": "Tier 4 vietato."}
        for f in file_paths:
            if any(p in f.lower() for p in self.protected_files):
                return {"accepted": False, "reason": f"Tentativo di modifica a file protetto: {f}"}
        if not tests_passed:
            return {"accepted": False, "reason": "Test falliti."}
        return {"accepted": True, "reason": "Patch certificata e conforme."}