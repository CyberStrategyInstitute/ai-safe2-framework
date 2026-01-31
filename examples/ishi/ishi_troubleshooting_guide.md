# Ishi Troubleshooting Guide (Windows 11)

**Quick fixes for common Ishi security issues on Windows**

**Platform:** Windows 11  
**Tested on:** i5-12500H, 16GB RAM

---

## CRITICAL ISSUES (Fix Immediately)

### Issue: Ishi Auto-Committing Ghost Files Without Approval

**Symptoms:**
- Files renamed/moved instantly
- No preview shown
- No "Approve/Reject" buttons

**Why this is critical:**
Bypasses core safety feature. Files can be deleted/overwritten without your knowledge.

**Fix 1: Via Ishi UI**
```
1. In Ishi: /config ghost_files
2. Set "Auto-commit": DISABLED
3. Set "Preview timeout": 3600 seconds
4. Enable "Require approval for all changes"
5. Save
6. Restart Ishi
```

**Fix 2: Via PowerShell (if UI inaccessible)**
```powershell
# Stop Ishi
Stop-Process -Name "ishi" -Force

# Edit config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Ensure safe defaults
if (-not $config.ghost_files) {
    $config | Add-Member -NotePropertyName "ghost_files" -NotePropertyValue @{} -Force
}
$config.ghost_files.auto_commit = $false
$config.ghost_files.preview_timeout_seconds = 3600
$config.ghost_files.require_approval = $true

# Save
$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8

# Restart
Start-Process "ishi"
```

**Verify fix:**
```
In Ishi: "Rename test.txt to test2.txt"
Expected: Preview shown, awaiting approval
```

---

### Issue: Exceeded Free Tier Token Limit

**Symptoms:**
- Ishi shows: "Daily limit reached"
- API errors in responses
- Provider shows: "Rate limit exceeded"

**Why this is critical:**
No more AI operations until tomorrow. Work blocked.

**Fix 1: Switch to backup provider**
```
In Ishi: /config providers

Priority order:
1. OpenRouter free (llama-3.1-8b) ← Add this
2. Gemini (if not exhausted)
3. Ishi Intent (if licensed)

Save and retry operation
```

**Fix 2: Manual provider switch**
```powershell
# Edit config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Set current provider to OpenRouter
$config.ai.current_provider = "openrouter"
$config.ai.openrouter.model = "meta-llama/llama-3.1-8b-instruct:free"

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

**Fix 3: Wait until tomorrow**
```
Token limits reset at:
- Gemini: 12:00 AM Pacific Time
- OpenRouter: Varies by model
- Ishi Intent: 12:00 AM your timezone

Check current time:
Get-Date
```

**Prevention:**
```powershell
# Set conservative daily limit
In Ishi: /config tokens
Max requests/day: 1,000 (leaves buffer)
Alert at: 750 requests (75%)
```

---

### Issue: Credentials Stored in Plaintext

**Symptoms:**
- Scanner reports: "Credentials stored in plaintext"
- Config.json contains `"api_key": "sk-ant-..."`
- Risk score: HIGH or CRITICAL

**Why this is critical:**
If your computer is compromised, attacker gets all your API keys.

**Fix: Migrate to Windows Credential Manager**
```powershell
# 1. Extract current keys from config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

$anthropicKey = $config.providers.anthropic.api_key
$geminiKey = $config.providers.google.api_key

# 2. Store in Windows Credential Manager
if ($anthropicKey -and $anthropicKey -ne '${WINDOWS_CREDENTIAL:Ishi_Anthropic_API_Key}') {
    cmdkey /generic:"Ishi_Anthropic_API_Key" /user:"ishi" /pass:"$anthropicKey"
    Write-Host "✓ Stored Anthropic key in Credential Manager"
}

if ($geminiKey -and $geminiKey -ne '${WINDOWS_CREDENTIAL:Ishi_Google_API_Key}') {
    cmdkey /generic:"Ishi_Google_API_Key" /user:"ishi" /pass:"$geminiKey"
    Write-Host "✓ Stored Gemini key in Credential Manager"
}

