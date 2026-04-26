[CmdletBinding()]
param(
    [string]$LogRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $LogRoot) {
    $preferred = Join-Path $HOME ".codex\logs"
    if (Test-Path -LiteralPath $preferred) {
        $LogRoot = $preferred
    } else {
        $LogRoot = Join-Path (Get-Location) ".codex-runtime-logs"
    }
}

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$summaryFile = Join-Path $LogRoot "latest-session-summary.txt"
$wrapperLog = Join-Path $LogRoot "wrapper-sessions.log"
$notifyLog = Join-Path $LogRoot "notify.log"

$out = New-Object System.Collections.Generic.List[string]
$out.Add("AI SAFE2 Codex Session Summary")
$out.Add("Generated: $((Get-Date).ToUniversalTime().ToString('o'))")
$out.Add("")

if (Test-Path -LiteralPath $wrapperLog) {
    $wrapperLines = Get-Content -LiteralPath $wrapperLog
    $out.Add("Wrapper events: $($wrapperLines.Count)")
    $out.Add("Last wrapper event: $($wrapperLines[-1])")
} else {
    $out.Add("Wrapper events: none")
}

if (Test-Path -LiteralPath $notifyLog) {
    $notifyLines = Get-Content -LiteralPath $notifyLog
    $out.Add("Notify events: $($notifyLines.Count)")
    $out.Add("Last notify event: $($notifyLines[-1])")
} else {
    $out.Add("Notify events: none")
}

$out | Set-Content -LiteralPath $summaryFile
$out
