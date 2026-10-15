"""
Omninode Secure Webhook Ingestion (Fase 10)
- Verifica firme HMAC-SHA256, timestamp freshness e prevenzione replay
"""
from __future__ import annotations

import hmac
import hashlib
import time
from typing import Dict, Any

class SecureWebhookVerifier:
    def __init__(self, secret_key: str, max_age_seconds: int = 300):
        self.secret_key = secret_key.encode("utf-8")
        self.max_age_seconds = max_age_seconds
        self.seen_signatures = set()

    def verify_request(self, payload_body: bytes, signature_header: str, timestamp_header: str) -> Dict[str, Any]:
        try:
            req_time = int(timestamp_header)
        except (ValueError, TypeError):
            return {"valid": False, "reason": "Timestamp non valido."}

        current_time = int(time.time())
        if abs(current_time - req_time) > self.max_age_seconds:
            return {"valid": False, "reason": "Timestamp scaduto o futuro (prevenzione replay)."}

        if signature_header in self.seen_signatures:
            return {"valid": False, "reason": "Firma già utilizzata (replay attack rilevato)."}

        expected_sig = hmac.new(self.secret_key, payload_body + timestamp_header.encode("utf-8"), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_sig, signature_header):
            return {"valid": False, "reason": "Firma HMAC non valida."}

        self.seen_signatures.add(signature_header)
        return {"valid": True, "reason": "Webhook verificato con successo."}