# 3. Update config to reference stored credentials
$config.providers.anthropic.api_key = '${WINDOWS_CREDENTIAL:Ishi_Anthropic_API_Key}'
$config.providers.google.api_key = '${WINDOWS_CREDENTIAL:Ishi_Google_API_Key}'

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8

Write-Host "✓ Config updated to use Credential Manager"

# 4. Restart Ishi
Stop-Process -Name "ishi" -Force
Start-Sleep -Seconds 2
Start-Process "ishi"

Write-Host "✓ Ishi restarted with secure credentials"
```

**Verify:**
```powershell
# Check credentials are stored
cmdkey /list | Select-String "Ishi"

# Should show:
# Target: Generic:Ishi_Anthropic_API_Key
# Target: Generic:Ishi_Google_API_Key
```

---

## HIGH-RISK ISSUES (Fix Within 24 Hours)

### Issue: Memory Protocol Not Loading

**Symptoms:**
- Ishi doesn't mention AI SAFE² when asked about safety
- Scanner reports: "Memory protocol not found"
- No permission slider enforcement

**Troubleshooting:**

**Step 1: Verify file exists**
```powershell
Test-Path "$env:APPDATA\ishi\memories\ishi_memory.md"
# Should return: True
```

**If False:**
```powershell
# Create memories directory
New-Item -Path "$env:APPDATA\ishi\memories" -ItemType Directory -Force

# Download protocol
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi_memory.md" -OutFile "$env:APPDATA\ishi\memories\ishi_memory.md"

# Verify
Get-Item "$env:APPDATA\ishi\memories\ishi_memory.md" | Select-Object Name,Length
# Should show ~19-20KB file
```

**Step 2: Check file encoding**
```powershell
# File must be UTF-8
$content = Get-Content "$env:APPDATA\ishi\memories\ishi_memory.md" -Raw
$content.Length
# Should be >15000 characters

# If file seems corrupted, re-download
Remove-Item "$env:APPDATA\ishi\memories\ishi_memory.md"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi_memory.md" -OutFile "$env:APPDATA\ishi\memories\ishi_memory.md"
```

**Step 3: Force Ishi reload**
```powershell
# Complete restart
Stop-Process -Name "ishi" -Force
Start-Sleep -Seconds 5

# Clear Ishi cache (if exists)
Remove-Item "$env:APPDATA\ishi\cache\*" -Recurse -Force -ErrorAction SilentlyContinue

# Restart
Start-Process "ishi"
```

**Step 4: Test**
```
In Ishi: "What's your safety protocol?"

Expected: Mentions AI SAFE², 5 pillars, permission slider
If not: Check Ishi logs for errors
```

---

### Issue: Scanner Can't Find Ishi Installation

**Symptoms:**
```
ERROR: Ishi path not found: C:\Users\user\.ishi
```

**Cause:** Ishi installed in non-standard location

**Fix 1: Let scanner auto-detect**
```powershell
# Search for Ishi
Get-ChildItem -Path $env:APPDATA -Filter "ishi" -Recurse -Directory -ErrorAction SilentlyContinue

# Or search entire user profile
Get-ChildItem -Path $env:USERPROFILE -Filter "ishi" -Recurse -Directory -ErrorAction SilentlyContinue | Select-Object FullName

# Note the correct path
```

**Fix 2: Run scanner with explicit path**
```powershell
python ishi-scanner.py --path "C:\Users\YourName\AppData\Roaming\ishi"

# Or wherever you found it in Fix 1
```

---

### Issue: Token Tracking Not Working

**Symptoms:**
- Ishi says "Token tracking disabled"
- Scanner reports: "No token usage tracking"
- Hit rate limits unexpectedly

**Fix: Create token tracking file**
```powershell
# Create tracking file
$tokenFile = "$env:APPDATA\ishi\token_usage.json"
$today = Get-Date -Format "yyyy-MM-dd"

