[CmdletBinding()]
param(
    [string]$Profile = "default",
    [int]$SessionTimeoutSeconds = 3600,
    [string[]]$AdditionalArgs = @()
)

$ErrorActionPreference = "Stop"

function Resolve-LogRoot {
    $preferred = Join-Path $HOME ".codex\logs"
    try {
        New-Item -ItemType Directory -Force -Path $preferred | Out-Null
        return $preferred
    } catch {
        $fallback = Join-Path (Get-Location) ".codex-runtime-logs"
        New-Item -ItemType Directory -Force -Path $fallback | Out-Null
        return $fallback
    }
}

function Write-Log {
    param(
        [string]$Path,
        [string]$Message
    )

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    Add-Content -LiteralPath $Path -Value "$timestamp | $Message"
}

$logRoot = Resolve-LogRoot
$monitoringRoot = Join-Path (Split-Path -Parent $logRoot) "monitoring"
New-Item -ItemType Directory -Force -Path $logRoot, $monitoringRoot | Out-Null

$sessionId = "codex-" + [guid]::NewGuid().ToString("N")
$sessionLog = Join-Path $logRoot "wrapper-sessions.log"
$summaryPath = Join-Path $logRoot "$sessionId.summary.txt"
$notifyScript = Join-Path $monitoringRoot "codex-notify.ps1"

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw "codex is not available in PATH."
}

$joinedArgs = ($AdditionalArgs -join " ")
if ($joinedArgs -match "--dangerously-bypass-approvals-and-sandbox") {
    throw "Blocked by AI SAFE2: dangerous bypass mode is not allowed."
}

if ($joinedArgs -match "--sandbox\s+danger-full-access") {
    throw "Blocked by AI SAFE2: danger-full-access is not allowed in the managed wrapper."
}

$configOverride = @(
    "-c", "notify=['powershell','-ExecutionPolicy','Bypass','-File','$notifyScript']"
)

$codexArgs = @()
if ($Profile) {
    $codexArgs += @("-p", $Profile)
}
$codexArgs += $configOverride
$codexArgs += $AdditionalArgs

$env:CODEX_SOVEREIGN_SESSION_ID = $sessionId
$env:CODEX_SOVEREIGN_SUMMARY_PATH = $summaryPath
$env:CODEX_SOVEREIGN_LOG_ROOT = $logRoot

Write-Log -Path $sessionLog -Message "SESSION_START | id=$sessionId | profile=$Profile | timeout=$SessionTimeoutSeconds | args=$joinedArgs"

try {
    $process = Start-Process -FilePath "codex" -ArgumentList $codexArgs -NoNewWindow -PassThru
    $completed = $process.WaitForExit($SessionTimeoutSeconds * 1000)

    if (-not $completed) {
        try {
            Stop-Process -Id $process.Id -ErrorAction Stop
        } catch {
        }
        Write-Log -Path $sessionLog -Message "SESSION_TIMEOUT | id=$sessionId | pid=$($process.Id)"
        throw "Blocked by AI SAFE2: Codex session exceeded timeout of $SessionTimeoutSeconds seconds."
    }

    $exitCode = $process.ExitCode
    Write-Log -Path $sessionLog -Message "SESSION_END | id=$sessionId | exit_code=$exitCode"
    "SessionId=$sessionId`nExitCode=$exitCode`nProfile=$Profile" | Set-Content -LiteralPath $summaryPath
    exit $exitCode
} finally {
}
