package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

const (
	agentContextTopicFormat     = "omninode/v1/nodes/%s/agent/context"
	agentActionTopicFormat      = "omninode/v1/nodes/%s/agent/actions"
	agentObservationTopicFormat = "omninode/v1/nodes/%s/agent/observations"
)

type AgentContext struct {
	SessionID      string            `json:"session_id"`
	Source         string            `json:"source"`
	URL            string            `json:"url,omitempty"`
	Title          string            `json:"title,omitempty"`
	Snapshot       string            `json:"snapshot,omitempty"`
	ScreenshotPath string            `json:"screenshot_path,omitempty"`
	ActiveWindow   string            `json:"active_window,omitempty"`
	Cursor         *CursorPosition   `json:"cursor,omitempty"`
	Error          string            `json:"error,omitempty"`
	Metadata       map[string]string `json:"metadata,omitempty"`
}

type CursorPosition struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type AgentAction struct {
	Action     string `json:"action"`
	Ref        int    `json:"ref,omitempty"`
	Selector   string `json:"selector,omitempty"`
	Text       string `json:"text,omitempty"`
	URL        string `json:"url,omitempty"`
	Key        string `json:"key,omitempty"`
	SecretRef  string `json:"secret_ref,omitempty"`
	TimeoutMS  int    `json:"timeout_ms,omitempty"`
	Screenshot bool   `json:"screenshot,omitempty"`
	CaptureDOM bool   `json:"capture_dom,omitempty"`
}

type ActionPlan struct {
	PlanID    string        `json:"plan_id"`
	SessionID string        `json:"session_id"`
	Actions   []AgentAction `json:"actions"`
}

type ActionResult struct {
	Action         string `json:"action"`
	Status         string `json:"status"`
	Message        string `json:"message,omitempty"`
	URL            string `json:"url,omitempty"`
	Title          string `json:"title,omitempty"`
	Snapshot       string `json:"snapshot,omitempty"`
	ScreenshotPath string `json:"screenshot_path,omitempty"`
}

type Observation struct {
	PlanID    string         `json:"plan_id"`
	SessionID string         `json:"session_id"`
	Status    string         `json:"status"`
	Results   []ActionResult `json:"results,omitempty"`
	Error     string         `json:"error,omitempty"`
	Timestamp string         `json:"timestamp"`
}

func agentContextTopic(nodeID string) string {
	return fmt.Sprintf(agentContextTopicFormat, nodeID)
}

func agentActionTopic(nodeID string) string {
	return fmt.Sprintf(agentActionTopicFormat, nodeID)
}

func agentObservationTopic(nodeID string) string {
	return fmt.Sprintf(agentObservationTopicFormat, nodeID)
}

func handleAgentActionPlan(client mqtt.Client, nodeID string, payload []byte) {
	var plan ActionPlan
	if err := json.Unmarshal(payload, &plan); err != nil {
		publishAgentObservation(client, nodeID, Observation{
			Status:    "error",
			Error:     fmt.Sprintf("piano azioni non valido: %v", err),
			Timestamp: time.Now().UTC().Format(time.RFC3339),
		})
		return
	}

	if strings.TrimSpace(plan.PlanID) == "" {
		plan.PlanID = fmt.Sprintf("plan_%d", time.Now().UnixNano())
	}

	if strings.TrimSpace(plan.SessionID) == "" {
		publishAgentObservation(client, nodeID, Observation{
			PlanID:    plan.PlanID,
			Status:    "error",
			Error:     "session_id obbligatorio",
			Timestamp: time.Now().UTC().Format(time.RFC3339),
		})
		return
	}

	session, err := sessions.GetOrCreate(plan.SessionID)
	if err != nil {
		publishAgentObservation(client, nodeID, Observation{
			PlanID:    plan.PlanID,
			SessionID: plan.SessionID,
			Status:    "error",
			Error:     err.Error(),
			Timestamp: time.Now().UTC().Format(time.RFC3339),
		})
		return
	}

	observation := Observation{
		PlanID:    plan.PlanID,
		SessionID: plan.SessionID,
		Status:    "completed",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}

	for _, action := range plan.Actions {
		result := executeAgentAction(session, action)
		observation.Results = append(observation.Results, result)

		if result.Status != "completed" {
			observation.Status = "error"
			observation.Error = result.Message
			break
		}
	}

	publishAgentObservation(client, nodeID, observation)
}

