package main

import (
	"log"
	"net/http"
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

func startOptionalUIServer() *http.Server {
	uiAddr := os.Getenv("UI_LISTEN_ADDR")
	if uiAddr == "" {
		return nil
	}
	gatewayURL := os.Getenv("GATEWAY_URL")
	if gatewayURL == "" {
		gatewayURL = "http://127.0.0.1:8000"
	}
	mcpSecret := os.Getenv("MCP_SECRET")

	var bridge *BridgeService
	workspaceRoot := os.Getenv("OMNINODE_WORKSPACE_ROOT")
	bridgeToken := os.Getenv("OMNINODE_BRIDGE_TOKEN")
	if workspaceRoot != "" && bridgeToken != "" {
		workspace := NewWorkspaceHandler(workspaceRoot)
		allowedOrigin := os.Getenv("OMNINODE_ALLOWED_ORIGIN")
		if allowedOrigin == "" {
			allowedOrigin = "http://" + uiAddr
		}
		var err error
		bridge, err = NewBridgeService(workspace, bridgeToken, allowedOrigin)
		if err != nil {
			log.Fatalf("[OmniClient] bridge non avviabile: %v", err)
		}
		log.Printf("[OmniClient] bridge locale attivo su /api/bridge/execute (workspace: %s)", workspaceRoot)
	}

	handler, err := NewUIHandler(gatewayURL, mcpSecret, bridge)
	if err != nil {
		log.Fatalf("[OmniClient] impossibile inizializzare UI server: %v", err)
	}

	srv := &http.Server{
		Addr:    uiAddr,
		Handler: handler,
	}

	go func() {
		log.Printf("[OmniClient] Web UI / PWA attiva su http://%s (Gateway: %s)", uiAddr, gatewayURL)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[OmniClient] errore UI server: %v", err)
		}
	}()
	return srv
}

func main() {
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)

	if os.Getenv("UI_ONLY") == "1" {
		if os.Getenv("UI_LISTEN_ADDR") == "" {
			_ = os.Setenv("UI_LISTEN_ADDR", "127.0.0.1:8080")
		}
		startOptionalUIServer()
		<-signals
		log.Println("[OmniClient] arresto UI standalone")
		return
	}

	log.Println("[OmniClient] avvio worker OmniNode")
	startOptionalUIServer()

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

	<-signals

	log.Println("[OmniClient] arresto richiesto")
	close(stop)
	log.Println("[OmniClient] worker arrestato")
}
