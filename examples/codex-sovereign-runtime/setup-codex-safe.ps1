$ErrorActionPreference = "Stop"

$targetRoot = Join-Path $HOME ".codex"
$monitoringRoot = Join-Path $targetRoot "monitoring"
New-Item -ItemType Directory -Force -Path $targetRoot, $monitoringRoot | Out-Null

Copy-Item ".\monitoring\codex-notify.ps1" (Join-Path $monitoringRoot "codex-notify.ps1") -Force

Write-Output "AI SAFE2 Codex Sovereign Runtime v2 setup complete."
Write-Output "Installed: $HOME\.codex\monitoring\codex-notify.ps1"
Write-Output "Default deployment mode: wrapper-first."
Write-Output "Optional governance files should be copied into the target project root."
Write-Output "Next step: launch .\scripts\codex-jit-wrapper.ps1"
