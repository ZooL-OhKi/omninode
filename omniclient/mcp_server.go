package main

import (
	"context"
	"encoding/json"
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
	baseGateway := NewHTTPGateway("http://127.0.0.1:8000")
	baseGateway.SetAPIKey("")
	return NewOmninodeServerWithGateway(&gatewayWrapper{HTTPGateway: baseGateway})
}

func NewOmninodeServerWithGateway(gateway OmninodeGateway) *OmninodeServer {
	mcpServer := mcp.NewServer(&mcp.Implementation{
		Name:    "omninode-client",
		Version: "v1.0.0",
	}, nil)

	s := &OmninodeServer{
		mcpServer: mcpServer,
		gateway:   gateway,
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

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_workspace_list",
		Description: "Elenca i file del workspace repository OmniNode.",
	}, s.handleOmninodeWorkspaceList)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_workspace_read",
		Description: "Legge un file testuale dal workspace repository OmniNode.",
	}, s.handleOmninodeWorkspaceRead)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_workspace_write",
		Description: "Scrive un file nel repository e verifica automaticamente la modifica con verify_all.",
	}, s.handleOmninodeWorkspaceWrite)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_workspace_rollback",
		Description: "Ripristina l’ultimo snapshot di un file nel workspace repository.",
	}, s.handleOmninodeWorkspaceRollback)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_command_verify",
		Description: "Esegue solo un preset statico di verifica OmniNode.",
	}, s.handleOmninodeCommandVerify)

	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "omninode_autonomy_step",
		Description: "Esegue un passo atomico: write, verify_all e rollback automatico in caso di fallimento.",
	}, s.handleOmninodeAutonomyStep)
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

	payload := map[string]any{
		"workspace_id": input.WorkspaceID,
		"path":         input.Path,
		"content":      input.Content,
	}

	dispatchRes, err := s.gateway.DispatchTask(ctx, "node-local", "workspace.write", payload)
	if err != nil {
		return nil, WorkspaceWriteOutput{}, fmt.Errorf("dispatch fallito: %w", err)
	}

	taskID := dispatchRes.TaskID
	maxAttempts := 30
	attemptDelay := 500 * time.Millisecond

	for i := 0; i < maxAttempts; i++ {
		select {
		case <-ctx.Done():
			return nil, WorkspaceWriteOutput{}, ctx.Err()
		default:
		}

		taskStatus, err := s.gateway.GetTaskStatus(ctx, taskID)
		if err != nil {
			time.Sleep(attemptDelay)
			continue
		}

		switch taskStatus.Status {
		case "completed":
			resultData, ok := taskStatus.Result.(map[string]any)
			if !ok {
				return nil, WorkspaceWriteOutput{Status: "completed", TaskID: taskID}, nil
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
			time.Sleep(attemptDelay)
			continue

		default:
			time.Sleep(attemptDelay)
			continue
		}
	}

	return nil, WorkspaceWriteOutput{
		Status: "timeout",
		TaskID: taskID,
		Error:  "polling timeout: task non completato entro il limite",
	}, fmt.Errorf("polling timeout dopo %d tentativi", maxAttempts)
}

// --- OmniNode autonomy MCP tools ---

type OmninodeWorkspaceListInput struct {
	Subpath string `json:"subpath,omitempty" jsonschema:"Sottopercorso relativo opzionale"`
}

type OmninodeWorkspaceFile struct {
	Path      string `json:"path"`
	SizeBytes int64  `json:"size_bytes"`
	Protected bool   `json:"protected"`
}

type OmninodeWorkspaceListOutput struct {
	Files     []OmninodeWorkspaceFile `json:"files"`
	Truncated bool                    `json:"truncated"`
}

func decodeGatewayMap[T any](value map[string]any, out *T) error {
	raw, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("codifica risposta gateway: %w", err)
	}
	if err := json.Unmarshal(raw, out); err != nil {
		return fmt.Errorf("decodifica risposta gateway: %w", err)
	}
	return nil
}

func (s *OmninodeServer) handleOmninodeWorkspaceList(ctx context.Context, req *mcp.CallToolRequest, input OmninodeWorkspaceListInput) (*mcp.CallToolResult, OmninodeWorkspaceListOutput, error) {
	result, err := s.gateway.WorkspaceList(ctx, input.Subpath)
	if err != nil {
		return nil, OmninodeWorkspaceListOutput{}, err
	}
	var output OmninodeWorkspaceListOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeWorkspaceListOutput{}, err
	}
	return nil, output, nil
}

type OmninodeWorkspaceReadInput struct {
	Path string `json:"path" jsonschema:"Percorso relativo del file da leggere"`
}

type OmninodeWorkspaceReadOutput struct {
	Path      string `json:"path"`
	Content   string `json:"content"`
	SHA256    string `json:"sha256"`
	SizeBytes int64  `json:"size_bytes"`
}

func (s *OmninodeServer) handleOmninodeWorkspaceRead(ctx context.Context, req *mcp.CallToolRequest, input OmninodeWorkspaceReadInput) (*mcp.CallToolResult, OmninodeWorkspaceReadOutput, error) {
	if input.Path == "" {
		return nil, OmninodeWorkspaceReadOutput{}, fmt.Errorf("path è obbligatorio")
	}
	result, err := s.gateway.WorkspaceRead(ctx, input.Path)
	if err != nil {
		return nil, OmninodeWorkspaceReadOutput{}, err
	}
	var output OmninodeWorkspaceReadOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeWorkspaceReadOutput{}, err
	}
	return nil, output, nil
}

