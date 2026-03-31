# =============================================================================
# AI SAFE2 -- Pre-Tool-Use Hook (Windows PowerShell)
# Sovereign Runtime Governor: Input Sanitization & Injection Detection
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Deploy to: C:\ProgramData\Anthropic\ClaudeCode\hooks\pre-tool-use.ps1
# Exit 0 = allow, Exit 2 = block
# =============================================================================

param()

$ErrorActionPreference = "Stop"

$LogDir = if ($env:CLAUDE_CODE_LOG_DIR) { $env:CLAUDE_CODE_LOG_DIR } else { "$env:USERPROFILE\.claude\logs" }
$LogFile = Join-Path $LogDir "pre-tool-use.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read stdin
$Input = $null
try {
    $Input = [Console]::In.ReadToEnd()
} catch {
    # No input
    $Input = "{}"
}

# Parse JSON
$ToolData = $null
try {
    $ToolData = $Input | ConvertFrom-Json
} catch {
    # Non-JSON input -- allow and log
    Add-Content -Path $LogFile -Value "$Timestamp | PARSE_ERROR | raw=${Input.Substring(0, [Math]::Min(200, $Input.Length))}"
    exit 0
}

$ToolName = if ($ToolData.tool_name) { $ToolData.tool_name } else { "unknown" }
$BashCmd = if ($ToolData.tool_input.command) { $ToolData.tool_input.command } else { "" }
$FetchUrl = if ($ToolData.tool_input.url) { $ToolData.tool_input.url } else { "" }

Add-Content -Path $LogFile -Value "$Timestamp | ATTEMPT | tool=$ToolName | cmd=$($BashCmd.Substring(0, [Math]::Min(200, $BashCmd.Length)))"

function Block-WithReason {
    param([string]$Reason)
    Add-Content -Path $LogFile -Value "$Timestamp | BLOCKED | tool=$ToolName | reason=$Reason"
    Write-Host "BLOCKED by AI SAFE2 Sovereign Runtime Governor: $Reason"
    exit 2
}

# =============================================================================
# Bash / PowerShell / CMD command checks
# =============================================================================
if ($ToolName -eq "Bash" -and $BashCmd) {

    # Bypass mode activation
    if ($BashCmd -match 'dangerously.skip.permissions|bypass.permissions|yolo.mode') {
        Block-WithReason "Attempt to activate permission bypass mode"
    }

    # Pipe to shell
    if ($BashCmd -match '(curl|wget)[^|]*\|\s*(ba)?sh') {
        Block-WithReason "Pipe-to-shell pattern: curl/wget output piped to shell"
    }

    # Base64 decode pipe
    if ($BashCmd -match 'base64\s+-d[^|]*\|') {
        Block-WithReason "Base64-decode pipe: possible obfuscated command injection"
    }

    # Credential exfiltration
    if ($BashCmd -match '(env|printenv)[^;]*\|\s*(curl|wget|nc)') {
        Block-WithReason "Environment variable exfiltration pattern detected"
    }

    # Direct API key exfiltration
    if ($BashCmd -match '(ANTHROPIC_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN)[^;]*\|\s*(curl|wget)') {
        Block-WithReason "API key exfiltration attempt detected"
    }

    # Recursive deletion
    if ($BashCmd -match 'rm\s+-[rRf]{1,3}\s+[/~]($|\s)') {
        Block-WithReason "Recursive deletion of root or home directory"
    }

    # Reverse shell
    if ($BashCmd -match '(nc|netcat|socat)\s+.*(-e\s+|exec=)(ba)?sh') {
        Block-WithReason "Reverse shell pattern detected"
    }
}

# =============================================================================
# WebFetch checks
# =============================================================================
if ($ToolName -eq "WebFetch" -and $FetchUrl) {
    if ($FetchUrl -match '^data:') {
        Block-WithReason "data: URI fetch blocked"
    }
    if ($FetchUrl -match '^file://') {
        Block-WithReason "file:// URI blocked in WebFetch"
    }
}

# Allow
Add-Content -Path $LogFile -Value "$Timestamp | ALLOWED | tool=$ToolName"
exit 0