$tokenData = @{
    date = $today
    providers = @{
        gemini = @{
            requests = 0
            limit = 1500
            percentage = 0
        }
        ishi = @{
            tokens = 0
            limit = 33333
            percentage = 0
        }
        openrouter = @{
            tokens = 0
            limit = 10000
            percentage = 0
        }
    }
}

$tokenData | ConvertTo-Json -Depth 10 | Out-File $tokenFile -Encoding UTF8

Write-Host "✓ Token tracking file created: $tokenFile"

# Enable tracking in config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

if (-not $config.tokens) {
    $config | Add-Member -NotePropertyName "tokens" -NotePropertyValue @{} -Force
}
$config.tokens.tracking_enabled = $true
$config.tokens.alert_threshold = 0.75

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8

Write-Host "✓ Token tracking enabled in config"

# Restart Ishi
Stop-Process -Name "ishi" -Force
Start-Process "ishi"
```

---

## MEDIUM-RISK ISSUES (Fix Within 1 Week)

### Issue: Permission Slider Not Configured

**Symptoms:**
- Ishi asks for approval on simple tasks (too restrictive)
- OR Ishi doesn't ask approval on dangerous tasks (too permissive)
- Scanner reports: "Permission level not configured"

**Fix:**
```
In Ishi: /config permissions

Recommended settings:
- Level: 2 (Associate)
- Ask for:
  ✓ File deletion
  ✓ Workflow execution
  ✓ Cloud data transfer
  ✗ File renaming (safe, allow auto)
  ✗ Folder creation (safe, allow auto)

Save and test
```

---

### Issue: Ishi Slow on Large File Operations

**Symptoms:**
- "Analyzing 100 files..." takes >5 minutes
- High memory usage (>4GB)
- CPU at 100%

**Cause:** Processing too many files at once, or using cloud AI for local operations

**Fix 1: Batch operations**
```
Instead of: "Analyze all files in Documents"
Do: "Analyze files in Documents/2024/ folder by folder"
```

**Fix 2: Use local processing where possible**
```
In Ishi config:
- Enable "Prefer local processing"
- File sorting: Use metadata (no AI)
- Text extraction: Use local OCR
- Only complex analysis: Use AI
```

**Fix 3: Increase resource limits**
```powershell
# Edit config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Increase batch size
$config.performance.max_concurrent_operations = 5
$config.performance.max_files_per_batch = 50

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

---

### Issue: Can't Connect to AgenticFlow

**Symptoms:**
- Ishi shows: "AgenticFlow connection failed"
- Workflows don't execute
- Error: "Authentication failed"

**Fix:**
```
1. Check AgenticFlow status: https://status.agenticflow.ai
2. Verify API key is valid:
   - Go to: https://app.agenticflow.ai/settings/api
   - Generate new key if needed
   
3. Update in Ishi:
   /config integrations
   AgenticFlow API key: [paste new key]
   Test connection
   
4. If still fails, check network:
   Test-NetConnection -ComputerName app.agenticflow.ai -Port 443
   # Should show: TcpTestSucceeded: True
```

---

## PERFORMANCE ISSUES

### Issue: High Memory Usage (>8GB)

**Symptoms:**
- Ishi using >8GB RAM
- System slows down
- Other apps crash

**Cause:** Large file processing, memory leaks, or too many operations cached

**Fix 1: Clear cache**
```powershell
# Stop Ishi
Stop-Process -Name "ishi" -Force

# Clear cache
Remove-Item "$env:APPDATA\ishi\cache\*" -Recurse -Force

# Restart
Start-Process "ishi"
```

