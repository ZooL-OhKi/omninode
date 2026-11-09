import os

os.environ.setdefault("MQTT_BROKER", "127.0.0.1")
os.environ.setdefault("MQTT_PORT", "8883")
os.environ.setdefault("MCP_SECRET", "test-mcp-secret")
os.environ.setdefault("MQTT_CA_PATH", "missing-ca.crt")
os.environ.setdefault("MQTT_CERT_PATH", "missing-client.crt")
os.environ.setdefault("MQTT_KEY_PATH", "missing-client.key")

import pytest
from fastapi.testclient import TestClient

import main
from mqtt_service import mqtt_service


class FakeMQTTClient:
    published: list[tuple[str, str, int]] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def publish(self, topic: str, payload: str, qos: int = 0, **kwargs):
        FakeMQTTClient.published.append((topic, payload, qos))
        for task_id, future in list(main.pending_mcp_requests.items()):
            if not future.done():
                future.set_result({"task_id": task_id, "status": "completed"})


@pytest.fixture
def client(monkeypatch):
    FakeMQTTClient.published.clear()
    monkeypatch.setattr(main, "MCP_SECRET", "test-key")
    monkeypatch.setattr(main, "aiomqtt", type("DummyAiomqtt", (), {"Client": FakeMQTTClient}))
    monkeypatch.setattr(mqtt_service, "publish", FakeMQTTClient().publish)
    monkeypatch.setattr(mqtt_service, "active_nodes", {})
    monkeypatch.setattr(mqtt_service, "agent_routing", {"agent_1": "worker-1"})
    return TestClient(main.app)


def test_nodes_endpoint_is_public(client):
    response = client.get("/api/v1/nodes")
    assert response.status_code == 200
    assert response.json() == {}


def test_mcp_requires_token(client):
    response = client.post("/mcp", json={"method": "ping"})
    assert response.status_code == 401


def test_mcp_with_valid_token_uses_mqtt(client):
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer test-key"},
        json={"id": "req-1", "method": "ping", "params": {"agent_id": "agent_1"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "req-1"
    assert body["result"]["status"] == "completed"


def test_approve_requires_auth(client):
    response = client.post(
        "/api/v1/approve",
        json={"task_id": "t1", "agent_id": "agent_1", "decision": "approve"},
    )
    assert response.status_code in (401, 403)


def test_approve_with_valid_token_uses_mqtt(client):
    response = client.post(
        "/api/v1/approve",
        headers={"Authorization": "Bearer test-key"},
        json={"task_id": "t1", "agent_id": "agent_1", "decision": "approve"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "node_id": "worker-1"}
    assert any(
        topic == "omninode/v1/nodes/worker-1/control"
        for topic, _, _ in FakeMQTTClient.published
    )
