package main

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestONAPValidationSmoke(t *testing.T) {
	for _, action := range []AgentAction{
		{Action: "navigate"},
		{Action: "press_key"},
		{Action: "fill", Text: "test"},
		{Action: "unknown-action"},
	} {
		t.Run(action.Action, func(t *testing.T) {
			result := executeAgentAction(nil, action)
			if result.Status != "error" || result.Message == "" {
				t.Fatalf("expected validation error, got %+v", result)
			}
		})
	}
}

func TestONAPPlanJSONSmoke(t *testing.T) {
	var plan ActionPlan
	if err := json.Unmarshal([]byte(`{"plan_id":"smoke-001","session_id":"smoke","actions":[{"action":"observe"}]}`), &plan); err != nil {
		t.Fatal(err)
	}
	if plan.PlanID != "smoke-001" || plan.SessionID != "smoke" || len(plan.Actions) != 1 || plan.Actions[0].Action != "observe" {
		t.Fatalf("unexpected plan: %+v", plan)
	}
}

func TestONAPSecretResolutionSmoke(t *testing.T) {
	t.Setenv("OMNINODE_SECRET_SMOKE", "synthetic-test-value")
	for _, ref := range []string{"vault:smoke", "env:OMNINODE_SECRET_SMOKE"} {
		value, err := resolveAgentValue("ignored", ref)
		if err != nil || value != "synthetic-test-value" {
			t.Fatalf("secret resolution failed for %s", ref)
		}
	}
	value, err := resolveAgentValue("plain text", "")
	if err != nil || value != "plain text" {
		t.Fatal("plain text resolution failed")
	}
	for _, ref := range []string{"", "env:", "vault:", "unsupported:smoke"} {
		if _, err := ResolveSecret(ref); err == nil {
			t.Fatalf("expected error for %q", ref)
		}
	}
}

func TestONAPScreenshotNilSession(t *testing.T) {
	if _, err := captureBrowserScreenshot(nil); err == nil {
		t.Fatal("expected nil session error")
	}
}

func TestONAPTopics(t *testing.T) {
	base := "omninode/v1/nodes/smoke/agent/"
	for _, topic := range []string{agentContextTopic("smoke"), agentActionTopic("smoke"), agentObservationTopic("smoke")} {
		if !strings.HasPrefix(topic, base) {
			t.Fatalf("unexpected topic: %s", topic)
		}
	}
}
