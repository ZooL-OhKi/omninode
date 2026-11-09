param(
  [string]$Token = "",
  [int]$Port = 8765,
  [int]$Ttl = 86400,
  [switch]$NoTunnel
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
  $rng.GetBytes($bytes)
  $rng.Dispose()
  $Token = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

$env:OMNI_CONTROL_TOKEN = $Token
$env:OMNI_CONTROL_PORT = "$Port"
$env:OMNI_CONTROL_TTL = "$Ttl"

$root = Split-Path -Parent $PSScriptRoot
$serverPath = Join-Path $root "desktop\desktop_control_server.py"

if (-not (Test-Path $serverPath)) {
  throw "File server non trovato: $serverPath"
}

$server = Start-Process -FilePath "python" -ArgumentList "`"$serverPath`"" -PassThru -WindowStyle Hidden

$ok = $false
for ($i = 0; $i -lt 50; $i++) {
  try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
    if ($response.ok) { $ok = $true; break }
  } catch {}
  Start-Sleep -Milliseconds 200
}

if (-not $ok) {
  throw "Control server non raggiungibile su http://127.0.0.1:$Port/health"
}

$url = $null
if (-not $NoTunnel) {
  $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($cloudflared) {
    $log = Join-Path $env:TEMP "omninode-cloudflared.log"
    if (Test-Path $log) { Remove-Item $log -Force }
    $tunnel = Start-Process -FilePath $cloudflared.Source -ArgumentList @(
      "tunnel",
      "--url", "http://127.0.0.1:$Port",
      "--logfile", $log,
      "--logfile-level", "info"
    ) -PassThru -WindowStyle Hidden

    for ($i = 0; $i -lt 100; $i++) {
      Start-Sleep -Milliseconds 300
      if (Test-Path $log) {
        $content = Get-Content $log -Raw
        if ($content -match "https://[a-z0-9-]+\.trycloudflare\.com") {
          $url = $Matches[0]
          break
        }
      }
    }
  }
}

[pscustomobject]@{
  token = $Token
  port = $Port
  url = $url
  server_pid = $server.Id
  tunnel_pid = if ($tunnel) { $tunnel.Id } else { $null }
} | ConvertTo-Json -Compress