type OmninodeWorkspaceWriteInput struct {
	TargetFile   string   `json:"target_file" jsonschema:"Percorso relativo del file da scrivere"`
	Content      string   `json:"content" jsonschema:"Contenuto completo del file"`
	ContextFiles []string `json:"context_files,omitempty" jsonschema:"File di contesto da includere"`
}

type OmninodeWorkspaceWriteOutput struct {
	Status       string         `json:"status"`
	ChangedFiles []string       `json:"changed_files,omitempty"`
	Verification map[string]any `json:"verification,omitempty"`
	RolledBack   bool           `json:"rolled_back,omitempty"`
}

func (s *OmninodeServer) handleOmninodeWorkspaceWrite(ctx context.Context, req *mcp.CallToolRequest, input OmninodeWorkspaceWriteInput) (*mcp.CallToolResult, OmninodeWorkspaceWriteOutput, error) {
	if input.TargetFile == "" {
		return nil, OmninodeWorkspaceWriteOutput{}, fmt.Errorf("target_file è obbligatorio")
	}
	if input.Content == "" {
		return nil, OmninodeWorkspaceWriteOutput{}, fmt.Errorf("content è obbligatorio")
	}
	result, err := s.gateway.AutonomyRunStep(ctx, input.TargetFile, input.Content, input.ContextFiles)
	if err != nil {
		return nil, OmninodeWorkspaceWriteOutput{}, err
	}
	var output OmninodeWorkspaceWriteOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeWorkspaceWriteOutput{}, err
	}
	return nil, output, nil
}

type OmninodeWorkspaceRollbackInput struct {
	Path string `json:"path" jsonschema:"Percorso relativo del file da ripristinare"`
}

type OmninodeWorkspaceRollbackOutput struct {
	Path   string `json:"path"`
	Action string `json:"action"`
}

func (s *OmninodeServer) handleOmninodeWorkspaceRollback(ctx context.Context, req *mcp.CallToolRequest, input OmninodeWorkspaceRollbackInput) (*mcp.CallToolResult, OmninodeWorkspaceRollbackOutput, error) {
	if input.Path == "" {
		return nil, OmninodeWorkspaceRollbackOutput{}, fmt.Errorf("path è obbligatorio")
	}
	result, err := s.gateway.WorkspaceRollback(ctx, input.Path)
	if err != nil {
		return nil, OmninodeWorkspaceRollbackOutput{}, err
	}
	var output OmninodeWorkspaceRollbackOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeWorkspaceRollbackOutput{}, err
	}
	return nil, output, nil
}

var allowedVerifyPresets = map[string]bool{
	"python_compile": true,
	"python_tests":   true,
	"go_vet":         true,
	"go_tests":       true,
	"git_diff_check": true,
	"verify_all":     true,
}

type OmninodeCommandVerifyInput struct {
	Preset string `json:"preset" jsonschema:"Preset statico: python_compile, python_tests, go_vet, go_tests, git_diff_check, verify_all"`
}

type OmninodeCommandVerifyOutput struct {
	Preset     string         `json:"preset"`
	Status     string         `json:"status"`
	Passed     bool           `json:"passed"`
	ExitCode   int            `json:"exit_code"`
	Stdout     string         `json:"stdout,omitempty"`
	Stderr     string         `json:"stderr,omitempty"`
	RawResult  map[string]any `json:"-"`
}

func (s *OmninodeServer) handleOmninodeCommandVerify(ctx context.Context, req *mcp.CallToolRequest, input OmninodeCommandVerifyInput) (*mcp.CallToolResult, OmninodeCommandVerifyOutput, error) {
	if !allowedVerifyPresets[input.Preset] {
		return nil, OmninodeCommandVerifyOutput{}, fmt.Errorf("preset non consentito: %s", input.Preset)
	}
	result, err := s.gateway.CommandVerify(ctx, input.Preset)
	if err != nil {
		return nil, OmninodeCommandVerifyOutput{}, err
	}
	var output OmninodeCommandVerifyOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeCommandVerifyOutput{}, err
	}
	output.RawResult = result
	return nil, output, nil
}

type OmninodeAutonomyStepInput struct {
	TargetFile   string   `json:"target_file" jsonschema:"Percorso relativo del file target"`
	Content      string   `json:"content" jsonschema:"Contenuto completo del file"`
	ContextFiles []string `json:"context_files,omitempty" jsonschema:"File di contesto"`
}

type OmninodeAutonomyStepOutput struct {
	Status       string         `json:"status"`
	ChangedFiles []string       `json:"changed_files,omitempty"`
	Verification map[string]any `json:"verification,omitempty"`
	RolledBack   bool           `json:"rolled_back,omitempty"`
}

func (s *OmninodeServer) handleOmninodeAutonomyStep(ctx context.Context, req *mcp.CallToolRequest, input OmninodeAutonomyStepInput) (*mcp.CallToolResult, OmninodeAutonomyStepOutput, error) {
	if input.TargetFile == "" {
		return nil, OmninodeAutonomyStepOutput{}, fmt.Errorf("target_file è obbligatorio")
	}
	if input.Content == "" {
		return nil, OmninodeAutonomyStepOutput{}, fmt.Errorf("content è obbligatorio")
	}
	result, err := s.gateway.AutonomyRunStep(ctx, input.TargetFile, input.Content, input.ContextFiles)
	if err != nil {
		return nil, OmninodeAutonomyStepOutput{}, err
	}
	var output OmninodeAutonomyStepOutput
	if err := decodeGatewayMap(result, &output); err != nil {
		return nil, OmninodeAutonomyStepOutput{}, err
	}
	return nil, output, nil
}
