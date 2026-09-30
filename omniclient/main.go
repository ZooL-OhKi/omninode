package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/ZooL-OhKi/omniclient/mqttclient"
)

func main() {
	mcpFlag := flag.Bool("mcp-stdio", false, "Run as MCP stdio server")
	flag.Parse()

	if *mcpFlag {
		// Modalità MCP stdio: avvia il server MCP per agenti IA
		fmt.Fprintln(os.Stderr, "[OmniClient] Starting MCP stdio server...")
		if err := NewOmninodeServer().StartMCPStdio(); err != nil {
			fmt.Fprintf(os.Stderr, "[OmniClient] MCP stdio error: %v\n", err)
			os.Exit(1)
		}
	} else {
		// Modalità worker headless con heartbeat MQTT
		fmt.Fprintln(os.Stderr, "[OmniClient] Starting background worker with MQTT heartbeat...")

		// Estrai Node ID da variabile d'ambiente con fallback
		nodeID := os.Getenv("OMNINODE_NODE_ID")
		if nodeID == "" {
			nodeID = "node-local"
		}

		// Inizializzazione heartbeat MQTT
		hbService, err := mqttclient.InitHeartbeat("tcp://127.0.0.1:1883", nodeID)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[OmniClient] Errore inizializzazione MQTT: %v\n", err)
			os.Exit(1)
		}

		hbService.Start(5 * time.Second)

		fmt.Fprintln(os.Stderr, "[OmniClient] Connected to MQTT broker. Sending heartbeat every 5 seconds...")

		// Avvia server WebSocket in background
		StartWSServer(8080)

		// Graceful shutdown: ascolta SIGINT (Ctrl+C) e SIGTERM
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

		go func() {
			<-sigCh
			hbService.Stop()
			fmt.Fprintf(os.Stderr, "[OmniClient] Graceful shutdown completato\n")
			os.Exit(0)
		}()

		// Mantieni il processo in esecuzione
		select {}
	}
}