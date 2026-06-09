# deploy.ps1 — AI SAFE² Antigravity Sovereign Runtime 1-Click Deployer
# Aligns with AI SAFE² CP.10 Sovereign Governance Deployment
# Version: 2.0

$Host.UI.RawUI.WindowTitle = "AI SAFE² — Antigravity Sovereign Runtime Deployer"
$ErrorActionPreference = "Stop"

Clear-Host

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host "  🛡️  AI SAFE²  //  AEGIS-ANTIGRAVITY SOVEREIGN RUNTIME v2.0  " -ForegroundColor DarkYellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host "  Target : Antigravity 2.0 Sovereign Agent Workspace"           -ForegroundColor Gray
Write-Host "  Profile: Full Sovereign Runtime (13-Scenario Verification)"   -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Detect Node Runtime (agy-node preferred, node fallback)
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "[ 1/4 ] Detecting runtime environment..." -ForegroundColor Gray

$nodeCmd = $null

# Check for agy-node in PATH
$agyInPath = Get-Command "agy-node" -ErrorAction SilentlyContinue
if ($agyInPath) {
    $nodeCmd = "agy-node"
    Write-Host "        ✓ Found agy-node in system PATH" -ForegroundColor Green
} else {
    # Check common Antigravity install locations
    $candidates = @(
        "$env:APPDATA\Antigravity\bin\agy-node.cmd",
        "$env:LOCALAPPDATA\Antigravity\bin\agy-node.cmd",
        "$env:ProgramFiles\Antigravity\bin\agy-node.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            $nodeCmd = $path
            Write-Host "        ✓ Found agy-node at: $path" -ForegroundColor Green
            break
        }
    }
}

# Fallback: standard Node.js
if (-not $nodeCmd) {
    $nodeInPath = Get-Command "node" -ErrorAction SilentlyContinue
    if ($nodeInPath) {
        $nodeCmd = "node"
        Write-Host "        ⚠ agy-node not found — using system Node.js" -ForegroundColor Yellow
        Write-Host "          Install Antigravity 2.0 for native agy-node support." -ForegroundColor DarkGray
    } else {
        Write-Host ""
        Write-Host "  [ERROR] Neither agy-node nor node found in PATH." -ForegroundColor Red
        Write-Host "          Install Antigravity 2.0 or Node.js 18+ before running this deployer." -ForegroundColor Red
        Exit 1
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Verify Directory Structure
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 2/4 ] Verifying sovereign directory structure..." -ForegroundColor Gray

$requiredDirs = @("core", "enforcement", "controls", "reports", "tests", "scripts")
$allGood = $true

foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $PSScriptRoot $dir
    if (Test-Path $fullPath) {
        Write-Host "        ✓ $dir/" -ForegroundColor Green
    } else {
        Write-Host "        ○ Creating $dir/" -ForegroundColor DarkGray
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}

$requiredFiles = @(
    "smoke_test.js",
    "enforcement/safe_gateway.js",
    "enforcement/circuit_breaker.js",
    "enforcement/audit_logger.js",
    "core/IDENTITY.md",
    "core/SOUL.md",
    "controls/policy.yaml"
)

Write-Host ""
Write-Host "        Checking required files..." -ForegroundColor DarkGray

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $PSScriptRoot $file
    if (Test-Path $fullPath) {
        Write-Host "        ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "        ✗ MISSING: $file" -ForegroundColor Red
        $allGood = $false
    }
}

if (-not $allGood) {
    Write-Host ""
    Write-Host "  [ERROR] Required files are missing. Cannot proceed." -ForegroundColor Red
    Write-Host "          Ensure the full repository is deployed before running." -ForegroundColor Red
    Exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Run Security Verification Suite
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 3/4 ] Running AI SAFE² Security Verification Suite..." -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host ""

$smokeTestPath = Join-Path $PSScriptRoot "smoke_test.js"
& $nodeCmd $smokeTestPath
$testExit = $LASTEXITCODE

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Final Status Report
# ─────────────────────────────────────────────────────────────────────────────

$elapsed = (Get-Date) - $startTime
$elapsedStr = "$([math]::Round($elapsed.TotalSeconds, 1))s"

Write-Host ""
Write-Host "[ 4/4 ] Deployment Summary" -ForegroundColor Gray
Write-Host ""
Write-Host "        Active Governance Files:" -ForegroundColor DarkGray
Write-Host "          core/IDENTITY.md    · core/SOUL.md" -ForegroundColor Gray
Write-Host "          core/GOVERNANCE.md  · core/TOOLS.md" -ForegroundColor Gray
Write-Host "          core/USER.md        · core/MEMORY.md" -ForegroundColor Gray
Write-Host ""
Write-Host "        Enforcement Layer:" -ForegroundColor DarkGray
Write-Host "          enforcement/safe_gateway.js   (P1+P4)" -ForegroundColor Gray
Write-Host "          enforcement/circuit_breaker.js (P3)" -ForegroundColor Gray
Write-Host "          enforcement/audit_logger.js    (P2)" -ForegroundColor Gray
Write-Host ""
Write-Host "        Verification Reports:" -ForegroundColor DarkGray
Write-Host "          reports/ai_safe2_compliance_report.md" -ForegroundColor DarkYellow
Write-Host "          reports/ai_safe2_evidence.json" -ForegroundColor DarkYellow
Write-Host "          reports/ai_safe2_results.sarif" -ForegroundColor DarkYellow
Write-Host ""

if ($testExit -eq 0) {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  🛡️  DEPLOYMENT STATUS: SECURE & FULLY COMPLIANT            " -ForegroundColor Green
    Write-Host "       Elapsed: $elapsedStr                                   " -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Exit 0
} else {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  🚨 DEPLOYMENT STATUS: COMPLIANCE GAPS DETECTED              " -ForegroundColor Red
    Write-Host "     Review test output above. Check enforcement/audit.log     " -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Exit 1
}
