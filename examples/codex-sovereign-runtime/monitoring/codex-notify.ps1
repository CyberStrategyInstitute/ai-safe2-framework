$ErrorActionPreference = "Continue"

$logRoot = if ($env:CODEX_SOVEREIGN_LOG_ROOT) { $env:CODEX_SOVEREIGN_LOG_ROOT } else { Join-Path $HOME ".codex\logs" }
try {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
} catch {
    $logRoot = Join-Path (Get-Location) ".codex-runtime-logs"
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
}
$logPath = Join-Path $logRoot "notify.log"

$stdin = [Console]::In.ReadToEnd()
$timestamp = (Get-Date).ToUniversalTime().ToString("o")
$sessionId = if ($env:CODEX_SOVEREIGN_SESSION_ID) { $env:CODEX_SOVEREIGN_SESSION_ID } else { "unknown" }

Add-Content -LiteralPath $logPath -Value "$timestamp | session=$sessionId | payload=$stdin"
