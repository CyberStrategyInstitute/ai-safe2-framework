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

function Resolve-CodexPath {
    $candidates = @()

    try {
        $cmd = Get-Command codex -ErrorAction Stop
        if ($cmd.Source) {
            $candidates += $cmd.Source
        }
    } catch {
    }

    $candidates += @(
        (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin\codex.exe"),
        "C:\Program Files\WindowsApps\OpenAI.Codex_26.422.3464.0_x64__2p2nqsd0c76g0\app\resources\codex.exe"
    )

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Write-Log {
    param(
        [string]$Path,
        [string]$Message
    )

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    try {
        Add-Content -LiteralPath $Path -Value "$timestamp | $Message"
    } catch {
        $fallbackDir = Join-Path (Get-Location) ".codex-runtime-logs"
        New-Item -ItemType Directory -Force -Path $fallbackDir | Out-Null
        $fallbackPath = Join-Path $fallbackDir (Split-Path -Leaf $Path)
        Add-Content -LiteralPath $fallbackPath -Value "$timestamp | $Message"
    }
}

$logRoot = Resolve-LogRoot
$monitoringRoot = Join-Path (Split-Path -Parent $logRoot) "monitoring"
New-Item -ItemType Directory -Force -Path $logRoot, $monitoringRoot | Out-Null

$sessionId = "codex-" + [guid]::NewGuid().ToString("N")
$sessionLog = Join-Path $logRoot "wrapper-sessions.log"
$summaryPath = Join-Path $logRoot "$sessionId.summary.txt"
$notifyScript = Join-Path $monitoringRoot "codex-notify.ps1"

function Write-Summary {
    param([string]$Content)

    try {
        Set-Content -LiteralPath $summaryPath -Value $Content
    } catch {
        $fallbackDir = Join-Path (Get-Location) ".codex-runtime-logs"
        New-Item -ItemType Directory -Force -Path $fallbackDir | Out-Null
        $fallbackSummary = Join-Path $fallbackDir (Split-Path -Leaf $summaryPath)
        Set-Content -LiteralPath $fallbackSummary -Value $Content
    }
}

$codexPath = Resolve-CodexPath
if (-not $codexPath) {
    throw "Unable to locate codex.exe. Use the local OpenAI Codex install path or refresh PATH in a new shell."
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
switch ($Profile) {
    "sovereign_strict" {
        $codexArgs += @("-a", "untrusted", "-s", "read-only")
    }
    default {
        $codexArgs += @("-a", "on-request", "-s", "workspace-write")
    }
}
$codexArgs += $configOverride
$codexArgs += $AdditionalArgs

$env:CODEX_SOVEREIGN_SESSION_ID = $sessionId
$env:CODEX_SOVEREIGN_SUMMARY_PATH = $summaryPath
$env:CODEX_SOVEREIGN_LOG_ROOT = $logRoot

Write-Log -Path $sessionLog -Message "SESSION_START | id=$sessionId | profile=$Profile | timeout=$SessionTimeoutSeconds | args=$joinedArgs"

try {
    Write-Log -Path $sessionLog -Message "SESSION_EXEC | id=$sessionId | codex_path=$codexPath | timeout_enforcement=disabled | mode=wrapper-first-v2"
    & $codexPath @codexArgs
    $exitCode = $LASTEXITCODE
    Write-Log -Path $sessionLog -Message "SESSION_END | id=$sessionId | codex_path=$codexPath | exit_code=$exitCode"
    Write-Summary -Content "SessionId=$sessionId`nExitCode=$exitCode`nProfile=$Profile"
    exit $exitCode
} finally {
}
