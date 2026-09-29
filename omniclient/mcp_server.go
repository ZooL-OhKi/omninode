package main

import (
	"context"
	"fmt"
	"log"
	"time"

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

	baseGateway := NewHTTPGateway("http://127.0.0.1:8000")
	// Configura API key dalle variabili d'ambiente se disponibile
	// In produzione, usare os.Getenv("OMNINODE_API_KEY")
	baseGateway.SetAPIKey("")

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

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "workspace.write",
		Description: "Scrive un file in un workspace autorizzato tramite il gateway Omninode. Supporta polling asincrono per task di lunga durata.",
	}, s.handleWorkspaceWrite)
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

// WorkspaceWriteInput definisce l'input per il tool workspace.write
type WorkspaceWriteInput struct {
	WorkspaceID  string `json:"workspace_id" jsonschema:"ID del workspace autorizzato (es: 'temporary')"`
	Path         string `json:"path" jsonschema:"Percorso relativo del file all'interno del workspace"`
	Content      string `json:"content" jsonschema:"Contenuto del file da scrivere"`
}

// WorkspaceWriteOutput definisce l'output del tool workspace.write
type WorkspaceWriteOutput struct {
	Status       string `json:"status"`
	TaskID       string `json:"task_id,omitempty"`
	Path         string `json:"path,omitempty"`
	BytesWritten int64  `json:"bytes_written,omitempty"`
	Error        string `json:"error,omitempty"`
}

// handleWorkspaceWrite gestisce il tool workspace.write con polling asincrono
func (s *OmninodeServer) handleWorkspaceWrite(ctx context.Context, req *mcp.CallToolRequest, input WorkspaceWriteInput) (*mcp.CallToolResult, WorkspaceWriteOutput, error) {
	if input.WorkspaceID == "" {
		return nil, WorkspaceWriteOutput{}, fmt.Errorf("workspace_id è obbligatorio")
	}
	if input.Path == "" {
		return nil, WorkspaceWriteOutput{}, fmt.Errorf("path è obbligatorio")
	}
	if input.Content == "" {
		return nil, WorkspaceWriteOutput{}, fmt.Errorf("content è obbligatorio")
	}

	// Prepara il payload per il gateway
	payload := map[string]any{
		"workspace_id": input.WorkspaceID,
		"path":         input.Path,
		"content":      input.Content,
	}

	// Invia il task al gateway (node-local per il workspace temporaneo locale)
	dispatchRes, err := s.gateway.DispatchTask(ctx, "node-local", "workspace.write", payload)
	if err != nil {
		return nil, WorkspaceWriteOutput{}, fmt.Errorf("dispatch fallito: %w", err)
	}

	// Il gateway risponde con 202 Accepted e task_id
	// Eseguiamo polling limitato per attendere il completamento
	taskID := dispatchRes.TaskID
	maxAttempts := 30
	attemptDelay := 500 * time.Millisecond

	for i := 0; i < maxAttempts; i++ {
		// Verifica se il context è stato cancellato
		select {
		case <-ctx.Done():
			return nil, WorkspaceWriteOutput{}, ctx.Err()
		default:
		}

		// Interroga lo stato del task
		taskStatus, err := s.gateway.GetTaskStatus(ctx, taskID)
		if err != nil {
			// Se il task non è ancora nel DB, aspetta e riprova
			time.Sleep(attemptDelay)
			continue
		}

		// Controlla lo stato del task
		switch taskStatus.Status {
		case "completed":
			// Estrai il risultato dal campo result
			resultData, ok := taskStatus.Result.(map[string]any)
			if !ok {
				return nil, WorkspaceWriteOutput{
					Status: "completed",
					TaskID: taskID,
				}, nil
			}

			bytesWritten := int64(0)
			if bw, ok := resultData["bytes_written"].(float64); ok {
				bytesWritten = int64(bw)
			}

			return nil, WorkspaceWriteOutput{
				Status:       "completed",
				TaskID:       taskID,
				Path:         input.Path,
				BytesWritten: bytesWritten,
			}, nil

		case "error":
			return nil, WorkspaceWriteOutput{
				Status: "error",
				TaskID: taskID,
				Error:  taskStatus.Error,
			}, fmt.Errorf("task fallito: %s", taskStatus.Error)

		case "dispatched", "queued", "running":
			// Task ancora in esecuzione, aspetta e riprova
			time.Sleep(attemptDelay)
			continue

		default:
			// Stato sconosciuto, aspetta e riprova
			time.Sleep(attemptDelay)
			continue
		}
	}

	// Timeout: polling esaurito senza risultato
	return nil, WorkspaceWriteOutput{
		Status: "timeout",
		TaskID: taskID,
		Error:  "polling timeout: task non completato entro il limite",
	}, fmt.Errorf("polling timeout dopo %d tentativi", maxAttempts)
}
