package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/playwright-community/playwright-go"
)

var (
	pw        *playwright.Playwright
	pwBrowser playwright.Browser
	pwContext playwright.BrowserContext
	pwPage    playwright.Page
)

// InitWebAgent si aggancia a un vero browser in esecuzione per bypassare i WAF (es. Datadome/Cloudflare)
func InitWebAgent() error {
	err := playwright.Install()
	if err != nil {
		fmt.Fprintf(os.Stderr, "[WebAgent] Errore installazione driver: %v\n", err)
	}

	pw, err = playwright.Run()
	if err != nil {
		return err
	}

	// Connessione tramite Chrome DevTools Protocol (Richiede Chrome avviato con --remote-debugging-port=9222)
	pwBrowser, err = pw.Chromium.ConnectOverCDP("http://localhost:9222")
	if err != nil {
		return fmt.Errorf("impossibile connettersi a Chrome su 9222 (è avviato con --remote-debugging-port=9222?): %v", err)
	}

	contexts := pwBrowser.Contexts()
	if len(contexts) > 0 {
		pwContext = contexts[0]
		pages := pwContext.Pages()
		if len(pages) > 0 {
			pwPage = pages[0]
		} else {
			pwPage, _ = pwContext.NewPage()
		}
	} else {
		return fmt.Errorf("nessun contesto browser trovato")
	}

	fmt.Fprintf(os.Stderr, "[WebAgent] Connesso a Chrome Reale via CDP con successo.\n")
	return nil
}

// SnapshotState cattura l'Accessibility Tree e lo scrive su disco per risparmiare Token LLM
func SnapshotState() (string, error) {
	if pwPage == nil {
		return "", fmt.Errorf("pagina non inizializzata")
	}

	snapshot, err := pwPage.Accessibility().Snapshot()
	if err != nil {
		return "", err
	}

	data, err := json.MarshalIndent(snapshot, "", "  ")
	if err != nil {
		return "", err
	}

	os.MkdirAll("omninode_state", 0755)
	filePath := filepath.Join("omninode_state", "AX_TREE.txt")
	err = os.WriteFile(filePath, data, 0644)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Stato DOM salvato in %s. Leggi il file per vedere i nodi.", filePath), nil
}
