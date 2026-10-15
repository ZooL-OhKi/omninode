"""
Omninode Risk Classifier (Fase 10)
- Classificazione deterministica del rischio per goal e task (Tier 0-4)
- Regole di blocco per Tier >= 2 e divieto assoluto per Tier 4
"""
from __future__ import annotations

from typing import Dict, Any, List, Literal

RiskTier = Literal[0, 1, 2, 3, 4]

class RiskClassifier:
    def __init__(self):
        self.protected_keywords = ["policy", "acl", "key", "audit", "secret", "credential", "main"]

    def classify_task(self, description: str, file_paths: List[str]) -> RiskTier:
        desc_lower = description.lower()
        
        # Tier 4: Modifiche a policy, ACL, chiavi, audit
        for path in file_paths:
            path_l = path.lower()
            if any(k in path_l for k in self.protected_keywords):
                return 4

        if any(k in desc_lower for k in ["policy", "acl", "signature key", "audit log"]):
            return 4

        # Tier 3: Reti, dipendenze, executor, sicurezza, deploy
        if any(k in desc_lower for k in ["deploy", "network", "dependency", "executor", "security", "socket"]):
            return 3

        # Tier 2: Nuove funzionalità, modifiche strutturali, multi-modulo
        if any(k in desc_lower for k in ["new feature", "architecture", "structural", "multi-module"]):
            return 2

        # Tier 1: Piccole correzioni locali, refactor sicuri
        if any(k in desc_lower for k in ["refactor", "fix", "local", "clean"]):
            return 1

        # Tier 0: Documentazione, commenti, test puri
        if any(k in desc_lower for k in ["doc", "comment", "test", "readme"]):
            return 0

        return 1 # Default conservativo