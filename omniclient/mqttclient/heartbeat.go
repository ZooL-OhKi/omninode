package mqttclient

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// HeartbeatPayload definisce il contratto dati inviato al Gateway FastAPI
type HeartbeatPayload struct {
	NodeID    string  `json:"node_id"`
	Status    string  `json:"status"`
	Load      float64 `json:"load"`
	Timestamp int64   `json:"timestamp"`
}

type HeartbeatService struct {
	client mqtt.Client
	nodeID string
	ticker *time.Ticker
	stopCh chan struct{}
}

// InitHeartbeat configura il client MQTT. I log sono forzati su stderr
// per preservare la validità dello stdout richiesto da MCP in modalità stdio.
func InitHeartbeat(brokerURL, nodeID string) (*HeartbeatService, error) {

	// PROTEZIONE MCP: Redirezione forzata su Stderr
	mqtt.ERROR = log.New(os.Stderr, "[MQTT ERR] ", log.LstdFlags)
	mqtt.CRITICAL = log.New(os.Stderr, "[MQTT CRIT] ", log.LstdFlags)
	mqtt.WARN = log.New(os.Stderr, "[MQTT WARN] ", log.LstdFlags)
	// mqtt.DEBUG = log.New(os.Stderr, "[MQTT DBG] ", log.LstdFlags) // Decommentare solo per debug

	opts := mqtt.NewClientOptions()
	opts.AddBroker(brokerURL)
	opts.SetClientID(fmt.Sprintf("omniworker-%s", nodeID))
	opts.SetKeepAlive(60 * time.Second)
	opts.SetPingTimeout(10 * time.Second)

	client := mqtt.NewClient(opts)
	token := client.Connect()
	token.Wait()

	if token.Error() != nil {
		return nil, token.Error()
	}

	return &HeartbeatService{
		client: client,
		nodeID: nodeID,
		stopCh: make(chan struct{}),
	}, nil
}

// Start avvia il worker asincrono che spara gli heartbeat
func (s *HeartbeatService) Start(interval time.Duration) {
	s.ticker = time.NewTicker(interval)
	topic := fmt.Sprintf("omninode/nodes/%s/heartbeat", s.nodeID)

	go func() {
		for {
			select {
			case <-s.ticker.C:
				payload := HeartbeatPayload{
					NodeID:    s.nodeID,
					Status:    "online",
					Load:      getSystemLoad(), // Da implementare metrica reale
					Timestamp: time.Now().Unix(),
				}

				data, err := json.Marshal(payload)
				if err != nil {
					fmt.Fprintf(os.Stderr, "[OmniClient] Errore marshal heartbeat: %v\n", err)
					continue
				}

				token := s.client.Publish(topic, 1, false, data)
				token.Wait()
				if token.Error() != nil {
					fmt.Fprintf(os.Stderr, "[OmniClient] Errore publish heartbeat: %v\n", token.Error())
				}

			case <-s.stopCh:
				s.ticker.Stop()
				return
			}
		}
	}()
}

// Stop termina il loop asincrono in modo pulito
func (s *HeartbeatService) Stop() {
	close(s.stopCh)
	s.client.Disconnect(250)
}

// getSystemLoad è un placeholder per la lettura del carico macchina reale
func getSystemLoad() float64 {
	// TODO: Utilizzare "github.com/shirou/gopsutil" in futuro per dati hardware reali
	return 1.25
}
