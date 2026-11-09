[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-p]{32}$')]
    [string]$ExtensionId,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
$installer = Join-Path $PSScriptRoot 'install_windows.py'
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) { throw 'Installer missing.' }
$launcher = Get-Command py -ErrorAction SilentlyContinue
$pythonArgs = @()
if ($launcher) {
    $pythonArgs += '-3'
} else {
    $launcher = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $launcher) { throw 'Python 3 is required; no installation was attempted.' }
$pythonArgs += @($installer, '--extension-id', $ExtensionId, '--browser', 'chrome')
if ($Apply) { $pythonArgs += '--apply' }
& $launcher.Source @pythonArgs
if ($LASTEXITCODE -ne 0) { throw "Native host setup failed: $LASTEXITCODE" }
if (-not $Apply) { return }
$key = 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.omninode.desktop'
$manifestPath = (Get-Item -LiteralPath $key).GetValue('')
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$expectedOrigin = 'chrome-extension://' + $ExtensionId + '/'
if ($manifest.name -ne 'com.omninode.desktop' -or $manifest.type -ne 'stdio') { throw 'Unexpected native host manifest.' }
if (@($manifest.allowed_origins).Count -ne 1 -or $manifest.allowed_origins[0] -ne $expectedOrigin) { throw 'Native host origin mismatch.' }
if (-not (Test-Path -LiteralPath $manifest.path -PathType Leaf)) { throw 'Native host launcher missing.' }
Write-Output 'Chrome native host registration verified. Desktop activation and end-to-end operation are not yet verified.'
