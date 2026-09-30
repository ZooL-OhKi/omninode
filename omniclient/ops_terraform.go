package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	_ "modernc.org/sqlite"
)

const (
	TerraformWorkDir = "C:\\omninode\\iac"
	ApprovalTTL      = 10 * time.Minute
)

var db *sql.DB

// InitDB inizializza il database SQLite per i task in approvazione.
func InitDB(dsn string) error {
	var err error
	db, err = sql.Open("sqlite", dsn)
	if err != nil {
		return err
	}
	query := `
	CREATE TABLE IF NOT EXISTS pending_tasks (
		task_id TEXT PRIMARY KEY,
		agent_id TEXT,
		subcmd TEXT,
		status TEXT,
		expires_at DATETIME
	);`
	_, err = db.Exec(query)
	return err
}

// HandleTerraform gestisce i comandi terraform con allowlist e HITL per apply/destroy.
func HandleTerraform(client mqtt.Client, nodeID, taskID, agentID, subcmd string) {
	allowlist := map[string]bool{"plan": true, "show": true, "apply": true, "destroy": true}
	if !allowlist[subcmd] {
		publishRes(client, nodeID, taskID, "error", "Sottocomando non autorizzato")
		return
	}
	if subcmd == "apply" || subcmd == "destroy" {
		processHITL(client, nodeID, taskID, agentID, subcmd)
	} else {
		go executeTerraform(client, nodeID, taskID, subcmd)
	}
}

func processHITL(client mqtt.Client, nodeID, taskID, agentID, subcmd string) {
	expiresAt := time.Now().Add(ApprovalTTL)

	_, err := db.Exec(`INSERT INTO pending_tasks (task_id, agent_id, subcmd, status, expires_at) 
		VALUES (?, ?, ?, 'pending', ?)`, taskID, agentID, subcmd, expiresAt)
	if err != nil {
		publishRes(client, nodeID, taskID, "error", "Errore interno persistenza")
		return
	}

	alert := map[string]string{
		"task_id":   taskID,
		"agent_id":  agentID,
		"command":   fmt.Sprintf("terraform %s", subcmd),
		"timestamp": time.Now().Format(time.RFC3339),
	}
	alertBytes, _ := json.Marshal(alert)
	client.Publish("omninode/alerts/approval", 1, false, alertBytes)
	publishRes(client, nodeID, taskID, "pending_approval", fmt.Sprintf("In attesa di approvazione per terraform %s", subcmd))
}

// HandleApproval elabora le decisioni di approvazione/rifiuto dal gateway.
func HandleApproval(client mqtt.Client, nodeID string, payload []byte) {
	var dec struct {
		TaskID   string `json:"task_id"`
		Approved bool   `json:"approved"`
	}
	if err := json.Unmarshal(payload, &dec); err != nil {
		return
	}

	var subcmd string
	var expiresAt time.Time
	err := db.QueryRow(`SELECT subcmd, expires_at FROM pending_tasks WHERE task_id = ? AND status = 'pending'`, dec.TaskID).Scan(&subcmd, &expiresAt)
	if err != nil {
		return
	}

	if time.Now().After(expiresAt) {
		db.Exec(`UPDATE pending_tasks SET status = 'timeout' WHERE task_id = ?`, dec.TaskID)
		publishRes(client, nodeID, dec.TaskID, "timeout", "Tempo scaduto per l'approvazione")
		return
	}

	if dec.Approved {
		db.Exec(`UPDATE pending_tasks SET status = 'approved' WHERE task_id = ?`, dec.TaskID)
		go executeTerraform(client, nodeID, dec.TaskID, subcmd)
	} else {
		db.Exec(`UPDATE pending_tasks SET status = 'rejected' WHERE task_id = ?`, dec.TaskID)
		publishRes(client, nodeID, dec.TaskID, "rejected", "Task rifiutato dall'operatore")
	}
}

func executeTerraform(client mqtt.Client, nodeID, taskID, subcmd string) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	cmdArgs := []string{subcmd}
	if subcmd == "apply" || subcmd == "destroy" {
		cmdArgs = append(cmdArgs, "-auto-approve")
	}

	cmd := exec.CommandContext(ctx, "terraform", cmdArgs...)
	cmd.Dir = TerraformWorkDir

	out, err := cmd.CombinedOutput()
	outputStr := string(out)
	if len(outputStr) > 15000 {
		outputStr = outputStr[:15000] + "\n...[TRUNCATED]"
	}

	if err != nil {
		publishRes(client, nodeID, taskID, "error", err.Error()+"\n"+outputStr)
	} else {
		publishRes(client, nodeID, taskID, "success", outputStr)
	}
}

func publishRes(client mqtt.Client, nodeID, taskID, status, output string) {
	res := map[string]string{"task_id": taskID, "status": status, "output": output}
	payload, _ := json.Marshal(res)
	client.Publish(fmt.Sprintf("omninode/nodes/%s/result/%s", nodeID, taskID), 1, false, payload)
}
