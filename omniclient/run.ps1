$ErrorActionPreference = "Stop"

$env:OMNINODE_MQTT_BROKER = "mqtt://localhost:1883"
$env:OMNINODE_NODE_ID = "omni-desktop-01"
$env:OMNINODE_AGENT_ID = "agent-desktop-01"
$env:OMNINODE_MQTT_USER = "omni"
$env:OMNINODE_MQTT_PASS = "omni"
$env:OMNINODE_WORKSPACE_ROOT = "C:\Users\ugopl\omninode-github\workspace"

# Generazione certificati validi X.509 reali con Go per superare il parser PEM senza toccare il codice
$certDir = "C:\Users\ugopl\omninode-github\omniclient\certs"
if (!(Test-Path $certDir)) { New-Item -ItemType Directory -Path $certDir -Force | Out-Null }

if (!(Test-Path "$certDir\ca.pem")) {
    Write-Host "[*] Generazione certificati TLS validi per il test locale..." -ForegroundColor Cyan
    go run -e '
    package main
    import (
        "crypto/ecdsa"
        "crypto/elliptic"
        "crypto/rand"
        "crypto/x509"
        "crypto/x509/pkix"
        "encoding/pem"
        "math/big"
        "os"
        "time"
    )
    func main() {
        priv, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
        template := x509.Certificate{
            SerialNumber: big.NewInt(1),
            Subject: pkix.Name{CommonName: "localhost"},
            NotBefore: time.Now(),
            NotAfter: time.Now().Add(time.Hour),
            KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
            IsCA: true, BasicConstraintsValid: true,
        }
        der, _ := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
        certPem := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
        b, _ := x509.MarshalECPrivateKey(priv)
        keyPem := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: b})
        os.WriteFile("C:\\Users\\ugopl\\omninode-github\\omniclient\\certs\\ca.pem", certPem, 0644)
        os.WriteFile("C:\\Users\\ugopl\\omninode-github\\omniclient\\certs\\cert.pem", certPem, 0644)
        os.WriteFile("C:\\Users\\ugopl\\omninode-github\\omniclient\\certs\\key.pem", keyPem, 0600)
    }
    '
}

$env:OMNINODE_MQTT_CA_PATH = "$certDir\ca.pem"
$env:OMNINODE_MQTT_CERT_PATH = "$certDir\cert.pem"
$env:OMNINODE_MQTT_KEY_PATH = "$certDir\key.pem"

Write-Host "[*] Compilazione ed esecuzione..." -ForegroundColor Green
go run .
