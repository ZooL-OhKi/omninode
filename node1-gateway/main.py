from fastapi import FastAPI, Header, HTTPException
import paho.mqtt.client as mqtt
import os

app = FastAPI(title="Omninode Node 1 Gateway")

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

AUTH_TOKEN = os.getenv("OMNINODE_SECRET_TOKEN", "cambia-questo-token-segreto")

@app.post("/mcp/task")
def dispatch_task(payload: dict, x_omninode_key: str = Header(None)):
    if x_omninode_key != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized access to OmniNode Gateway")

    mqtt_client.publish("omninode/tasks", str(payload))
    return {"status": "dispatched", "target": "omni-client"}

@app.get("/health")
def health_check():
    return {"status": "online", "mode": "cloudflare-tunnel"}