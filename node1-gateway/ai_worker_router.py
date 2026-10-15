"""
Omninode AI Worker Router (Fase 12)
- Routing dei task verso Gemini o Perplexity in base al ruolo cognitivo
"""
from __future__ import annotations

from typing import Literal

AIRole = Literal["planner", "coder", "reviewer", "tester", "diagnostician"]
AIWorker = Literal["Gemini", "Perplexity", "OmniNode"]

class AIWorkerRouter:
    def route_task(self, role: AIRole) -> AIWorker:
        if role == "planner":
            return "Gemini"
        elif role == "coder":
            return "Gemini" # o Perplexity
        elif role == "reviewer":
            return "Perplexity"
        elif role == "tester":
            return "OmniNode"
        elif role == "diagnostician":
            return "Perplexity"
        return "Gemini"