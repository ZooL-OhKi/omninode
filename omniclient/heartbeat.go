package main

import (
	"encoding/json"
	"fmt"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// publishHeartbeat invia un heartbeat periodico sul topic
// omninode/nodes/{nodeID}/heartbeat con la lista degli agent supportati.
func publishHeartbeat(client mqtt.Client, nodeID string, agents []string) {
	topic := fmt.Sprintf("omninode/nodes/%s/heartbeat", nodeID)
	payload := map[string]interface{}{
		"node_id":          nodeID,
		"status":           "online",
		"supported_agents": agents,
		"timestamp":        time.Now().Format(time.RFC3339),
	}
	data, _ := json.Marshal(payload)
	client.Publish(topic, 1, false, data)
}

// startHeartbeatLoop avvia una goroutine che pubblica heartbeat ogni 30s.
func startHeartbeatLoop(client mqtt.Client, nodeID string, agents []string) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	publishHeartbeat(client, nodeID, agents)
	for range ticker.C {
		publishHeartbeat(client, nodeID, agents)
	}
}
