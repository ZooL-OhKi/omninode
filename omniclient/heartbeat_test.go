package main

import (
	"encoding/json"
	"testing"
)

func TestHeartbeatTopicUsesV1(t *testing.T) {
	if got := heartbeatTopic("worker-1"); got != "omninode/v1/nodes/worker-1/heartbeat" {
		t.Fatalf("unexpected heartbeat topic: %s", got)
	}
}

func TestHeartbeatPayloadIsStructuredJSON(t *testing.T) {
	payload, err := heartbeatPayload("worker-1", []string{"workspace.write"})
	if err != nil {
		t.Fatal(err)
	}
	var decoded map[string]any
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["node_id"] != "worker-1" || decoded["status"] != "online" {
		t.Fatalf("unexpected heartbeat payload: %s", payload)
	}
}
