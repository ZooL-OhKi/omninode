"""
Omninode Safe Self-Improvement Engine (Fase 6)
- Gestione dei livelli di fiducia (Trust Tiers 0-4)
- Policy di approvazione automatica o human-in-the-loop
- Protezione di file critici (ACL, policy, chiavi, audit)
"""
from __future__ import annotations

import os
from typing import Dict, Any, Literal

TrustTier = Literal[0, 1, 2, 3, 4]

PROTECTED_PATHS = [
    "security.md",
    "acl",
    "keys",
    "audit",
    "config/auth",
    ".env"
]

def evaluate_trust_tier(file_path: str, change_type: str) -> TrustTier:
    """Valuta il livello di rischio e assegna il Trust Tier appropriato."""
    lower_path = file_path.lower()
    
    # Livello 4: Policy, ACL, chiavi, audit (Vietato all'AI)
    for p in PROTECTED_PATHS:
        if p in lower_path:
            return 4
            
    # Livello 0: Documentazione, commenti, test puri (priorita massima sul path)
    if lower_path.endswith(".md") or "test_" in lower_path or change_type == "docs":
        return 0
        
    # Livello 3: Dipendenze, rete, executor, sicurezza, deploy
    if "requirements.txt" in lower_path or "go.mod" in lower_path or "gateway/main.py" in lower_path or "deploy" in lower_path:
        return 3
        
    # Livello 2: Nuove funzionalita limitate
    if change_type == "new_feature":
        return 2
        
    # Livello 1: Piccole correzioni locali e refactor sicuri
    if change_type == "refactor" or change_type == "bugfix":
        return 1
        
    return 2 # Default prudenziale per modifiche generiche

def validate_proposal(file_path: str, change_type: str) -> Dict[str, Any]:
    tier = evaluate_trust_tier(file_path, change_type)
    
    if tier == 4:
        return {
            "approved": False,
            "trust_tier": 4,
            "requires_human": True,
            "reason": "Modifica vietata: il file rientra nelle policy di sicurezza critiche (Tier 4)."
        }
        
    if tier == 3:
        return {
            "approved": False,
            "trust_tier": 3,
            "requires_human": True,
            "reason": "Richiesta approvazione umana obbligatoria per modifiche a infrastruttura o dipendenze (Tier 3)."
        }
        
    if tier == 2:
        return {
            "approved": False,
            "trust_tier": 2,
            "requires_human": True,
            "reason": "Richiesta approvazione umana per nuove funzionalita (Tier 2)."
        }
        
    # Tier 0 e 1: Approvazione automatica subordinata a verifica verde
    return {
        "approved": True,
        "trust_tier": tier,
        "requires_human": False,
        "reason": f"Approvazione automatica concessa per modifiche di livello Tier {tier}."
    }