package main

import (
"log"
"os"
"os/signal"
"syscall"
"time"
)

func main() {
log.Println("[OmniClient] Avvio del nodo Go worker in corso...")

brokerURL := os.Getenv("OMNINODE_MQTT_BROKER")
if brokerURL == "" {
brokerURL = "tcp://127.0.0.1:1883"
}

clientID := os.Getenv("OMNINODE_NODE_ID")
if clientID == "" {
clientID = "omni-worker-go-1"
}

username := os.Getenv("OMNINODE_MQTT_USER")
password := os.Getenv("OMNINODE_MQTT_PASS")
caCertPath := os.Getenv("OMNINODE_MQTT_CA_PATH")

client, err := StartMQTTWorker(brokerURL, clientID, username, password, caCertPath)
if err != nil {
log.Fatalf("[OmniClient] Errore critico di connessione MQTT: %v", err)
}
defer client.Disconnect(250)

log.Printf("[OmniClient] Nodo %s connesso con successo al broker %s", clientID, brokerURL)

// Canale per gracefull shutdown
sigChan := make(chan os.Signal, 1)
signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

<-sigChan
log.Println("[OmniClient] Segnale di arresto ricevuto, chiusura in corso...")
time.Sleep(500 * time.Millisecond)
log.Println("[OmniClient] Spegnimento completato.")
}