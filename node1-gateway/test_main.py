import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "test-key")
    return TestClient(main.app)


def test_browse_requires_api_key(client):
    response = client.post("/api/v1/browse", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_browse_rejects_when_no_node_is_online(client, monkeypatch):
    monkeypatch.setattr(main.mqtt_service, "get_nodes", lambda: [])
    response = client.post(
        "/api/v1/browse",
        headers={"x-omninode-key": "test-key"},
        json={"url": "https://example.com"},
    )
    assert response.status_code == 503
