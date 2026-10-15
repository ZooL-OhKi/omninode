package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

func heartbeatTopic(nodeID string) string {
	return fmt.Sprintf("omninode/v1/nodes/%s/heartbeat", nodeID)
}

func heartbeatPayload(nodeID string, agents []string) ([]byte, error) {
	return json.Marshal(map[string]any{
		"node_id":          nodeID,
		"status":           "online",
		"supported_agents": agents,
		"timestamp":        time.Now().UTC().Format(time.RFC3339),
	})
}

func publishHeartbeat(client mqtt.Client, nodeID string, agents []string) error {
	payload, err := heartbeatPayload(nodeID, agents)
	if err != nil {
		return err
	}
	token := client.Publish(heartbeatTopic(nodeID), 1, false, payload)
	if !token.Wait() || token.Error() != nil {
		return token.Error()
	}
	return nil
}

func logHeartbeatError(err error) {
	log.Printf("[MQTT] heartbeat non pubblicato: %v", err)
}

func startHeartbeatLoop(client mqtt.Client, nodeID string, agents []string, stop <-chan struct{}) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	if err := publishHeartbeat(client, nodeID, agents); err != nil {
		logHeartbeatError(err)
	}
	for {
		select {
		case <-stop:
			return
		case <-ticker.C:
			if err := publishHeartbeat(client, nodeID, agents); err != nil {
				logHeartbeatError(err)
			}
		}
	}
}
