package main

import (
	"fmt"
	"os"

	"github.com/playwright-community/playwright-go"
)

// Stato globale del browser condiviso da tutte le sessioni agente.
// pwContext/pwPage puntano al contesto di default del Chrome reale e servono
// solo come ripiego; le sessioni agente usano contesti dedicati (vedi cdp_agent.go).
var (
	pw        *playwright.Playwright
	pwBrowser playwright.Browser
	pwContext playwright.BrowserContext
	pwPage    playwright.Page
)

// InitWebAgent si aggancia a un Chrome reale gia' in esecuzione via CDP.
// Requisito: Chrome avviato con --remote-debugging-port=9222 e --user-data-dir dedicato.
// La porta 9222 deve restare in ascolto SOLO su 127.0.0.1.
func InitWebAgent() error {
	if err := playwright.Install(); err != nil {
		fmt.Fprintf(os.Stderr, "[WebAgent] Errore installazione driver: %v\n", err)
	}

	var err error
	pw, err = playwright.Run()
	if err != nil {
		return fmt.Errorf("avvio playwright: %w", err)
	}

	pwBrowser, err = pw.Chromium.ConnectOverCDP("http://127.0.0.1:9222")
	if err != nil {
		return fmt.Errorf("impossibile connettersi a Chrome su 9222 (avviato con --remote-debugging-port=9222?): %w", err)
	}

	contexts := pwBrowser.Contexts()
	if len(contexts) == 0 {
		return fmt.Errorf("nessun contesto browser trovato")
	}
	pwContext = contexts[0]

	if pages := pwContext.Pages(); len(pages) > 0 {
		pwPage = pages[0]
	} else if pwPage, err = pwContext.NewPage(); err != nil {
		return fmt.Errorf("creazione pagina: %w", err)
	}

	fmt.Fprintf(os.Stderr, "[WebAgent] Connesso a Chrome reale via CDP.\n")
	return nil
}