**Fix 2: Limit memory usage**
```powershell
# Edit config
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Set memory limit (in MB)
$config.performance.max_memory_mb = 4096  # 4GB limit

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

**Fix 3: Process smaller batches**
```
Instead of: "Analyze 1,000 files"
Do: "Analyze first 100 files" (repeat as needed)
```

---

### Issue: Slow Startup (>30 seconds)

**Symptoms:**
- Ishi takes >30 seconds to launch
- Shows "Loading..." for extended time

**Causes:**
- Large memory protocol
- Many cached files
- Slow disk I/O

**Fix:**
```powershell
# Check disk speed
$disk = Get-PhysicalDisk | Where-Object {$_.FriendlyName -like "*SSD*"}
if ($null -eq $disk) {
    Write-Host "Warning: Not using SSD. Consider upgrading for better performance."
}

# Optimize Ishi directory
Optimize-Volume -DriveLetter C -Defrag -Verbose

# Clear old logs (>30 days)
$logsPath = "$env:APPDATA\ishi\logs"
Get-ChildItem $logsPath -Recurse -File | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Force

Write-Host "✓ Optimized Ishi directory"
```

---

## INTEGRATION ISSUES

### Issue: OpenClaw Delegation Failing

**Symptoms:**
- Ishi says: "Cannot reach OpenClaw"
- Tasks not delegated
- Timeout errors

**Troubleshooting:**

**Step 1: Verify OpenClaw is running**
```powershell
# If OpenClaw is in WSL2
wsl -d Ubuntu -- ps aux | Select-String openclaw

# If running natively on Windows
Get-Process | Where-Object {$_.ProcessName -like "*openclaw*"}
```

**Step 2: Test connection**
```powershell
# If OpenClaw gateway on localhost:18789
Test-NetConnection -ComputerName localhost -Port 18789

# Should show: TcpTestSucceeded: True
```

**Step 3: Check Ishi config**
```powershell
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Verify OpenClaw endpoint
Write-Host "OpenClaw endpoint: $($config.integrations.openclaw.endpoint)"
# Should be: http://localhost:18789 or http://127.0.0.1:18789

# If wrong, fix it:
$config.integrations.openclaw.endpoint = "http://localhost:18789"
$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

**Step 4: Test delegation**
```
In Ishi: "Test OpenClaw connection"
Expected: "✓ OpenClaw responding (v1.0.3)"
```

---

### Issue: AgenticFlow Workflow Validation Failing

**Symptoms:**
- All workflows blocked
- Error: "Workflow validation failed"
- Scanner shows: "Auto-execute enabled"

**Fix:**
```powershell
# Ensure validation is enabled but not overly restrictive
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

$config.integrations.agenticflow.validate_workflows = $true
$config.integrations.agenticflow.auto_execute = $false
$config.integrations.agenticflow.validation_level = "medium"  # Not "strict"

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8

Write-Host "✓ AgenticFlow validation configured for balanced security"
```

---

## WINDOWS-SPECIFIC ISSUES

### Issue: Windows Defender Blocking Ishi

**Symptoms:**
- Ishi won't start
- Windows shows: "Threat detected"
- Files quarantined

**Fix:**
```powershell
# Add Ishi to exclusions (run as Administrator)
Add-MpPreference -ExclusionPath "$env:APPDATA\ishi"
Add-MpPreference -ExclusionProcess "ishi.exe"

Write-Host "✓ Added Ishi to Windows Defender exclusions"

# Restore quarantined files
Start-Process "windowsdefender://threat/" -Verb RunAs
# Then manually restore Ishi files
```

---

### Issue: PowerShell Execution Policy Blocking Scripts

**Symptoms:**
- Scanner won't run
- Error: "Execution policy is restricted"
- Scripts show as blocked

**Fix:**
```powershell
# Check current policy
Get-ExecutionPolicy

# If "Restricted", change to RemoteSigned
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host "✓ PowerShell execution policy updated"

# Now retry scanner
python ishi-scanner.py
```

---

### Issue: Python Not Found

**Symptoms:**
- Scanner shows: "python is not recognized"
- Can't run Python scripts

