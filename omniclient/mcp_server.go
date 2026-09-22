package main

import (
	"context"
	"fmt"
	"log"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type OmninodeGateway interface {
	Gateway
	FabricHealth() (map[string]interface{}, error)
}

type gatewayWrapper struct {
	*HTTPGateway
}

func (g *gatewayWrapper) FabricHealth() (map[string]interface{}, error) {
	return map[string]interface{}{
		"health_status": "ok",
		"total_nodes":   1,
		"online_nodes":  1,
	}, nil
}

type OmninodeServer struct {
	mcpServer *mcp.Server
	gateway   OmninodeGateway
}

func NewOmninodeServer() *OmninodeServer {
	mcpServer := mcp.NewServer(&mcp.Implementation{
		Name:    "omninode-client",
		Version: "v1.0.0",
	}, nil)

	baseGateway := NewHTTPGateway("https://api.omninode.local/v1")
	extendedGateway := &gatewayWrapper{HTTPGateway: baseGateway}

	s := &OmninodeServer{
		mcpServer: mcpServer,
		gateway:   extendedGateway,
	}
	s.registerTools()
	return s
}

func (s *OmninodeServer) StartMCPStdio() error {
	if err := s.mcpServer.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Printf("Server failed: %v", err)
		return err
	}
	return nil
}

func (s *OmninodeServer) registerTools() {
	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "restart_node",
		Description: "Invia un comando di riavvio a un nodo specifico tramite il gateway.",
	}, s.handleRestartNode)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "run_sandbox_code",
		Description: "Esegue codice su un nodo cloud e restituisce l'output.",
	}, s.handleRunSandboxCode)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "browse_webpage",
		Description: "Visita una pagina web e ne estrae il contenuto.",
	}, s.handleBrowseWebpage)
}

type RestartNodeInput struct {
	NodeID string `json:"node_id" jsonschema:"L'ID del nodo da riavviare"`
}

type RestartNodeOutput struct {
	Status string `json:"status"`
	NodeID string `json:"node_id"`
}

func (s *OmninodeServer) handleRestartNode(ctx context.Context, req *mcp.CallToolRequest, input RestartNodeInput) (*mcp.CallToolResult, RestartNodeOutput, error) {
	if input.NodeID == "" {
		return nil, RestartNodeOutput{}, fmt.Errorf("node_id è obbligatorio")
	}
	if err := s.gateway.RestartNode(input.NodeID); err != nil {
		return nil, RestartNodeOutput{}, err
	}
	return nil, RestartNodeOutput{Status: "restarted", NodeID: input.NodeID}, nil
}

type RunSandboxCodeInput struct {
	Language string `json:"language" jsonschema:"Il linguaggio da usare per l'esecuzione. Valori ammessi: python, javascript, bash"`
	Code     string `json:"code" jsonschema:"Il codice sorgente completo da eseguire nel nodo"`
}

type RunSandboxCodeOutput struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	NodeID   string `json:"node_id"`
}

func (s *OmninodeServer) handleRunSandboxCode(ctx context.Context, req *mcp.CallToolRequest, input RunSandboxCodeInput) (*mcp.CallToolResult, RunSandboxCodeOutput, error) {
	if input.Language == "" {
		return nil, RunSandboxCodeOutput{}, fmt.Errorf("language è obbligatorio")
	}
	if input.Code == "" {
		return nil, RunSandboxCodeOutput{}, fmt.Errorf("code è obbligatorio")
	}
	res, err := s.gateway.Execute(ctx, input.Language, input.Code)
	if err != nil {
		return nil, RunSandboxCodeOutput{}, err
	}
	return nil, RunSandboxCodeOutput{Stdout: res.Stdout, Stderr: res.Stderr, ExitCode: res.ExitCode, NodeID: res.NodeID}, nil
}

type BrowseWebpageInput struct {
	URL            string `json:"url" jsonschema:"L'URL completo della pagina web da visitare"`
	ExtractContent string `json:"extract_content,omitempty" jsonschema:"Formato desiderato per il parsing. Valori ammessi: markdown, text, html (default: markdown)"`
}

type BrowseWebpageOutput struct {
	Title   string `json:"title"`
	Content string `json:"content"`
	NodeID  string `json:"node_id,omitempty"`
}

func (s *OmninodeServer) handleBrowseWebpage(ctx context.Context, req *mcp.CallToolRequest, input BrowseWebpageInput) (*mcp.CallToolResult, BrowseWebpageOutput, error) {
	if input.URL == "" {
		return nil, BrowseWebpageOutput{}, fmt.Errorf("url è obbligatorio")
	}
	format := input.ExtractContent
	if format == "" {
		format = "markdown"
	}
	res, err := s.gateway.Browse(ctx, input.URL, format)
	if err != nil {
		return nil, BrowseWebpageOutput{}, err
	}
	return nil, BrowseWebpageOutput{Title: res.Title, Content: res.Content, NodeID: res.NodeID}, nil
}
