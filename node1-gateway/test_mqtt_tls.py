import os

import pytest

from mqtt_topics import MQTTTopics


def test_v1_topics_are_used():
    os.environ["OMNINODE_MQTT_TOPIC_VERSION"] = "v1"
    assert MQTTTopics.tasks("worker-1") == "omninode/v1/nodes/worker-1/tasks"
    assert MQTTTopics.responses("worker-1") == "omninode/v1/nodes/worker-1/responses"
    assert MQTTTopics.heartbeat("worker-1") == "omninode/v1/nodes/worker-1/heartbeat"


def test_missing_mqtt_certificate_fails_closed(monkeypatch, tmp_path):
    from main import mqtt_tls_params

    monkeypatch.setenv("MQTT_CA_PATH", str(tmp_path / "missing-ca.crt"))
    monkeypatch.setenv("MQTT_CERT_PATH", str(tmp_path / "missing-client.crt"))
    monkeypatch.setenv("MQTT_KEY_PATH", str(tmp_path / "missing-client.key"))

    with pytest.raises(RuntimeError, match="Certificato MQTT mancante"):
        mqtt_tls_params()
