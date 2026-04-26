[CmdletBinding()]
param(
    [string]$SearchRoot = $HOME,
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

function Resolve-ReportPath {
    if ($ReportPath) {
        return $ReportPath
    }

    $preferredRoot = Join-Path $HOME ".codex\logs"
    try {
        New-Item -ItemType Directory -Force -Path $preferredRoot | Out-Null
        return (Join-Path $preferredRoot "config-scan-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt")
    } catch {
        $fallbackRoot = Join-Path (Get-Location) ".codex-runtime-logs"
        New-Item -ItemType Directory -Force -Path $fallbackRoot | Out-Null
        return (Join-Path $fallbackRoot "config-scan-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt")
    }
}

$ReportPath = Resolve-ReportPath
New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($ReportPath)) | Out-Null

$issues = 0
$warnings = 0
$lines = New-Object System.Collections.Generic.List[string]

function Add-Report {
    param([string]$Line)
    $script:lines.Add($Line)
    Write-Output $Line
}

Add-Report "AI SAFE2 Codex Config Scanner"
Add-Report "Scan root: $SearchRoot"
Add-Report "Report path: $ReportPath"
Add-Report ""

$files = Get-ChildItem -Path $SearchRoot -Recurse -Force -ErrorAction SilentlyContinue -Filter "config.toml" |
    Where-Object { $_.FullName -match "\\\.codex\\" -and $_.FullName -notmatch "\\node_modules\\" }

if (-not $files) {
    Add-Report "No .codex\\config.toml files found."
    $lines | Set-Content -LiteralPath $ReportPath
    exit 0
}

foreach ($file in $files) {
    $content = Get-Content -Raw -LiteralPath $file.FullName
    Add-Report "Checking: $($file.FullName)"

    if ($content -match 'dangerously-bypass-approvals-and-sandbox') {
        Add-Report "  [CRITICAL] Dangerous bypass startup flag referenced."
        $issues++
    }

    if ($content -match 'sandbox_mode\s*=\s*"danger-full-access"') {
        Add-Report "  [CRITICAL] sandbox_mode = danger-full-access"
        $issues++
    }

    if ($content -match 'approval_policy\s*=\s*"never"') {
        Add-Report "  [WARN] approval_policy = never"
        $warnings++
    }

    if ($content -match '\[features\][\s\S]*multi_agent\s*=\s*true') {
        Add-Report "  [WARN] multi_agent enabled. ACT-4 / CP.9 governance required."
        $warnings++
    }

    if ($content -match '\[mcp_servers\.') {
        Add-Report "  [INFO] MCP servers configured. Validate against allowlist."
    } else {
        Add-Report "  [INFO] No MCP servers configured."
    }

    Add-Report ""
}

Add-Report "Summary: critical=$issues warnings=$warnings"
$lines | Set-Content -LiteralPath $ReportPath

if ($issues -gt 0) {
    exit 1
}

exit 0
