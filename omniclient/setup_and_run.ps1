$ErrorActionPreference = "Stop"

Write-Host "[*] Impostazione variabili d'ambiente complete..." -ForegroundColor Cyan
$env:OMNINODE_MQTT_BROKER = "mqtt://localhost:1883"
$env:OMNINODE_NODE_ID = "omni-desktop-01"
$env:OMNINODE_AGENT_ID = "agent-desktop-01"
$env:OMNINODE_MQTT_USER = "omni"
$env:OMNINODE_MQTT_PASS = "omni"
$env:OMNINODE_WORKSPACE_ROOT = "C:\Users\ugopl\omninode-github\workspace"

# Passiamo valori dummy per soddisfare i controlli di buildTLSConfig in chiaro
$env:OMNINODE_MQTT_CA_PATH = "dummy"
$env:OMNINODE_MQTT_CERT_PATH = "dummy"
$env:OMNINODE_MQTT_KEY_PATH = "dummy"

Write-Host "[*] Compilazione di omniclient.exe..." -ForegroundColor Cyan
go build -o omniclient.exe .

Write-Host "[*] Avvio di omniclient.exe..." -ForegroundColor Green
.\omniclient.exe
