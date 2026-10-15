import os

os.environ.setdefault("MQTT_BROKER", "127.0.0.1")
os.environ.setdefault("MQTT_PORT", "8883")
os.environ.setdefault("MCP_SECRET", "test-mcp-secret")
os.environ.setdefault("MQTT_CA_PATH", "/tmp/omninode-test-ca.crt")
os.environ.setdefault("MQTT_CERT_PATH", "/tmp/omninode-test-gateway.crt")
os.environ.setdefault("MQTT_KEY_PATH", "/tmp/omninode-test-gateway.key")
os.environ.setdefault("MQTT_HOST", "127.0.0.1")
os.environ.setdefault("MQTT_USERNAME", "gateway")
os.environ.setdefault("MQTT_PASSWORD", "test-mqtt-password")
