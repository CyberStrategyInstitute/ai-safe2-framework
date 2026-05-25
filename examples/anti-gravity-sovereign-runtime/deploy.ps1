# deploy.ps1 - AI SAFE² Compliance Suite 1-Click Deployer
# Aligned with AI SAFE² Control CP.10 (Sovereign Governance Deployment)

$Host.UI.RawUI.WindowTitle = "AI SAFE² - Antigravity 1-Click Deployer"

Clear-Host
Write-Host "=============================================================" -ForegroundColor DarkRed
Write-Host "🛡️  AEGIS-ANTIGRAVITY // AI SAFE² 1-CLICK DEPLOYER v3.0" -ForegroundColor DarkYellow
Write-Host "=============================================================" -ForegroundColor DarkRed
Write-Host "Target: Antigravity 2.0 Sovereign Agent Workspace" -ForegroundColor Gray
Write-Host ""

# Step 1: Detect Host Environment Runtime
Write-Host "[*] Inspecting runtime prerequisites..." -ForegroundColor Gray
$agyNode = Get-Command "agy-node" -ErrorAction SilentlyContinue
if (-not $agyNode) {
    Write-Host "[!] Warning: 'agy-node' command was not found in global PATH." -ForegroundColor Yellow
    Write-Host "[*] Checking standard Roaming AppData directories..." -ForegroundColor Gray
    $roamingPath = "$env:APPDATA\Roaming\Antigravity\bin\agy-node.cmd"
    if (Test-Path $roamingPath) {
        Write-Host "[SUCCESS] Found native 'agy-node' engine at: $roamingPath" -ForegroundColor Green
        $script:exeCmd = $roamingPath
    } else {
        Write-Host "[ERROR] Could not resolve any local Electron-Node (agy-node) binary." -ForegroundColor Red
        Write-Host "        Please install the Antigravity 2.0 client before executing this deployer." -ForegroundColor Red
        Exit 1
    }
} else {
    Write-Host "[SUCCESS] Verified 'agy-node' system command integration." -ForegroundColor Green
    $script:exeCmd = "agy-node"
}

# Step 2: Initialize Directory Structure
Write-Host ""
Write-Host "[*] Initializing sovereign file structure..." -ForegroundColor Gray
$paths = @("core", "enforcement")
foreach ($p in $paths) {
    $fullPath = Join-Path $PSScriptRoot $p
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "    Created directory: $p" -ForegroundColor Gray
    } else {
        Write-Host "    Verified directory: $p" -ForegroundColor Gray
    }
}

# Step 3: Run the Verification Suite (Smoke Test)
Write-Host ""
Write-Host "=============================================================" -ForegroundColor DarkRed
Write-Host "[*] Executing Secure Sandbox Verification Tests..." -ForegroundColor DarkYellow
Write-Host "=============================================================" -ForegroundColor DarkRed
Write-Host ""

$testPath = Join-Path $PSScriptRoot "smoke_test.js"
& $script:exeCmd $testPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=============================================================" -ForegroundColor DarkRed
    Write-Host "🛡️  DEPLOYMENT STATUS: SECURE & FULLY COMPLIANT" -ForegroundColor Green
    Write-Host "=============================================================" -ForegroundColor DarkRed
    Write-Host "Aegis-Antigravity Sovereign Suite deployed in 1-click." -ForegroundColor Gray
    Write-Host "Workspace Hardened. Ledger generated." -ForegroundColor Gray
    Write-Host ""
    Write-Host "Active Files:" -ForegroundColor Gray
    Write-Host "  - Core Rules:       core/IDENTITY.md, core/SOUL.md, core/TOOLS.md" -ForegroundColor Gray
    Write-Host "  - External Shields: enforcement/safe_gateway.js, enforcement/circuit_breaker.js" -ForegroundColor Gray
    Write-Host "  - Compliance Audit: enforcement/ai_safe2_compliance_report.md" -ForegroundColor DarkYellow
    Write-Host ""
    Write-Host "Ready to share. Deployer successfully exited." -ForegroundColor Green
    Exit 0
} else {
    Write-Host ""
    Write-Host "🚨 DEPLOYMENT STATUS: COMPLIANCE FAILURE" -ForegroundColor Red
    Write-Host "Verification tests failed to execute properly. Sandbox breached." -ForegroundColor Red
    Exit 1
}
