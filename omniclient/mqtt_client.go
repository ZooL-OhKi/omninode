package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"strings"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// CommandPayload rappresenta un comando ricevuto dal broker MQTT.
type CommandPayload struct {
	TaskID  string `json:"task_id"`
	AgentID string `json:"agent_id"`
	Action  string `json:"action"`
	Ref     string `json:"ref,omitempty"`
	Subcmd  string `json:"subcmd,omitempty"`
}

// MQTTWorker gestisce la connessione MQTT e l'elaborazione dei comandi.
type MQTTWorker struct {
	Client mqtt.Client
	NodeID string
}

// NewTLSConfig crea una configurazione TLS per MQTT mTLS.
func NewTLSConfig(caCertPath, clientCertPath, clientKeyPath string) (*tls.Config, error) {
	cert, err := tls.LoadX509KeyPair(clientCertPath, clientKeyPath)
	if err != nil {
		return nil, err
	}
	caCert, err := os.ReadFile(caCertPath)
	if err != nil {
		return nil, err
	}
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)

	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      caCertPool,
	}, nil
}

// StartMQTTWorker avvia il worker MQTT connesso al broker mTLS.
func StartMQTTWorker(brokerURL, nodeID, caPath, certPath, keyPath string) (*MQTTWorker, error) {
	tlsConfig, err := NewTLSConfig(caPath, certPath, keyPath)
	if err != nil {
		return nil, err
	}

	opts := mqtt.NewClientOptions()
	opts.AddBroker(brokerURL)
	opts.SetClientID(fmt.Sprintf("omninode-worker-%s", nodeID))
	opts.SetTLSConfig(tlsConfig)
	opts.SetAutoReconnect(true)
	opts.SetConnectionLostHandler(func(c mqtt.Client, err error) {
		slog.Error("Connessione MQTT persa", "err", err)
	})
	opts.SetOnConnectHandler(func(c mqtt.Client) {
		slog.Info("Connesso al broker MQTT TLS", "node", nodeID)
		cmdTopic := fmt.Sprintf("omninode/nodes/%s/cmd/+", nodeID)
		approvalTopic := "omninode/approvals/in"
		if token := c.Subscribe(cmdTopic, 1, cmdHandler(nodeID)); token.Wait() && token.Error() != nil {
			slog.Error("Errore sottoscrizione comandi", "err", token.Error())
		}
		if token := c.Subscribe(approvalTopic, 1, approvalHandler(nodeID)); token.Wait() && token.Error() != nil {
			slog.Error("Errore sottoscrizione approvazioni", "err", token.Error())
		}
	})

	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		return nil, token.Error()
	}
	return &MQTTWorker{Client: client, NodeID: nodeID}, nil
}

// cmdHandler elabora i comandi MQTT in arrivo.
func cmdHandler(nodeID string) mqtt.MessageHandler {
	return func(client mqtt.Client, msg mqtt.Message) {
		topic := msg.Topic()
		parts := strings.Split(topic, "/")
		if len(parts) < 5 {
			return
		}
		taskID := parts[4]

		var cmd CommandPayload
		if err := json.Unmarshal(msg.Payload(), &cmd); err != nil {
			publishRes(client, nodeID, taskID, "error", "JSON non valido")
			return
		}

		slog.Info("Comando ricevuto", "task", taskID, "action", cmd.Action)

		switch cmd.Action {
		case "web_snapshot":
			sess, err := sessions.GetOrCreate(cmd.AgentID)
			if err != nil {
				publishRes(client, nodeID, taskID, "error", err.Error())
				return
			}
			out, err := SnapshotState(sess)
			if err != nil {
				publishRes(client, nodeID, taskID, "error", err.Error())
			} else {
				publishRes(client, nodeID, taskID, "success", out)
			}

		case "web_click":
			sess, err := sessions.GetOrCreate(cmd.AgentID)
			if err != nil {
				publishRes(client, nodeID, taskID, "error", err.Error())
				return
			}
			out, err := TrustedClick(sess, parseRef(cmd.Ref))
			if err != nil {
				publishRes(client, nodeID, taskID, "error", err.Error())
			} else {
				publishRes(client, nodeID, taskID, "success", out)
			}

		case "ops_terraform":
			HandleTerraform(client, nodeID, taskID, cmd.AgentID, cmd.Subcmd)

		default:
			publishRes(client, nodeID, taskID, "error", "Azione sconosciuta")
		}
	}
}

// approvalHandler elabora le approvazioni in arrivo.
func approvalHandler(nodeID string) mqtt.MessageHandler {
	return func(client mqtt.Client, msg mqtt.Message) {
		slog.Info("Approvazione ricevuta", "payload", string(msg.Payload()))
		HandleApproval(client, nodeID, msg.Payload())
	}
}

// parseRef converte un ref string in intero per TrustedClick.
func parseRef(s string) int {
	var ref int
	fmt.Sscanf(s, "%d", &ref)
	return ref
}

// publishRes pubblica un risultato sul topic MQTT.
func publishRes(client mqtt.Client, nodeID, taskID, status, output string) {
	res := map[string]string{"task_id": taskID, "status": status, "output": output}
	payload, _ := json.Marshal(res)
	client.Publish(fmt.Sprintf("omninode/nodes/%s/result/%s", nodeID, taskID), 1, false, payload)
}

// publishHeartbeat invia un heartbeat periodico.
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

// startHeartbeatLoop avvia il loop di heartbeat ogni 30 secondi.
func startHeartbeatLoop(client mqtt.Client, nodeID string, agents []string) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	publishHeartbeat(client, nodeID, agents)
	for range ticker.C {
		publishHeartbeat(client, nodeID, agents)
	}
}