func executeAgentAction(session *WebSession, action AgentAction) ActionResult {
	result := ActionResult{
		Action: action.Action,
		Status: "completed",
	}

	switch strings.ToLower(strings.TrimSpace(action.Action)) {
	case "navigate":
		if strings.TrimSpace(action.URL) == "" {
			result.Status = "error"
			result.Message = "url obbligatorio per navigate"
			return result
		}

		if _, err := session.page.Goto(action.URL); err != nil {
			result.Status = "error"
			result.Message = fmt.Sprintf("navigazione non riuscita: %v", err)
			return result
		}

		result.URL = session.page.URL()
		result.Title, _ = session.page.Title()

	case "click":
		message, err := TrustedClick(session, action.Ref)
		if err != nil {
			result.Status = "error"
			result.Message = err.Error()
			return result
		}
		result.Message = message

	case "fill":
		value, err := resolveAgentValue(action.Text, action.SecretRef)
		if err != nil {
			result.Status = "error"
			result.Message = err.Error()
			return result
		}

		if strings.TrimSpace(action.Selector) == "" {
			result.Status = "error"
			result.Message = "selector obbligatorio per fill"
			return result
		}

		if err := session.page.Locator(action.Selector).Fill(value); err != nil {
			result.Status = "error"
			result.Message = fmt.Sprintf("compilamento %q non riuscito: %v", action.Selector, err)
			return result
		}

	case "press_key":
		if strings.TrimSpace(action.Key) == "" {
			result.Status = "error"
			result.Message = "key obbligatorio per press_key"
			return result
		}

		if err := session.page.Keyboard().Press(action.Key); err != nil {
			result.Status = "error"
			result.Message = fmt.Sprintf("pressione tasto non riuscita: %v", err)
			return result
		}

	case "type_text":
		value, err := resolveAgentValue(action.Text, action.SecretRef)
		if err != nil {
			result.Status = "error"
			result.Message = err.Error()
			return result
		}

		if err := session.page.Keyboard().Type(value); err != nil {
			result.Status = "error"
			result.Message = fmt.Sprintf("digitazione non riuscita: %v", err)
			return result
		}

	case "wait":
		delay := time.Duration(action.TimeoutMS) * time.Millisecond
		if delay <= 0 {
			delay = time.Second
		}
		time.Sleep(delay)

	case "observe", "snapshot":
		snapshot, err := SnapshotState(session)
		if err != nil {
			result.Status = "error"
			result.Message = err.Error()
			return result
		}

		result.Snapshot = snapshot
		result.URL = session.page.URL()
		result.Title, _ = session.page.Title()

	case "screenshot":
		path, err := captureBrowserScreenshot(session)
		if err != nil {
			result.Status = "error"
			result.Message = err.Error()
			return result
		}

		result.ScreenshotPath = path

	default:
		result.Status = "error"
		result.Message = fmt.Sprintf("azione non supportata: %q", action.Action)
	}

	return result
}

func captureBrowserScreenshot(session *WebSession) (string, error) {
	if session == nil {
		return "", errors.New("sessione browser nulla")
	}

	workspaceRoot := os.Getenv("OMNINODE_WORKSPACE_ROOT")
	if strings.TrimSpace(workspaceRoot) == "" {
		workspaceRoot = "."
	}

	capturesDirectory := filepath.Join(workspaceRoot, "captures")
	if err := os.MkdirAll(capturesDirectory, 0o750); err != nil {
		return "", fmt.Errorf("creazione directory screenshot: %w", err)
	}

	path := filepath.Join(capturesDirectory, fmt.Sprintf("browser_%d.png", time.Now().UnixNano()))
	image, err := session.page.Screenshot()
	if err != nil {
		return "", fmt.Errorf("cattura screenshot: %w", err)
	}

	if err := os.WriteFile(path, image, 0o600); err != nil {
		return "", fmt.Errorf("salvataggio screenshot: %w", err)
	}

	return path, nil
}

func publishAgentObservation(client mqtt.Client, nodeID string, observation Observation) {
	payload, err := json.Marshal(observation)
	if err != nil {
		log.Printf("[ONAP] serializzazione osservazione non riuscita: %v", err)
		return
	}

	token := client.Publish(agentObservationTopic(nodeID), 1, false, payload)
	if !token.WaitTimeout(10*time.Second) || token.Error() != nil {
		log.Printf("[ONAP] pubblicazione osservazione non riuscita: %v", token.Error())
	}
}

func subscribeAgentTopics(client mqtt.Client, nodeID string) {
	token := client.Subscribe(agentActionTopic(nodeID), 1, func(_ mqtt.Client, message mqtt.Message) {
		handleAgentActionPlan(client, nodeID, message.Payload())
	})

	if !token.WaitTimeout(10*time.Second) || token.Error() != nil {
		log.Printf("[ONAP] sottoscrizione azioni agente non riuscita: %v", token.Error())
		return
	}

	log.Printf("[ONAP] sottoscritto a %s", agentActionTopic(nodeID))
}
