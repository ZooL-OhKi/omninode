import pytest
import os
from pydantic import ValidationError
from mqtt_topics import MQTTTopics, get_topic_version
from mqtt_envelope import MQTTEnvelope

def test_topic_builder_legacy(monkeypatch):
    monkeypatch.setenv("OMNINODE_MQTT_TOPIC_VERSION", "legacy")
    assert MQTTTopics.tasks("node-01") == "omninode/nodes/node-01/tasks"
    assert MQTTTopics.responses("node-01") == "omninode/nodes/node-01/responses"
    assert MQTTTopics.heartbeat("node-01") == "omninode/nodes/node-01/heartbeat"

def test_topic_builder_v1(monkeypatch):
    monkeypatch.setenv("OMNINODE_MQTT_TOPIC_VERSION", "v1")
    assert MQTTTopics.tasks("node-01") == "omninode/v1/nodes/node-01/tasks"
    assert MQTTTopics.responses("node-01") == "omninode/v1/nodes/node-01/responses"
    assert MQTTTopics.heartbeat("node-01") == "omninode/v1/nodes/node-01/heartbeat"

def test_topic_fail_fast_invalid_version(monkeypatch):
    monkeypatch.setenv("OMNINODE_MQTT_TOPIC_VERSION", "invalid-version")
    with pytest.raises(ValueError, match="Configurazione MQTT Topic non valida"):
        get_topic_version()

def test_envelope_valid():
    env = MQTTEnvelope(
        schema_version=1,
        message_type="task",
        actor="gateway",
        node_id="node-01",
        task_id="task-123",
        payload={"action": "run"}
    )
    assert env.schema_version == 1
    assert env.node_id == "node-01"
    assert env.verify_identity("gateway") is True

def test_envelope_invalid_schema():
    with pytest.raises(ValidationError):
        MQTTEnvelope(
            schema_version=2,  # Non supportato, atteso 1
            message_type="task",
            actor="gateway",
            node_id="node-01",
            payload={}
        )

def test_identity_verification():
    env = MQTTEnvelope(
        schema_version=1,
        message_type="response",
        actor="node",
        node_id="01",
        payload={}
    )
    # L'identità autenticata del nodo deve essere node-01
    assert env.verify_identity("node-01") is True
    assert env.verify_identity("gateway") is False

def test_idempotency_message_id():
    from mqtt_envelope import MQTTEnvelope
    env1 = MQTTEnvelope(schema_version=1, message_type="task", actor="gateway", node_id="node-01", task_id="t-1")
    env2 = MQTTEnvelope(schema_version=1, message_type="task", actor="gateway", node_id="node-01", task_id="t-1")
    # Ogni messaggio deve avere un message_id univoco (UUID v4)
    assert env1.message_id != env2.message_id

def test_acl_identity_spoofing_rejection():
    # Un nodo non può impersonare un altro nodo o il gateway
    env = MQTTEnvelope(schema_version=1, message_type="task", actor="node", node_id="01", task_id="t-1")
    # L'identità autenticata inviata dal broker è node-02, ma il payload dichiara node-01
    assert env.verify_identity("node-02") is False
    # Il gateway non può firmare come nodo
    assert env.verify_identity("gateway") is False
