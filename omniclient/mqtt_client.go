package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"os"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"time"
)

type WorkerConfig struct {
	BrokerURL     string
	ClientID      string
	Username      string
	Password      string
	CACertPath    string
	CertPath      string
	KeyPath       string
	ServerName    string
	NodeID        string
	WorkspaceRoot string
}

type TaskEnvelope struct {
	TaskID      string          `json:"task_id"`
	TaskType    string          `json:"task_type"`
	Payload     json.RawMessage `json:"payload"`
	SubmittedAt int64           `json:"submitted_at"`
}

type TaskResponse struct {
	TaskID string          `json:"task_id"`
	Status string          `json:"status"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  string          `json:"error,omitempty"`
}

type ControlMessage struct {
	Type      string `json:"type"`
	TaskID    string `json:"task_id"`
	Approved  bool   `json:"approved"`
}

type ControlAcknowledgement struct {
	Type         string `json:"type"`
	TaskID       string `json:"task_id"`
	Acknowledged bool   `json:"acknowledged"`
}

func taskTopic(nodeID string) string {
	return fmt.Sprintf("omninode/v1/nodes/%s/tasks", nodeID)
}

func responseTopic(nodeID string) string {
	return fmt.Sprintf("omninode/v1/nodes/%s/responses", nodeID)
}

func controlTopic(nodeID string) string {
	return fmt.Sprintf("omninode/v1/nodes/%s/control", nodeID)
}

func controlAckTopic(nodeID string) string {
	return fmt.Sprintf("omninode/v1/nodes/%s/control/ack", nodeID)
}

func buildTLSConfig(caPath, certPath, keyPath, serverName string) (*tls.Config, error) {
	if caPath == "" || certPath == "" || keyPath == "" {
		return nil, errors.New("mTLS richiede CA, certificato client e chiave client")
	}

	caPEM, err := os.ReadFile(caPath)
	if err != nil {
		return nil, fmt.Errorf("lettura CA %q non riuscita: %w", caPath, err)
	}
	caPool := x509.NewCertPool()
	if !caPool.AppendCertsFromPEM(caPEM) {
		return nil, fmt.Errorf("CA %q non valida o non leggibile come PEM", caPath)
	}

	clientCert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		return nil, fmt.Errorf("caricamento certificato/chiave client non riuscito: %w", err)
	}

	return &tls.Config{
		Certificates:       []tls.Certificate{clientCert},
		RootCAs:            caPool,
		ServerName:         serverName,
		InsecureSkipVerify: false,
		MinVersion:         tls.VersionTLS13,
		MaxVersion:         tls.VersionTLS13,
	}, nil
}

func NewMQTTClient(config WorkerConfig) (mqtt.Client, error) {
	tlsConfig, err := buildTLSConfig(config.CACertPath, config.CertPath, config.KeyPath, config.ServerName)
	if err != nil {
		return nil, err
	}

	handler := NewWorkspaceHandler(config.WorkspaceRoot)
	opts := mqtt.NewClientOptions()
	opts.AddBroker(config.BrokerURL)
	opts.SetClientID(config.ClientID)
	opts.SetUsername(config.Username)
	opts.SetPassword(config.Password)
	opts.SetTLSConfig(tlsConfig)
	opts.SetCleanSession(false)
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)
	opts.SetMaxReconnectInterval(60 * time.Second)
	opts.SetOnConnectHandler(func(client mqtt.Client) {
		for topic, handler := range map[string]mqtt.MessageHandler{
			taskTopic(config.NodeID): func(_ mqtt.Client, message mqtt.Message) {
				handleTask(client, config.NodeID, message.Payload(), handler)
			},
			controlTopic(config.NodeID): func(_ mqtt.Client, message mqtt.Message) {
				handleControl(client, config.NodeID, message.Payload())
			},
		} {
			token := client.Subscribe(topic, 1, handler)
			if !token.Wait() || token.Error() != nil {
				log.Printf("[MQTT] sottoscrizione a %s non riuscita: %v", topic, token.Error())
				continue
			}
			log.Printf("[MQTT] sottoscritto a %s", topic)
		}
	})

	return mqtt.NewClient(opts), nil
}

func handleTask(client mqtt.Client, nodeID string, payload []byte, handler *WorkspaceHandler) {
	var envelope TaskEnvelope
	if err := json.Unmarshal(payload, &envelope); err != nil || envelope.TaskID == "" {
		log.Printf("[MQTT] task non valido scartato: %v", err)
		return
	}

	result, err := handler.Execute(envelope)
	response := TaskResponse{TaskID: envelope.TaskID, Status: "completed"}
	if err != nil {
		response.Status = "error"
		response.Error = err.Error()
	} else {
		response.Result = result
	}

	encoded, err := json.Marshal(response)
	if err != nil {
		log.Printf("[MQTT] serializzazione risposta non riuscita: %v", err)
		return
	}
	token := client.Publish(responseTopic(nodeID), 1, false, encoded)
	if !token.Wait() || token.Error() != nil {
		log.Printf("[MQTT] pubblicazione risposta non riuscita: %v", token.Error())
	}
}

func handleControl(client mqtt.Client, nodeID string, payload []byte) {
	var message ControlMessage
	if err := json.Unmarshal(payload, &message); err != nil || message.TaskID == "" {
		log.Printf("[MQTT] messaggio di controllo non valido scartato: %v", err)
		return
	}

	ack := ControlAcknowledgement{
		Type:         message.Type,
		TaskID:       message.TaskID,
		Acknowledged: true,
	}
	encoded, err := json.Marshal(ack)
	if err != nil {
		log.Printf("[MQTT] serializzazione ack non riuscita: %v", err)
		return
	}
	token := client.Publish(controlAckTopic(nodeID), 1, false, encoded)
	if !token.Wait() || token.Error() != nil {
		log.Printf("[MQTT] pubblicazione ack non riuscita: %v", token.Error())
	}
}

func publishRes(client mqtt.Client, nodeID, taskID, status, result string) error {
	resultPayload := json.RawMessage(result)
	if !json.Valid(resultPayload) {
		encodedResult, err := json.Marshal(result)
		if err != nil {
			return err
		}
		resultPayload = encodedResult
	}

	payload, err := json.Marshal(TaskResponse{
		TaskID: taskID,
		Status: status,
		Result: resultPayload,
	})
	if err != nil {
		return err
	}

	token := client.Publish(responseTopic(nodeID), 1, false, payload)
	if !token.Wait() || token.Error() != nil {
		return token.Error()
	}
	return nil
}

func StartMQTTWorker(config WorkerConfig) (mqtt.Client, error) {
	client, err := NewMQTTClient(config)
	if err != nil {
		return nil, err
	}
	token := client.Connect()
if !token.WaitTimeout(20 * time.Second) {
    return nil, fmt.Errorf("timeout connessione MQTT a %s dopo 20s", config.BrokerURL)
}
if err := token.Error(); err != nil {
    return nil, fmt.Errorf("connessione MQTT non riuscita: %w", err)
}
	return client, nil
}
