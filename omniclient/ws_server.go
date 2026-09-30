package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"runtime"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Permette la connessione da qualsiasi estensione/pagina web
	},
}

type WSMessage struct {
	Action  string `json:"action"`
	Command string `json:"command"`
}

type WSResponse struct {
	Status string `json:"status"`
	Output string `json:"output"`
	Error  string `json:"error,omitempty"`
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] Errore upgrade: %v\n", err)
		return
	}
	defer c.Close()

	fmt.Fprintf(os.Stderr, "[Omniclient WS] Client web connesso\n")

	for {
		_, msg, err := c.ReadMessage()
		if err != nil {
			fmt.Fprintf(os.Stderr, "[Omniclient WS] Client disconnesso: %v\n", err)
			break
		}

		var req WSMessage
		if err := json.Unmarshal(msg, &req); err != nil {
			continue
		}

		if req.Action == "exec" && req.Command != "" {
			fmt.Fprintf(os.Stderr, "[Omniclient WS] Esecuzione comando: %s\n", req.Command)

			var cmd *exec.Cmd
			if runtime.GOOS == "windows" {
				cmd = exec.Command("cmd", "/c", req.Command)
			} else {
				cmd = exec.Command("sh", "-c", req.Command)
			}

			out, err := cmd.CombinedOutput()

			resp := WSResponse{
				Status: "success",
				Output: string(out),
			}
			if err != nil {
				resp.Status = "error"
				resp.Error = err.Error()
			}

			respJSON, _ := json.Marshal(resp)
			c.WriteMessage(websocket.TextMessage, respJSON)
		}
	}
}

// StartWSServer avvia il listener HTTP/WS in background
func StartWSServer(port int) {
	http.HandleFunc("/ws", handleWebSocket)
	addr := fmt.Sprintf("127.0.0.1:%d", port)

	go func() {
		fmt.Fprintf(os.Stderr, "[Omniclient WS] In ascolto su ws://%s/ws\n", addr)
		if err := http.ListenAndServe(addr, nil); err != nil {
			fmt.Fprintf(os.Stderr, "[Omniclient WS] Errore server fatale: %v\n", err)
		}
	}()
}