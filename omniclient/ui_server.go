package main

import (
	"bytes"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"
)

//go:embed ui/*
var uiAssets embed.FS

type UIWriteRequest struct {
	AgentID string `json:"agent_id"`
	Path    string `json:"path"`
	Content string `json:"content"`
}

type UIPromptRequest struct {
	Prompt  string `json:"prompt"`
	AgentID string `json:"agent_id"`
	Path    string `json:"path"`
}

type TaskHistoryEntry struct {
	TaskID    string `json:"task_id"`
	Method    string `json:"method"`
	AgentID   string `json:"agent_id"`
	Path      string `json:"path"`
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

var (
	historyMu   sync.Mutex
	taskHistory []TaskHistoryEntry
)

func recordHistory(entry TaskHistoryEntry) {
	historyMu.Lock()
	defer historyMu.Unlock()
	taskHistory = append([]TaskHistoryEntry{entry}, taskHistory...)
	if len(taskHistory) > 25 {
		taskHistory = taskHistory[:25]
	}
}

// ParseNaturalWriteCommand estrae agent_id, path e content da un comando in linguaggio naturale
func ParseNaturalWriteCommand(prompt, defaultAgent, defaultPath string) (agentID, path, content string, err error) {
	p := strings.TrimSpace(prompt)
	if p == "" {
		return "", "", "", fmt.Errorf("comando vuoto")
	}

	agentID = defaultAgent
	if agentID == "" {
		agentID = "archivista"
	}

	reFile := regexp.MustCompile(`(?i)\b([a-z0-9_\-\.]+\.(txt|md|json|log|yaml|yml|csv))\b`)
	if matches := reFile.FindStringSubmatch(p); len(matches) > 1 {
		path = matches[1]
	} else if strings.TrimSpace(defaultPath) != "" {
		path = strings.TrimSpace(defaultPath)
	} else {
		path = fmt.Sprintf("appunti-%d.txt", time.Now().Unix())
	}

	if idx := strings.Index(p, ":"); idx != -1 && idx+1 < len(p) {
		content = strings.TrimSpace(p[idx+1:])
	} else {
		content = p
	}
	content = strings.Trim(content, "\"'`")
	return agentID, path, content, nil
}

func forwardJSONRPC(r *http.Request, gatewayURL, mcpSecret, method string, params map[string]interface{}) (int, []byte, string, error) {
	taskID := fmt.Sprintf("ui-task-%d", time.Now().UnixNano())
	rpcPayload := map[string]interface{}{
		"jsonrpc": "2.0",
		"method":  method,
		"params":  params,
		"id":      taskID,
	}

	bodyBytes, err := json.Marshal(rpcPayload)
	if err != nil {
		return http.StatusInternalServerError, nil, taskID, err
	}

	endpoint := strings.TrimRight(gatewayURL, "/") + "/mcp"
	httpReq, err := http.NewRequestWithContext(r.Context(), http.MethodPost, endpoint, bytes.NewReader(bodyBytes))
	if err != nil {
		return http.StatusInternalServerError, nil, taskID, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if mcpSecret != "" {
		httpReq.Header.Set("Authorization", "Bearer "+mcpSecret)
	}

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return http.StatusBadGateway, nil, taskID, err
	}
	defer resp.Body.Close()

	respBytes, err := io.ReadAll(resp.Body)
	return resp.StatusCode, respBytes, taskID, err
}

// NewUIHandler costruisce l'handler HTTP con asset PWA embedded e proxy sicuro verso il Gateway MCP.
// Il parametro variadic bridge è opzionale per mantenere compatibilità con i chiamanti esistenti.
func NewUIHandler(gatewayURL string, mcpSecret string, bridge ...*BridgeService) (http.Handler, error) {
	subFS, err := fs.Sub(uiAssets, "ui")
	if err != nil {
		return nil, fmt.Errorf("errore caricamento asset UI: %w", err)
	}

	mux := http.NewServeMux()
	fileServer := http.FileServer(http.FS(subFS))

	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		historyMu.Lock()
		hist := append([]TaskHistoryEntry(nil), taskHistory...)
		historyMu.Unlock()

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"status":    "online",
			"component": "omninode-pwa-ui",
			"gateway":   gatewayURL,
			"history":   hist,
		})
	})

	if len(bridge) == 1 && bridge[0] != nil {
		mux.Handle("/api/bridge/execute", bridge[0])
	}

	mux.HandleFunc("/api/task/write", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
			return
		}

		var req UIWriteRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Payload JSON non valido", http.StatusBadRequest)
			return
		}
		if strings.TrimSpace(req.Path) == "" {
			http.Error(w, "Il campo path e obbligatorio", http.StatusBadRequest)
			return
		}
		if strings.TrimSpace(req.AgentID) == "" {
			req.AgentID = "archivista"
		}

		status, respBytes, taskID, err := forwardJSONRPC(r, gatewayURL, mcpSecret, "workspace.write", map[string]interface{}{
			"agent_id": req.AgentID,
			"path":     req.Path,
			"content":  req.Content,
		})
		if err != nil {
			recordHistory(TaskHistoryEntry{TaskID: taskID, Method: "workspace.write", AgentID: req.AgentID, Path: req.Path, Status: "gateway_error", Timestamp: time.Now().Format(time.RFC3339)})
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadGateway)
			_ = json.NewEncoder(w).Encode(map[string]string{
				"status": "error",
				"error":  fmt.Sprintf("Gateway non raggiungibile: %v", err),
			})
			return
		}

		recordHistory(TaskHistoryEntry{TaskID: taskID, Method: "workspace.write", AgentID: req.AgentID, Path: req.Path, Status: fmt.Sprintf("HTTP %d", status), Timestamp: time.Now().Format(time.RFC3339)})
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		_, _ = w.Write(respBytes)
	})

	mux.HandleFunc("/api/task/prompt", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
			return
		}

		var req UIPromptRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Payload JSON non valido", http.StatusBadRequest)
			return
		}

		agentID, path, content, err := ParseNaturalWriteCommand(req.Prompt, req.AgentID, req.Path)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		status, respBytes, taskID, err := forwardJSONRPC(r, gatewayURL, mcpSecret, "workspace.write", map[string]interface{}{
			"agent_id": agentID,
			"path":     path,
			"content":  content,
		})
		if err != nil {
			recordHistory(TaskHistoryEntry{TaskID: taskID, Method: "workspace.write (AI)", AgentID: agentID, Path: path, Status: "gateway_error", Timestamp: time.Now().Format(time.RFC3339)})
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadGateway)
			_ = json.NewEncoder(w).Encode(map[string]string{
				"status": "error",
				"error":  fmt.Sprintf("Gateway non raggiungibile: %v", err),
			})
			return
		}

		recordHistory(TaskHistoryEntry{TaskID: taskID, Method: "workspace.write (AI)", AgentID: agentID, Path: path, Status: fmt.Sprintf("HTTP %d", status), Timestamp: time.Now().Format(time.RFC3339)})
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		_, _ = w.Write(respBytes)
	})

	mux.Handle("/", fileServer)
	return mux, nil
}
