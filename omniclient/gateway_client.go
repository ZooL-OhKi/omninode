package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"
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

// HTTPGateway è l'implementazione del client verso il cluster
type HTTPGateway struct {
	baseURL string
	client  *http.Client
}

// NewHTTPGateway crea un gateway con un client HTTP resiliente di default
func NewHTTPGateway(baseURL string) *HTTPGateway {
	defaultClient := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			Proxy: http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   5 * time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   5 * time.Second,
			ResponseHeaderTimeout: 10 * time.Second,
			IdleConnTimeout:       90 * time.Second,
		},
	}
	return NewHTTPGatewayWithClient(baseURL, defaultClient)
}

// NewHTTPGatewayWithClient permette di iniettare un client HTTP custom (es. per test)
func NewHTTPGatewayWithClient(baseURL string, client *http.Client) *HTTPGateway {
	return &HTTPGateway{
		baseURL: baseURL,
		client:  client,
	}
}

// doJSON è il motore di rete interno, testabile e agnostico rispetto agli endpoint reali
func (g *HTTPGateway) doJSON(ctx context.Context, method, path string, reqBody any, resBody any) error {
	url := g.baseURL + path

	var bodyReader io.Reader
	if reqBody != nil {
		jsonData, err := json.Marshal(reqBody)
		if err != nil {
			return fmt.Errorf("errore serializzazione request: %w", err)
		}
		bodyReader = bytes.NewReader(jsonData)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, bodyReader)
	if err != nil {
		return fmt.Errorf("errore creazione request: %w", err)
	}

	req.Header.Set("Accept", "application/json")
	if reqBody != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	res, err := g.client.Do(req)
	if err != nil {
		return fmt.Errorf("errore esecuzione request: %w", err)
	}
	defer res.Body.Close()

	// Limita la lettura a 5MB per prevenire attacchi OOM su payload eccessivi
	limitedBody := io.LimitReader(res.Body, 5*1024*1024)

	if res.StatusCode < 200 || res.StatusCode >= 300 {
		errData, _ := io.ReadAll(limitedBody)
		return fmt.Errorf("HTTP %d: %s", res.StatusCode, string(bytes.TrimSpace(errData)))
	}

	if resBody != nil {
		if err := json.NewDecoder(limitedBody).Decode(resBody); err != nil {
			return fmt.Errorf("errore decodifica response: %w", err)
		}
	}

	return nil
}

// --- METODI PUBBLICI MOCKATI (IN ATTESA DI SPECIFICHE) ---

func (g *HTTPGateway) RestartNode(nodeID string) error {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return nil
}

func (g *HTTPGateway) Execute(ctx context.Context, language, code string) (*ExecuteResult, error) {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return &ExecuteResult{
		Stdout:   "Codice eseguito con successo sul nodo (Mock)",
		Stderr:   "",
		ExitCode: 0,
		NodeID:   "node-alpha-01",
	}, nil
}

func (g *HTTPGateway) Browse(ctx context.Context, url, format string) (*BrowseResult, error) {
	// TODO: Cablare la chiamata reale doJSON quando documentata
	return &BrowseResult{
		Title:   "Pagina estratta da Omninode",
		Content: "# Contenuto Markdown (Mock)\nQuesto è il parsing di: " + url,
		NodeID:  "node-browser-02",
	}, nil
}
