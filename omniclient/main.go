package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

func main() {
	mcpFlag := flag.Bool("mcp-stdio", false, "Run as MCP stdio server")
	flag.Parse()

	if *mcpFlag {
		fmt.Fprintln(os.Stderr, "[OmniClient] Starting MCP stdio worker...")
		select {}
	} else {
		fmt.Println("[OmniClient] Running in standard background worker mode...")

		// Configurazione del client MQTT verso il broker locale
		opts := mqtt.NewClientOptions()
		opts.AddBroker("tcp://127.0.0.1:1883")
		opts.SetClientID("omniclient-node-local")

		client := mqtt.NewClient(opts)
		if token := client.Connect(); token.Wait() && token.Error() != nil {
			fmt.Printf("[OmniClient] Errore connessione MQTT: %v\n", token.Error())
			return
		}
		defer client.Disconnect(250)

		fmt.Println("[OmniClient] Connesso al broker MQTT. Invio heartbeat in corso...")

		// Loop di invio heartbeat ogni 5 secondi
		for {
			payload := `{"status": "online", "node": "node-local", "timestamp": "` + time.Now().Format(time.RFC3339) + `"}`
			token := client.Publish("omninode/nodes/node-local/heartbeat", 0, false, payload)
			token.Wait()

			time.Sleep(5 * time.Second)
		}
	}
}