package main

import (
	"embed"
	"fmt"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

// App struct
type App struct {
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// Greeting returns a greeting for the given name
func (a *App) Greeting(name string) string {
	return fmt.Sprintf("Hello %s, welcome to Omninode!", name)
}

func main() {
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
		OnStartup: func(ctx *wails.Context) {
			app.startup(ctx)
		},
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		println("Error:", err.Error())
	}
}

// startup is called when the app starts. The context is saved
func (a *App) startup(ctx *wails.Context) {
	// Initialize MCP client connection here
}
