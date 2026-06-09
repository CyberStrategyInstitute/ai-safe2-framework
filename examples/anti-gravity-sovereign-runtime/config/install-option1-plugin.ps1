# install-option1-plugin.ps1
# Option 1: Install governance-enforcer as a native Antigravity plugin
# Effect: Governance constraints auto-load for EVERY session across ALL projects.
# Rollback: Remove the plugin directory from the plugins folder.

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host "  🛡️  AI SAFE²  //  GOVERNANCE PLUGIN INSTALLER (Option 1)" -ForegroundColor DarkYellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host ""

# ─── Locate Antigravity plugin directory ──────────────────────────────────────

$pluginDirs = @(
    "$env:USERPROFILE\.gemini\config\plugins",
    "$env:APPDATA\Antigravity\plugins",
    "$env:LOCALAPPDATA\Antigravity\plugins"
)

$targetPluginRoot = $null

foreach ($dir in $pluginDirs) {
    if (Test-Path $dir) {
        $targetPluginRoot = $dir
        Write-Host "[✓] Found Antigravity plugin directory: $dir" -ForegroundColor Green
        break
    }
}

if (-not $targetPluginRoot) {
    # Fall back to creating the most likely path
    $targetPluginRoot = "$env:USERPROFILE\.gemini\config\plugins"
    Write-Host "[○] Plugin directory not found — creating: $targetPluginRoot" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetPluginRoot -Force | Out-Null
}

$targetPlugin = Join-Path $targetPluginRoot "governance-enforcer"

# ─── Backup existing plugin if present ───────────────────────────────────────

if (Test-Path $targetPlugin) {
    $backupPath = "$targetPlugin.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Host "[○] Backing up existing plugin to: $backupPath" -ForegroundColor Yellow
    Copy-Item -Path $targetPlugin -Destination $backupPath -Recurse -Force
}

# ─── Copy plugin files ────────────────────────────────────────────────────────

$sourcePlugin = Join-Path $PSScriptRoot "..\plugins\governance-enforcer"
if (-not (Test-Path $sourcePlugin)) {
    Write-Host "[ERROR] Source plugin directory not found: $sourcePlugin" -ForegroundColor Red
    Write-Host "        Run this script from the repo's config/ directory." -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "[ 1/3 ] Copying plugin files..." -ForegroundColor Gray
Copy-Item -Path $sourcePlugin -Destination $targetPlugin -Recurse -Force

$copiedFiles = Get-ChildItem -Path $targetPlugin -Recurse -File
foreach ($f in $copiedFiles) {
    $rel = $f.FullName.Replace($targetPlugin, "").TrimStart('\')
    Write-Host "        ✓ $rel" -ForegroundColor Green
}

# ─── Verify plugin.json is readable ──────────────────────────────────────────

Write-Host ""
Write-Host "[ 2/3 ] Verifying plugin manifest..." -ForegroundColor Gray

$pluginJson = Join-Path $targetPlugin "plugin.json"
if (Test-Path $pluginJson) {
    $manifest = Get-Content $pluginJson | ConvertFrom-Json
    Write-Host "        ✓ Name:     $($manifest.name)" -ForegroundColor Green
    Write-Host "        ✓ Version:  $($manifest.version)" -ForegroundColor Green
    Write-Host "        ✓ AutoLoad: $($manifest.autoLoad)" -ForegroundColor Green
} else {
    Write-Host "        [ERROR] plugin.json not found after copy." -ForegroundColor Red
    Exit 1
}

# ─── Write install receipt ────────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 3/3 ] Writing install receipt..." -ForegroundColor Gray

$receipt = @{
    installedAt    = (Get-Date).ToString("o")
    pluginVersion  = $manifest.version
    installedTo    = $targetPlugin
    installedFrom  = $sourcePlugin
    installedBy    = $env:USERNAME
    rollbackCmd    = "Remove-Item -Path '$targetPlugin' -Recurse -Force"
}
$receipt | ConvertTo-Json | Set-Content (Join-Path $targetPlugin "install-receipt.json")
Write-Host "        ✓ Receipt written" -ForegroundColor Green

# ─── Done ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  🛡️  GOVERNANCE PLUGIN INSTALLED SUCCESSFULLY               " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $targetPlugin" -ForegroundColor Gray
Write-Host "  Effect   : Governance constraints load automatically for every" -ForegroundColor Gray
Write-Host "             Antigravity session across all projects." -ForegroundColor Gray
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor DarkYellow
Write-Host "  1. Restart Antigravity to pick up the new plugin." -ForegroundColor Gray
Write-Host "  2. Open any workspace and verify 🛡️ appears in session init." -ForegroundColor Gray
Write-Host "  3. Run: node smoke_test.js  to verify enforcement layer." -ForegroundColor Gray
Write-Host ""
Write-Host "  ROLLBACK:" -ForegroundColor DarkGray
Write-Host "  Remove-Item -Path '$targetPlugin' -Recurse -Force" -ForegroundColor DarkGray
Write-Host ""
