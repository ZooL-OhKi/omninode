import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "MCP_SECRET", "test-key")
    return TestClient(main.app)


def test_nodes_endpoint_is_public(client):
    response = client.get("/api/v1/nodes")
    assert response.status_code == 200
    assert response.json() == {}


def test_mcp_requires_token(client):
    response = client.post("/mcp", json={"method": "ping"})
    assert response.status_code == 401


def test_mcp_with_valid_token_is_not_unauthorized(client):
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer test-key"},
        json={"method": "ping"},
    )
    assert response.status_code != 401
