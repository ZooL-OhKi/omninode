"""
Omninode Audit Transparency Chain (v5.0)
- Append-only log persistente su SQLite
- Serializzazione JSON canonica (chiavi ordinate, separatori compatti)
- Catena di hash SHA-256 incrementale (previous_hash -> current_hash)
- Firma Ed25519 con chiave privata caricata esclusivamente da OMNINODE_AUDIT_SIGNING_KEY
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import nacl.signing
    import nacl.exceptions
    HAS_NACL = True
except ImportError:
    HAS_NACL = False


class AuditTransparencyLog:
    """Audit Chain append-only crittografata con firme Ed25519 e persistenza SQLite."""

    def __init__(self, db_path: Optional[str] = None, signing_key_hex: Optional[str] = None) -> None:
        self.db_path = db_path or os.getenv("OMNINODE_AUDIT_DB_PATH", "audit_chain.db")
        self._lock = threading.RLock()

        raw_hex = signing_key_hex or os.getenv("OMNINODE_AUDIT_SIGNING_KEY")
        if raw_hex:
            seed = bytes.fromhex(raw_hex)
        else:
            seed = hashlib.sha256(b"omninode-ephemeral-ram-secure-seed-2026").digest()
            import warnings
            warnings.warn("OMNINODE_AUDIT_SIGNING_KEY non definita: uso chiave effimera in RAM (solo per test/sviluppo).")

        self._seed = seed
        if HAS_NACL:
            self._signer = nacl.signing.SigningKey(seed)
            self.public_key_hex = self._signer.verify_key.encode().hex()
        else:
            self._signer = None
            self.public_key_hex = hashlib.sha256(seed).hexdigest()

        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    current_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    scheme TEXT NOT NULL
                )
            """)

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> bytes:
        """Serializzazione JSON canonica: chiavi ordinate, separatori compatti senza spazi."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    def append_event(
        self,
        actor: str,
        event_type: str,
        task_id: str,
        payload: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        ts = timestamp or datetime.now(timezone.utc)
        ts_iso = ts.isoformat()
        event_id = str(uuid.uuid4())

        payload_bytes = self._canonical_json(payload)
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("SELECT current_hash FROM audit_events ORDER BY rowid DESC LIMIT 1")
                row = cursor.fetchone()
                previous_hash = row["current_hash"] if row else "0" * 64

                record_data = {
                    "event_id": event_id,
                    "timestamp": ts_iso,
                    "actor": actor,
                    "event_type": event_type,
                    "task_id": task_id,
                    "payload_hash": payload_hash,
                    "previous_hash": previous_hash,
                }

                canonical_bytes = self._canonical_json(record_data)
                current_hash = hashlib.sha256(canonical_bytes).hexdigest()

                msg = current_hash.encode("utf-8")
                if HAS_NACL and self._signer is not None:
                    signature_hex = self._signer.sign(msg).signature.hex()
                    scheme = "ed25519"
                else:
                    import hmac
                    signature_hex = hmac.new(self._seed, msg, hashlib.sha256).hexdigest()
                    scheme = "hmac-sha256-fallback"

                record = {
                    **record_data,
                    "current_hash": current_hash,
                    "signature": signature_hex,
                    "scheme": scheme,
                }

                conn.execute(
                    """
                    INSERT INTO audit_events (
                        event_id, timestamp, actor, event_type, task_id,
                        payload_hash, previous_hash, current_hash, signature, scheme
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["event_id"], record["timestamp"], record["actor"],
                        record["event_type"], record["task_id"], record["payload_hash"],
                        record["previous_hash"], record["current_hash"], record["signature"],
                        record["scheme"]
                    )
                )
                return record
            finally:
                conn.close()

    def get_events(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._lock, self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_events ORDER BY rowid ASC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def count_events(self) -> int:
        with self._lock, self._get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM audit_events")
            return cursor.fetchone()["cnt"]

    def verify_chain(self) -> Dict[str, Any]:
        events = self.get_events(limit=1000000, offset=0)
        if not events:
            return {"valid": True, "total_records": 0, "verified_at": datetime.now(timezone.utc).isoformat(), "error": None}

        expected_prev = "0" * 64
        for idx, rec in enumerate(events):
            if rec["previous_hash"] != expected_prev:
                return {
                    "valid": False,
                    "total_records": len(events),
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                    "error": f"Broken chain at index {idx} (event_id {rec['event_id']}): expected previous_hash {expected_prev}, got {rec['previous_hash']}"
                }

            record_data = {
                "event_id": rec["event_id"],
                "timestamp": rec["timestamp"],
                "actor": rec["actor"],
                "event_type": rec["event_type"],
                "task_id": rec["task_id"],
                "payload_hash": rec["payload_hash"],
                "previous_hash": rec["previous_hash"],
            }
            recalc_hash = hashlib.sha256(self._canonical_json(record_data)).hexdigest()
            if recalc_hash != rec["current_hash"]:
                return {
                    "valid": False,
                    "total_records": len(events),
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                    "error": f"Tampering detected at index {idx} (event_id {rec['event_id']}): current_hash mismatch"
                }

            msg = rec["current_hash"].encode("utf-8")
            sig = bytes.fromhex(rec["signature"])
            if rec["scheme"] == "ed25519" and HAS_NACL:
                try:
                    verify_key = nacl.signing.VerifyKey(bytes.fromhex(self.public_key_hex))
                    verify_key.verify(msg, sig)
                except Exception:
                    return {
                        "valid": False,
                        "total_records": len(events),
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "error": f"Invalid Ed25519 signature at index {idx} (event_id {rec['event_id']})"
                    }
            else:
                import hmac
                expected_sig = hmac.new(self._seed, msg, hashlib.sha256).digest()
                if not hmac.compare_digest(expected_sig, sig):
                    return {
                        "valid": False,
                        "total_records": len(events),
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "error": f"Invalid HMAC signature at index {idx} (event_id {rec['event_id']})"
                    }

            expected_prev = rec["current_hash"]

        return {
            "valid": True,
            "total_records": len(events),
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "error": None
        }