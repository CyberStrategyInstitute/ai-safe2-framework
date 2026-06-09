# install-option3-system-prompt.ps1
# Option 3: Inject governance system prompt into Antigravity global config
# Effect: Governance prompt is present in context before ANY tool execution.
# Rollback: Script creates a dated backup before modifying — restore from backup.

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host "  🛡️  AI SAFE²  //  SYSTEM PROMPT INJECTOR (Option 3)       " -ForegroundColor DarkYellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkRed
Write-Host ""

# ─── Load governance prompt content ──────────────────────────────────────────

$promptSource = Join-Path $PSScriptRoot "governance-system-prompt.md"
if (-not (Test-Path $promptSource)) {
    Write-Host "[ERROR] governance-system-prompt.md not found at: $promptSource" -ForegroundColor Red
    Exit 1
}
$governancePrompt = Get-Content $promptSource -Raw
Write-Host "[✓] Governance prompt loaded ($([System.Text.Encoding]::UTF8.GetByteCount($governancePrompt)) bytes)" -ForegroundColor Green

# ─── Locate Antigravity config file ──────────────────────────────────────────

$configCandidates = @(
    "$env:USERPROFILE\.gemini\config\agent-config.json",
    "$env:USERPROFILE\.gemini\config\config.json",
    "$env:APPDATA\Antigravity\config\agent-config.json",
    "$env:APPDATA\Antigravity\config\config.json",
    "$env:LOCALAPPDATA\Antigravity\config\agent-config.json"
)

$configFile = $null
foreach ($candidate in $configCandidates) {
    if (Test-Path $candidate) {
        $configFile = $candidate
        Write-Host "[✓] Found Antigravity config: $configFile" -ForegroundColor Green
        break
    }
}

if (-not $configFile) {
    Write-Host ""
    Write-Host "[!] No existing config file found. Creating at default location." -ForegroundColor Yellow
    $configDir = "$env:USERPROFILE\.gemini\config"
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    $configFile = "$configDir\agent-config.json"
    '{"system_prompt": ""}' | Set-Content $configFile
    Write-Host "[✓] Created: $configFile" -ForegroundColor Green
}

# ─── Backup before modification ───────────────────────────────────────────────

Write-Host ""
Write-Host "[ 1/4 ] Creating backup..." -ForegroundColor Gray

$backupPath = "$configFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -Path $configFile -Destination $backupPath
Write-Host "        ✓ Backup saved: $backupPath" -ForegroundColor Green
Write-Host "        ROLLBACK: Copy-Item -Path '$backupPath' -Destination '$configFile' -Force" -ForegroundColor DarkGray

# ─── Read and update config ───────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 2/4 ] Reading current config..." -ForegroundColor Gray

$configContent = Get-Content $configFile -Raw
$config = $null

try {
    $config = $configContent | ConvertFrom-Json
} catch {
    Write-Host "        [WARN] Config is not valid JSON. Attempting recovery..." -ForegroundColor Yellow
    # If it's not JSON, treat as empty and start fresh
    $config = [PSCustomObject]@{}
}

# Check if governance block is already present
$existingPrompt = ""
if ($config.PSObject.Properties.Name -contains "system_prompt") {
    $existingPrompt = $config.system_prompt
}

if ($existingPrompt -like "*AI SAFE² Sovereign Governance*") {
    Write-Host "        [!] Governance block already present in system_prompt." -ForegroundColor Yellow
    Write-Host "            Replacing with current version..." -ForegroundColor Yellow
    # Strip existing governance block
    $existingPrompt = ($existingPrompt -replace "(?s)# AI SAFE² Sovereign Governance.*?\*AI SAFE² v3\.0.*?\*", "").Trim()
}

# ─── Build new system prompt ─────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 3/4 ] Injecting governance prompt..." -ForegroundColor Gray

$separator = if ($existingPrompt) { "`n`n---`n`n" } else { "" }
$newPrompt = "$existingPrompt$separator$governancePrompt".Trim()

# Update config object
$config | Add-Member -MemberType NoteProperty -Name "system_prompt" -Value $newPrompt -Force

# Serialize back to JSON with proper formatting
$updatedJson = $config | ConvertTo-Json -Depth 10
Set-Content -Path $configFile -Value $updatedJson -Encoding UTF8

$newSize = (Get-Item $configFile).Length
Write-Host "        ✓ Config updated ($newSize bytes)" -ForegroundColor Green

# ─── Verify injection ────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[ 4/4 ] Verifying injection..." -ForegroundColor Gray

$verifyContent = Get-Content $configFile -Raw
if ($verifyContent -like "*AI SAFE² Sovereign Governance*") {
    Write-Host "        ✓ Governance block confirmed in config" -ForegroundColor Green
} else {
    Write-Host "        [ERROR] Governance block NOT found after write — check config manually." -ForegroundColor Red
    Exit 1
}

if ($verifyContent -like "*HARD LIMITS*") {
    Write-Host "        ✓ Hard limits section confirmed" -ForegroundColor Green
}

if ($verifyContent -like "*ESCALATION PROTOCOL*") {
    Write-Host "        ✓ Escalation protocol confirmed" -ForegroundColor Green
}

# ─── Done ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  🛡️  SYSTEM PROMPT INJECTED SUCCESSFULLY                    " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Config   : $configFile" -ForegroundColor Gray
Write-Host "  Backup   : $backupPath" -ForegroundColor Gray
Write-Host "  Effect   : Governance constraints present in context window" -ForegroundColor Gray
Write-Host "             before any tool execution in every session." -ForegroundColor Gray
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor DarkYellow
Write-Host "  1. Restart Antigravity completely." -ForegroundColor Gray
Write-Host "  2. Start a new session and verify 🛡️ appears in init output." -ForegroundColor Gray
Write-Host "  3. Run: node smoke_test.js  to verify enforcement layer." -ForegroundColor Gray
Write-Host ""
Write-Host "  ROLLBACK:" -ForegroundColor DarkGray
Write-Host "  Copy-Item -Path '$backupPath' -Destination '$configFile' -Force" -ForegroundColor DarkGray
Write-Host ""
