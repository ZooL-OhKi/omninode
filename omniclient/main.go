package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"
)

func requiredEnv(name string) string {
	value := os.Getenv(name)
	if value == "" {
		log.Fatalf("[OmniClient] variabile obbligatoria mancante: %s", name)
	}
	return value
}

func main() {
	log.Println("[OmniClient] avvio worker OmniNode")

	brokerURL := requiredEnv("OMNINODE_MQTT_BROKER")
	nodeID := requiredEnv("OMNINODE_NODE_ID")
	agentID := requiredEnv("OMNINODE_AGENT_ID")
	username := requiredEnv("OMNINODE_MQTT_USER")
	password := requiredEnv("OMNINODE_MQTT_PASS")
	caPath := requiredEnv("OMNINODE_MQTT_CA_PATH")
	certPath := requiredEnv("OMNINODE_MQTT_CERT_PATH")
	keyPath := requiredEnv("OMNINODE_MQTT_KEY_PATH")
	serverName := os.Getenv("OMNINODE_MQTT_SERVER_NAME")
	workspaceRoot := requiredEnv("OMNINODE_WORKSPACE_ROOT")

	client, err := StartMQTTWorker(WorkerConfig{
		BrokerURL:     brokerURL,
		ClientID:      nodeID,
		Username:      username,
		Password:      password,
		CACertPath:    caPath,
		CertPath:      certPath,
		KeyPath:       keyPath,
		ServerName:    serverName,
		NodeID:        nodeID,
		WorkspaceRoot: workspaceRoot,
	})
	if err != nil {
		log.Fatalf("[OmniClient] connessione MQTT non riuscita: %v", err)
	}
	defer client.Disconnect(250)

	stop := make(chan struct{})
	go startHeartbeatLoop(client, nodeID, []string{agentID}, stop)

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	<-signals

	log.Println("[OmniClient] arresto richiesto")
	close(stop)
	log.Println("[OmniClient] worker arrestato")
}
