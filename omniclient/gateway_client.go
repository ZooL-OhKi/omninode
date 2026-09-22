package main

import (
	"context"
)

// ExecuteResult mappa la risposta di un nodo dopo aver eseguito codice
type ExecuteResult struct {
	Stdout   string
	Stderr   string
	ExitCode int
	NodeID   string
}

// BrowseResult mappa la risposta di un nodo dopo aver esplorato una pagina web
type BrowseResult struct {
	Title   string
	Content string
	NodeID  string
}

// Gateway definisce il contratto per parlare con il control plane di Omninode
type Gateway interface {
	RestartNode(nodeID string) error
	Execute(ctx context.Context, language, code string) (*ExecuteResult, error)
	Browse(ctx context.Context, url, format string) (*BrowseResult, error)
}

// HTTPGateway è l'implementazione concreta del client verso il cluster
type HTTPGateway struct {
	Endpoint string
}

func NewHTTPGateway(endpoint string) *HTTPGateway {
	return &HTTPGateway{Endpoint: endpoint}
}

func (g *HTTPGateway) RestartNode(nodeID string) error {
	// TODO: Cablare la vera richiesta HTTP/gRPC al control plane di Omninode
	return nil
}

func (g *HTTPGateway) Execute(ctx context.Context, language, code string) (*ExecuteResult, error) {
	// TODO: Cablare la vera richiesta HTTP/gRPC per l'esecuzione in sandbox
	return &ExecuteResult{
		Stdout:   "Codice eseguito con successo sul nodo (Mock)",
		Stderr:   "",
		ExitCode: 0,
		NodeID:   "node-alpha-01",
	}, nil
}

func (g *HTTPGateway) Browse(ctx context.Context, url, format string) (*BrowseResult, error) {
	// TODO: Cablare la vera richiesta HTTP/gRPC verso un nodo browser headless
	return &BrowseResult{
		Title:   "Pagina estratta da Omninode",
		Content: "# Contenuto Markdown (Mock)\nQuesto è il parsing di: " + url,
		NodeID:  "node-browser-02",
	}, nil
}
