package main

import (
	"embed"
	"fmt"
	"log"
	"os"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

// App struct
type App struct {
	mcpServer *OmninodeServer
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{
		mcpServer: NewOmninodeServer(),
	}
}

// Greeting returns a greeting for the given name
func (a *App) Greeting(name string) string {
	return fmt.Sprintf("Hello %s, welcome to Omninode!", name)
}

// GetFabricHealth returns the current fabric health status
func (a *App) GetFabricHealth() map[string]interface{} {
	// Wrapper per esporre a Wails frontend
	_, exists := a.mcpServer.GetNodeStatus("gateway")
	if !exists {
		// Simula nodo gateway
		a.mcpServer.UpdateNodeStatus("gateway", NodeStatus{
			ID:       "gateway",
			Status:   "online",
			Load:     15,
			LastSeen: 0,
		})
	}

	s := a.mcpServer
	s.statusMutex.RLock()
	defer s.statusMutex.RUnlock()

	total := len(s.nodeStatus)
	online := 0
	for _, node := range s.nodeStatus {
		if node.Status == "online" {
			online++
		}
	}

	return map[string]interface{}{
		"total_nodes":   total,
		"online_nodes":  online,
		"health_status": "healthy",
	}
}

// startup is called when the app starts
func (a *App) startup(ctx *wails.Context) {
	log.Println("Omninode Client starting...")

	// Avvia MCP SSE server in goroutine separata
	go func() {
		if err := a.mcpServer.StartMCPSSE(":8080"); err != nil {
			log.Printf("MCP SSE server error: %v", err)
		}
	}()

	log.Println("MCP SSE server started on :8080")
}

func main() {
	// Check for MCP stdio mode (for agent integration)
	if len(os.Args) > 1 && os.Args[1] == "--mcp-stdio" {
		server := NewOmninodeServer()
		if err := server.StartMCPStdio(); err != nil {
			log.Fatalf("MCP stdio error: %v", err)
		}
		return
	}

	// Create an instance of the app structure
	app := NewApp()

	// Create application with options
	err := wails.Run(&options.App{
		Title:  "Omninode Client",
		Width:  1024,
		Height: 768,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 27, G: 38, B: 54, A: 1},
		OnStartup:        app.startup,
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		println("Error:", err.Error())
	}
}
