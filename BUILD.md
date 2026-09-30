# Build del Worker Go (Omninode)

Questo documento descrive come compilare il worker `omniclient.exe` per i due target hardware:

- **Desktop Ryzen:** Windows AMD64
- **Surface Pro 11:** Windows ARM64

## Prerequisiti

- Go 1.21 o superiore installato e nel PATH.
- Accesso a internet per scaricare le dipendenze Go.
- PowerShell o terminale Windows con permessi di scrittura nella cartella `omniclient/`.

## Passo 1: Prepara il modulo Go

```powershell
cd omniclient
go mod tidy
```

## Passo 2: Installa le dipendenze

```powershell
go get github.com/eclipse/paho.mqtt.golang
go get modernc.org/sqlite
go get github.com/playwright-community/playwright-go
go get github.com/gorilla/websocket
```

**Nota:** `modernc.org/sqlite` e' un driver SQLite puro Go, compatibile con `CGO_ENABLED=0` e Windows ARM.

## Passo 3: Build per Ryzen (AMD64)

```powershell
$env:CGO_ENABLED = "0"
$env:GOOS = "windows"
$env:GOARCH = "amd64"
go build -o omniclient-ryzen.exe .
```

## Passo 4: Build per Surface Pro 11 (ARM64)

```powershell
$env:CGO_ENABLED = "0"
$env:GOOS = "windows"
$env:GOARCH = "arm64"
go build -o omniclient-surface.exe .
```

## Passo 5: Deploy

1. Copia l'eseguibile appropriato (`omniclient-ryzen.exe` o `omniclient-surface.exe`) nella directory di destinazione.
2. Crea una cartella `certs/` con `ca.crt`, `client.crt`, `client.key` (generati da Mosquitto).
3. Imposta le variabili d'ambiente richieste:
   ```powershell
   $env:OMNI_WS_TOKEN = "token-lungo-almeno-32-caratteri"
   $env:OMNI_WS_ORIGINS = "http://127.0.0.1:8080"
   $env:OMNI_NODE_ID = "ryzen"  # o "surface"
   $env:OMNI_MQTT_BROKER = "tls://oracle-b.plini.net:8883"
   $env:OMNI_MQTT_CA = "certs/ca.crt"
   $env:OMNI_MQTT_CERT = "certs/client.crt"
   $env:OMNI_MQTT_KEY = "certs/client.key"
   ```
4. Avvia Chrome con debugging locale:
   ```powershell
   chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\omninode-chrome
   ```
5. Esegui il worker:
   ```powershell
   .\omniclient-ryzen.exe
   ```

## Risoluzione problemi

- **Errore `playwright-go`:** verifica di usare v0.4201.1 o superiore. Esegui `go mod tidy` e riprova.
- **Errore SQLite:** assicurati che `CGO_ENABLED=0` sia impostato prima della build.
- **Errore MQTT mTLS:** controlla percorsi e permessi dei certificati in `certs/`.
