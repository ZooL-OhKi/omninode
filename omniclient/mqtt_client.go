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
func NewMQTTClient(brokerURL, clientID, username, password string, caCertPath string) mqtt.Client {
opts := mqtt.NewClientOptions()
opts.AddBroker(brokerURL)
opts.SetClientID(clientID)
opts.SetUsername(username)
opts.SetPassword(password)

opts.SetKeepAlive(30 * time.Second)
opts.SetPingTimeout(10 * time.Second)
opts.SetCleanSession(false)
opts.SetAutoReconnect(true)

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
InsecureSkipVerify: false,
}
opts.SetTLSConfig(tlsConfig)
}
}

return mqtt.NewClient(opts)
}

// StartMQTTWorker ripristina la firma compatibile con main.go
func StartMQTTWorker(brokerURL, clientID, username, password, caCertPath string) (mqtt.Client, error) {
client := NewMQTTClient(brokerURL, clientID, username, password, caCertPath)
if token := client.Connect(); token.Wait() && token.Error() != nil {
return nil, token.Error()
}
return client, nil
}

// publishRes ripristina la firma compatibile con ops_terraform.go
func publishRes(client mqtt.Client, nodeID, taskID, status, result string) error {
topic := "omninode/v1/nodes/" + nodeID + "/responses"
payload := []byte(`{"task_id":"` + taskID + `","status":"` + status + `","result":"` + result + `"}`)
token := client.Publish(topic, 1, false, payload)
token.Wait()
return token.Error()
}