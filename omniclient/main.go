package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/ZooL-OhKi/omninode/omniclient/mqttclient"
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

		// Inizializzazione heartbeat MQTT
		hbService, err := mqttclient.InitHeartbeat("tcp://127.0.0.1:1883", "node-local")
		if err != nil {
			fmt.Fprintf(os.Stderr, "[OmniClient] Errore inizializzazione MQTT: %v\n", err)
			os.Exit(1)
		}
		defer hbService.Stop()

		hbService.Start(5 * time.Second)

		fmt.Fprintln(os.Stderr, "[OmniClient] Connected to MQTT broker. Sending heartbeat every 5 seconds...")

		// Mantieni il processo in esecuzione
		select {}
	}
}
