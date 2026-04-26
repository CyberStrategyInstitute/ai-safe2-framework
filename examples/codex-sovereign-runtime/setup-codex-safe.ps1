$ErrorActionPreference = "Stop"

$targetRoot = Join-Path $HOME ".codex"
$monitoringRoot = Join-Path $targetRoot "monitoring"
New-Item -ItemType Directory -Force -Path $targetRoot, $monitoringRoot | Out-Null

Copy-Item ".\managed-settings\config.strict.toml" (Join-Path $targetRoot "config.toml") -Force
Copy-Item ".\monitoring\codex-notify.ps1" (Join-Path $monitoringRoot "codex-notify.ps1") -Force

Write-Output "AI SAFE2 Codex setup complete."
Write-Output "Next step: launch .\scripts\codex-jit-wrapper.ps1"