**Fix:**
```powershell
# Install Python from Microsoft Store (easiest)
# Or check if it's installed but not in PATH

# Find Python
Get-Command python -ErrorAction SilentlyContinue

# If not found, add to PATH
$pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311"
if (Test-Path $pythonPath) {
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pythonPath", [EnvironmentVariableTarget]::User)
    Write-Host "✓ Added Python to PATH. Restart PowerShell."
}
```

---

## EMERGENCY PROCEDURES

### Emergency: Ishi Deleting Files Uncontrollably

**Immediate actions:**

**Step 1: STOP ISHI IMMEDIATELY**
```powershell
Stop-Process -Name "ishi" -Force
```

**Step 2: Check trash for deleted files**
```powershell
# Ishi trash
$trashPath = "$env:APPDATA\ishi\trash"
if (Test-Path $trashPath) {
    Get-ChildItem $trashPath -Recurse | Format-Table Name, LastWriteTime
}

# Windows Recycle Bin
# Open File Explorer → This PC → Recycle Bin
```

**Step 3: Disable auto-commit**
```powershell
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

$config.ghost_files.auto_commit = $false
$config.permissions.level = 1  # Set to Intern (ask everything)

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

**Step 4: Review logs**
```powershell
Get-Content "$env:APPDATA\ishi\logs\actions.jsonl" -Tail 100 | ConvertFrom-Json | Where-Object {$_.action -eq "delete"} | Format-Table timestamp, file, committed
```

**Step 5: Restore files**
```
In Ishi (after restarting):
/undo last 10 actions

Or manually:
Copy files from $env:APPDATA\ishi\trash\ back to original location
```

---

### Emergency: API Keys Compromised

**Immediate actions:**

**Step 1: Revoke all keys**
- Anthropic: https://console.anthropic.com/settings/keys
- Google: https://aistudio.google.com/apikeys
- OpenRouter: https://openrouter.ai/keys

Click "Delete" on all existing keys

**Step 2: Generate new keys**
Create new keys from same portals

**Step 3: Update Ishi securely**
```powershell
# Store new keys in Credential Manager (secure)
cmdkey /generic:"Ishi_Anthropic_API_Key" /user:"ishi" /pass:"NEW-sk-ant-key"
cmdkey /generic:"Ishi_Google_API_Key" /user:"ishi" /pass:"NEW-AIza-key"

# Update config to use Credential Manager
$configPath = "$env:APPDATA\ishi\config.json"
$config = Get-Content $configPath | ConvertFrom-Json

$config.providers.anthropic.api_key = '${WINDOWS_CREDENTIAL:Ishi_Anthropic_API_Key}'
$config.providers.google.api_key = '${WINDOWS_CREDENTIAL:Ishi_Google_API_Key}'

$config | ConvertTo-Json -Depth 10 | Out-File $configPath -Encoding UTF8
```

**Step 4: Check for unauthorized usage**
Review billing/usage on each provider's dashboard

---

## GETTING HELP

**If still stuck after trying fixes:**

1. **Check logs:**
```powershell
# Ishi main log
Get-Content "$env:APPDATA\ishi\logs\ishi.log" -Tail 50

# Action log
Get-Content "$env:APPDATA\ishi\logs\actions.jsonl" -Tail 20 | ConvertFrom-Json | Format-List
```

2. **Run scanner with verbose output:**
```powershell
python ishi-scanner.py --output detailed-report.txt
notepad detailed-report.txt
```

3. **Search existing issues:**
- Ishi: https://github.com/PixelML/ishi/issues
- AI SAFE²: https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues

4. **File new issue:**
Include:
- Windows version
- Ishi version
- Scanner output
- Relevant log excerpts (redact secrets!)
- What you were trying to do
- What actually happened

5. **Community help:**
- Ishi Discord: https://qra.ai/discord
- AI SAFE² Discussions: https://github.com/CyberStrategyInstitute/ai-safe2-framework/discussions

---

**Document Version:** 2.1  
**Last Updated:** January 30, 2026  
**Platform:** Windows 11  
**Maintained By:** Cyber Strategy Institute
