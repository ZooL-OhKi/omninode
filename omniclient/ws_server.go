package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

// Configurazione (variabili d'ambiente):
//   OMNI_WS_TOKEN    obbligatorio, almeno 32 caratteri
//   OMNI_WS_ORIGINS  obbligatorio, elenco separato da virgole, es. "http://127.0.0.1:8080"
// Se manca qualcosa il server NON parte (fail closed).

const (
	authTimeout  = 5 * time.Second
	idleTimeout  = 90 * time.Second
	writeTimeout = 10 * time.Second
	maxMsgBytes  = 64 << 10
)

var (
	wsToken        string
	allowedOrigins = map[string]bool{}
)

func configureWS() error {
	wsToken = os.Getenv("OMNI_WS_TOKEN")
	if len(wsToken) < 32 {
		return fmt.Errorf("OMNI_WS_TOKEN mancante o troppo corto (minimo 32 caratteri)")
	}
	raw := strings.TrimSpace(os.Getenv("OMNI_WS_ORIGINS"))
	if raw == "" {
		return fmt.Errorf("OMNI_WS_ORIGINS mancante")
	}
	for _, o := range strings.Split(raw, ",") {
		if n := normalizeOrigin(o); n != "" {
			allowedOrigins[n] = true
		}
	}
	if len(allowedOrigins) == 0 {
		return fmt.Errorf("OMNI_WS_ORIGINS non contiene origin validi")
	}
	return nil
}

// normalizeOrigin restituisce "schema://host[:porta]" in minuscolo, oppure "".
func normalizeOrigin(o string) string {
	u, err := url.Parse(strings.TrimSpace(o))
	if err != nil || u.Scheme == "" || u.Host == "" {
		return ""
	}
	return strings.ToLower(u.Scheme + "://" + u.Host)
}

// checkOrigin: l'header Origin e' OBBLIGATORIO e deve essere nella allowlist.
func checkOrigin(r *http.Request) bool {
	origin := normalizeOrigin(r.Header.Get("Origin"))
	return origin != "" && allowedOrigins[origin]
}

// hostIsLoopback difende dal DNS rebinding: l'header Host deve essere locale.
func hostIsLoopback(r *http.Request) bool {
	host, _, err := net.SplitHostPort(r.Host)
	if err != nil {
		host = r.Host
	}
	return host == "127.0.0.1" || host == "localhost" || host == "[::1]" || host == "::1"
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  4096,
	WriteBufferSize: 4096,
	CheckOrigin:     checkOrigin,
}

// WSMessage: nessun campo "command". L'esecuzione di shell e' stata rimossa.
type WSMessage struct {
	Action  string `json:"action"`
	AgentID string `json:"agent_id,omitempty"`
	Token   string `json:"token,omitempty"`
	Ref     int    `json:"ref,omitempty"`
}

type WSResponse struct {
	Status string `json:"status"`
	Output string `json:"output"`
	Error  string `json:"error,omitempty"`
}

func wsOK(out string) WSResponse { return WSResponse{Status: "success", Output: out} }
func wsFail(err error) WSResponse {
	return WSResponse{Status: "error", Error: err.Error()}
}

func writeJSON(c *websocket.Conn, resp WSResponse) error {
	b, err := json.Marshal(resp)
	if err != nil {
		return err
	}
	_ = c.SetWriteDeadline(time.Now().Add(writeTimeout))
	return c.WriteMessage(websocket.TextMessage, b)
}

func closeWithPolicy(c *websocket.Conn, reason string) {
	_ = c.WriteControl(websocket.CloseMessage,
		websocket.FormatCloseMessage(websocket.ClosePolicyViolation, reason),
		time.Now().Add(time.Second))
}

// dispatchWS esegue le uniche azioni consentite. Nessuna shell.
func dispatchWS(req WSMessage) WSResponse {
	switch req.Action {
	case "ping":
		return wsOK("pong")

	case "web_snapshot":
		sess, err := sessions.GetOrCreate(req.AgentID)
		if err != nil {
			return wsFail(err)
		}
		out, err := SnapshotState(sess)
		if err != nil {
			return wsFail(err)
		}
		return wsOK(out)

	case "web_click":
		sess, err := sessions.GetOrCreate(req.AgentID)
		if err != nil {
			return wsFail(err)
		}
		out, err := TrustedClick(sess, req.Ref)
		if err != nil {
			return wsFail(err)
		}
		return wsOK(out)

	default:
		return wsFail(fmt.Errorf("azione non supportata: %q", req.Action))
	}
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	if !hostIsLoopback(r) {
		http.Error(w, "host non consentito", http.StatusForbidden)
		return
	}

	// L'upgrade fallisce con 403 se checkOrigin restituisce false.
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] Upgrade rifiutato (origin=%q): %v\n", r.Header.Get("Origin"), err)
		return
	}
	defer c.Close()
	c.SetReadLimit(maxMsgBytes)

	// Fase 1: autenticazione obbligatoria entro authTimeout.
	_ = c.SetReadDeadline(time.Now().Add(authTimeout))
	_, msg, err := c.ReadMessage()
	if err != nil {
		return
	}
	var first WSMessage
	if json.Unmarshal(msg, &first) != nil || first.Action != "auth" ||
		subtle.ConstantTimeCompare([]byte(first.Token), []byte(wsToken)) != 1 {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] Autenticazione fallita da %s\n", r.RemoteAddr)
		closeWithPolicy(c, "auth")
		return
	}
	if err := writeJSON(c, wsOK("authenticated")); err != nil {
		return
	}
	fmt.Fprintf(os.Stderr, "[Omniclient WS] Client autenticato: %s\n", r.RemoteAddr)

	// Fase 2: loop comandi. Il client deve restare attivo (usare "ping").
	for {
		_ = c.SetReadDeadline(time.Now().Add(idleTimeout))
		_, msg, err := c.ReadMessage()
		if err != nil {
			fmt.Fprintf(os.Stderr, "[Omniclient WS] Client disconnesso: %v\n", err)
			return
		}

		var req WSMessage
		if err := json.Unmarshal(msg, &req); err != nil {
			if writeJSON(c, wsFail(fmt.Errorf("JSON non valido"))) != nil {
				return
			}
			continue
		}
		req.Token = "" // il token non deve mai finire nei log o nei handler

		if err := writeJSON(c, dispatchWS(req)); err != nil {
			return
		}
	}
}

// StartWSServer avvia il listener SOLO su loopback. Se la configurazione di
// sicurezza e' incompleta, non parte.
func StartWSServer(port int) {
	if err := configureWS(); err != nil {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] NON avviato: %v\n", err)
		return
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/ws", handleWebSocket)

	addr := fmt.Sprintf("127.0.0.1:%d", port)
	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] In ascolto su ws://%s/ws\n", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "[Omniclient WS] Errore server fatale: %v\n", err)
		}
	}()
}
