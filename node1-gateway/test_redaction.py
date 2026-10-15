import pytest
from redaction_engine import sanitize_payload, sanitize_dict

def test_jwt_redaction():
    raw = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    cleaned = sanitize_payload(raw)
    assert "[REDACTED_JWT]" in cleaned
    assert "eyJhbGci" not in cleaned

def test_api_key_redaction():
    raw = "My secret key is sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
    cleaned = sanitize_payload(raw)
    assert "[REDACTED_API_KEY]" in cleaned
    assert "sk-proj-123" not in cleaned

def test_dict_recursive_sanitization():
    payload = {
        "user": "admin",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "nested": {"api_key": "sk-1234567890abcdef"}
    }
    cleaned = sanitize_dict(payload)
    assert cleaned["token"] == "[REDACTED_JWT]"
    assert cleaned["nested"]["api_key"] == "[REDACTED_API_KEY]"