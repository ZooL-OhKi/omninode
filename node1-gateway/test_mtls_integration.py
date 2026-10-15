"""Test di integrazione mTLS end-to-end e fail-closed per il gateway OmniNode."""
import os
import ssl
import pytest
from fastapi.testclient import TestClient

import main
from mqtt_service import mqtt_service


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "MCP_SECRET", "test-key")
    return TestClient(main.app)


def test_mqtt_tls_params_missing_files_fails_closed(monkeypatch, tmp_path):
    """Verifica che mqtt_tls_params sollevi un'eccezione se i certificati mTLS non esistono."""
    monkeypatch.setenv("MQTT_CA_PATH", str(tmp_path / "nonexistent-ca.crt"))
    monkeypatch.setenv("MQTT_CERT_PATH", str(tmp_path / "nonexistent-client.crt"))
    monkeypatch.setenv("MQTT_KEY_PATH", str(tmp_path / "nonexistent-client.key"))

    with pytest.raises(RuntimeError, match="Certificato MQTT mancante o non leggibile"):
        main.mqtt_tls_params()


def test_readyz_fails_when_mqtt_not_ready(client, monkeypatch):
    """Verifica che /readyz restituisca 503 se il client MQTT non ha completato l'handshake mTLS."""
    mqtt_service.mqtt_ready.clear()
    response = client.get("/readyz")
    assert response.status_code == 503
    assert "MQTT non pronto" in response.text
