$ErrorActionPreference = "Stop"
Set-Location "C:\Users\ugopl\omninode-github\omniclient"

Write-Host "[*] Ripristino pulito e applicazione patch..." -ForegroundColor Cyan

$env:OMNINODE_MQTT_BROKER = "mqtt://localhost:1883"
$env:OMNINODE_NODE_ID = "omni-desktop-01"
$env:OMNINODE_AGENT_ID = "agent-desktop-01"
$env:OMNINODE_WORKSPACE_ROOT = "C:\Users\ugopl\omninode-github\workspace"

# Rimuoviamo eventuali variabili TLS residue
Remove-Item Env:\OMNINODE_MQTT_CA_PATH -ErrorAction SilentlyContinue
Remove-Item Env:\OMNINODE_MQTT_CERT_PATH -ErrorAction SilentlyContinue
Remove-Item Env:\OMNINODE_MQTT_KEY_PATH -ErrorAction SilentlyContinue
Remove-Item Env:\OMNINODE_MQTT_USER -ErrorAction SilentlyContinue
Remove-Item Env:\OMNINODE_MQTT_PASS -ErrorAction SilentlyContinue

Write-Host "[*] Compilazione ed esecuzione..." -ForegroundColor Green
go run .
