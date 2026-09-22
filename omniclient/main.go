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

type App struct {
    mcpServer *OmninodeServer
}

func NewApp() *App {
    return &App{mcpServer: NewOmninodeServer()}
}

func (a *App) Greeting(name string) string {
    return fmt.Sprintf("Hello %s, welcome to Omninode!", name)
}

func (a *App) GetFabricHealth() map[string]interface{} {
    if a.mcpServer.gateway != nil {
        health, err := a.mcpServer.gateway.FabricHealth()
        if err == nil {
            return health
        }
        return map[string]interface{}{"health_status": "unavailable", "error": err.Error()}
    }
    return map[string]interface{}{"health_status": "local-fallback", "total_nodes": 0, "online_nodes": 0}
}

func (a *App) startup() {
    if a.mcpServer.gateway == nil {
        log.Println("Node1 Gateway not configured; MCP uses local fallback mode")
        return
    }
    log.Println("Omninode Client connected to configured Node1 Gateway")
}

func main() {
    if len(os.Args) > 1 && os.Args[1] == "--mcp-stdio" {
        if err := NewOmninodeServer().StartMCPStdio(); err != nil {
            log.Fatalf("MCP stdio error: %v", err)
        }
        return
    }

    app := NewApp()
    err := wails.Run(&options.App{
        Title:  "Omninode Client",
        Width:  1024,
        Height: 768,
        AssetServer: &assetserver.Options{
            Assets: assets,
        },
        BackgroundColour: &options.RGBA{R: 27, G: 38, B: 54, A: 1},
        OnStartup:        app.startup,
        Bind:             []interface{}{app},
    })
    if err != nil {
        log.Fatal(err)
    }
}
