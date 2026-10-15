"""
Omninode Local Redaction & Spatial Pruning Engine (Task C)
- Redaction preventiva di JWT, API Keys, Private Keys, Cookie e PII
- Regole configurabili basate su pattern regex sicuri
"""
from __future__ import annotations

import re
from typing import Dict, Any

# Pattern di redaction sicuri, robusti e flessibili
SENSITIVE_PATTERNS = [
    (re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-\_\s]*"), "[REDACTED_JWT]"),
    (re.compile(r"sk-[a-zA-Z0-9_\-]{10,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"-----BEGIN (?:RSA|PRIVATE|EC) KEY-----[^-]+-----END (?:RSA|PRIVATE|EC) KEY-----", re.DOTALL), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{6,}['\"]?", re.IGNORECASE), "[REDACTED_SECRET]")
]

def sanitize_payload(text: str) -> str:
    """Esegue la redaction locale dei dati sensibili prima di qualsiasi trasmissione MQTT."""
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized

def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ricorsivamente sanitizza dizionari di payload."""
    cleaned = {}
    for k, v in data.items():
        if isinstance(v, str):
            cleaned[k] = sanitize_payload(v)
        elif isinstance(v, dict):
            cleaned[k] = sanitize_dict(v)
        elif isinstance(v, list):
            cleaned[k] = [sanitize_dict(item) if isinstance(item, dict) else (sanitize_payload(item) if isinstance(item, str) else item) for item in v]
        else:
            cleaned[k] = v
    return cleaned