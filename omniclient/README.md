# OmniClient

Desktop application for Omninode fabric, built with Go and Wails.

## Prerequisites

- Go 1.21+
- Node.js 18+
- Wails CLI (`go install github.com/wailsapp/wails/v2/cmd/wails@latest`)

## Development

```bash
wails dev
```

## Build

```bash
wails build
```

## Architecture

OmniClient connects to the Omninode fabric via MCP (Model Context Protocol) and provides:
- Local agent orchestration
- Zero-touch updates via GitHub Actions
- Distributed computation coordination
