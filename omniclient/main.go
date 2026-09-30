package main

import (
	"log/slog"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	slog.Info("Avvio Omninode Worker...")

	// Inizializza database SQLite per HITL
	if err := InitDB("file:omninode.db?mode=rwc"); err != nil {
		slog.Error("Impossibile inizializzare database", "err", err)
		os.Exit(1)
	}

	// Inizializza browser CDP
	if err := InitWebAgent(); err != nil {
		slog.Error("Impossibile avviare WebAgent", "err", err)
		os.Exit(1)
	}

	// Avvia WebSocket locale (opzionale, per debug)
	go func() {
		if err := StartWSServer(8080); err != nil {
			slog.Error("Errore WS Server", "err", err)
		}
	}()

	// Configura parametri MQTT da variabili d'ambiente
	nodeID := getEnv("OMNI_NODE_ID", "ryzen")
	brokerURL := getEnv("OMNI_MQTT_BROKER", "tls://oracle-b.plini.net:8883")
	caPath := getEnv("OMNI_MQTT_CA", "certs/ca.crt")
	certPath := getEnv("OMNI_MQTT_CERT", "certs/client.crt")
	keyPath := getEnv("OMNI_MQTT_KEY", "certs/client.key")

	// Avvia worker MQTT
	worker, err := StartMQTTWorker(brokerURL, nodeID, caPath, certPath, keyPath)
	if err != nil {
		slog.Error("Errore connessione MQTT", "err", err)
		os.Exit(1)
	}
	defer worker.Client.Disconnect(250)

	// Avvia heartbeat loop
	go startHeartbeatLoop(worker.Client, nodeID, []string{"agent_1", "devops_bot"})

	// Attendi segnale di terminazione
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	slog.Info("Spegnimento Omninode Worker...")
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
