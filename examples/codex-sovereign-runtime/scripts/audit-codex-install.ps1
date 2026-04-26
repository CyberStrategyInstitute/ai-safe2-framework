[CmdletBinding()]
param(
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
        return (Join-Path $preferredRoot "audit-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt")
    } catch {
        $fallbackRoot = Join-Path (Get-Location) ".codex-runtime-logs"
        New-Item -ItemType Directory -Force -Path $fallbackRoot | Out-Null
        return (Join-Path $fallbackRoot "audit-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt")
    }
}

$ReportPath = Resolve-ReportPath
New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($ReportPath)) | Out-Null

$report = New-Object System.Collections.Generic.List[string]
$issues = 0

function Add-Report {
    param([string]$Line)
    $script:report.Add($Line)
    Write-Output $Line
}

Add-Report "AI SAFE2 Codex Installation Audit"
Add-Report "Generated: $((Get-Date).ToUniversalTime().ToString('o'))"
Add-Report "Host: $env:COMPUTERNAME"
Add-Report "User: $env:USERNAME"
Add-Report ""

$paths = & where.exe codex 2>$null
if ($paths) {
    Add-Report "--- Codex Binary Locations ---"
    foreach ($path in $paths) {
        Add-Report "Found: $path"
    }
    if (($paths | Measure-Object).Count -gt 1) {
        Add-Report "[WARN] Multiple Codex binary locations detected."
        $issues++
    }
    Add-Report ""
}

$command = Get-Command codex -ErrorAction SilentlyContinue
if ($command) {
    Add-Report "Resolved path: $($command.Source)"
    $versionOutput = & $command.Source "--version" 2>&1
    $versionLine = $versionOutput | Where-Object { $_ -match '^codex' } | Select-Object -First 1
    if ($versionLine) {
        Add-Report "Version: $versionLine"
    } else {
        Add-Report "[WARN] Unable to read codex version."
        $issues++
    }
} else {
    Add-Report "[WARN] codex command not found in current shell."
    $issues++
}
Add-Report ""

$configPaths = @(
    (Join-Path $HOME ".codex\config.toml"),
    (Join-Path (Get-Location) ".codex\config.toml")
)

Add-Report "--- Config Files ---"
foreach ($configPath in $configPaths) {
    if (Test-Path -LiteralPath $configPath) {
        Add-Report "Found: $configPath"
        $content = Get-Content -Raw -LiteralPath $configPath
        if ($content -match 'sandbox_mode\s*=\s*"danger-full-access"') {
            Add-Report "[WARN] danger-full-access found in $configPath"
            $issues++
        }
        if ($content -match 'approval_policy\s*=\s*"never"') {
            Add-Report "[WARN] approval_policy = never found in $configPath"
            $issues++
        }
        if ($content -match '\[mcp_servers\.') {
            Add-Report "[INFO] MCP definitions present in $configPath"
        }
    }
}
Add-Report ""

Add-Report "--- Shell Aliases And Functions ---"
$profilePath = $PROFILE.CurrentUserCurrentHost
if (Test-Path -LiteralPath $profilePath) {
    $profileContent = Get-Content -Raw -LiteralPath $profilePath
    if ($profileContent -match 'codex.*dangerously-bypass-approvals-and-sandbox') {
        Add-Report "[WARN] PowerShell profile contains dangerous Codex alias or wrapper."
        $issues++
    } else {
        Add-Report "No dangerous Codex alias found in $profilePath"
    }
} else {
    Add-Report "No PowerShell profile found at $profilePath"
}
Add-Report ""

Add-Report "Summary: issues=$issues"
$report | Set-Content -LiteralPath $ReportPath

if ($issues -gt 0) {
    exit 1
}

exit 0
