package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
)

// main avvia il worker Go: inizializza il browser (CDP) e il server WS locale.
// Il processo resta in ascolto finche' non riceve SIGINT/SIGTERM.
func main() {
	// Inizializza il browser (Chrome reale via CDP su 127.0.0.1:9222).
	if err := InitWebAgent(); err != nil {
		fmt.Fprintf(os.Stderr, "[main] Errore InitWebAgent: %v\n", err)
		os.Exit(1)
	}

	// Avvia il server WebSocket locale (solo loopback, con token+origin).
	StartWSServer(8080)

	// Hook per shutdown pulito.
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch

	fmt.Fprintf(os.Stderr, "[main] Shutdown...\n")
	// Qui si potrebbero chiudere le sessioni (sessions.Close(agentID)) se servisse.
}
