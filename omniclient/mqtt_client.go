package main

import (
"crypto/tls"
"crypto/x509"
"log"
"os"
"time"

mqtt "github.com/eclipse/paho.mqtt.golang"
)

// NewMQTTClient configura il client Paho MQTT supportando sia TLS (tcp://) che WebSocket Secure (wss://)
// con keep-alive a 30 secondi e gestione della riconnessione resiliente.
func NewMQTTClient(brokerURL, clientID, username, password string, caCertPath string) mqtt.Client {
opts := mqtt.NewClientOptions()
opts.AddBroker(brokerURL)
opts.SetClientID(clientID)
opts.SetUsername(username)
opts.SetPassword(password)

// Requisito: Keep-alive a 30 secondi per prevenire timeout WSS (es. Cloudflare)
opts.SetKeepAlive(30 * time.Second)
opts.SetPingTimeout(10 * time.Second)
opts.SetCleanSession(false)
opts.SetAutoReconnect(true)

// Backoff esponenziale e jitter per il reconnect
opts.SetConnectRetry(true)
opts.SetConnectRetryInterval(5 * time.Second)
opts.SetMaxReconnectInterval(60 * time.Second)

if caCertPath != "" {
certPool := x509.NewCertPool()
caCert, err := os.ReadFile(caCertPath)
if err != nil {
log.Printf("[MQTT] Attenzione: Impossibile leggere il certificato CA da %s: %v", caCertPath, err)
} else {
certPool.AppendCertsFromPEM(caCert)
tlsConfig := &tls.Config{
RootCAs:            certPool,
InsecureSkipVerify: false, // Mai disabilitare in produzione
}
opts.SetTLSConfig(tlsConfig)
}
}

client := mqtt.NewClient(opts)
return client
}

// StartMQTTWorker avvia il worker MQTT per la ricezione dei task e l'invio delle risposte (Task A / Swarm Fabric v5.0)
func StartMQTTWorker(client mqtt.Client, nodeID string, taskHandler func(topic string, payload []byte)) error {
if token := client.Connect(); token.Wait() && token.Error() != nil {
return token.Error()
}

// Sottoscrizione al topic v1 / legacy dei task per questo nodo
topic := "omninode/v1/nodes/" + nodeID + "/tasks"
token := client.Subscribe(topic, 1, func(client mqtt.Client, msg mqtt.Message) {
taskHandler(msg.Topic(), msg.Payload())
})
token.Wait()
return token.Error()
}

// publishRes pubblica la risposta o l'heartbeat del nodo sul topic canonico
func publishRes(client mqtt.Client, nodeID string, subpath string, payload []byte) error {
topic := "omninode/v1/nodes/" + nodeID + "/" + subpath
token := client.Publish(topic, 1, false, payload)
token.Wait()
return token.Error()
}