# QUICKSTART -- 15-Minute Codex Sovereign Runtime v2 Setup

This guide deploys the highest-priority AI SAFE2 controls for Codex with the current Codex runtime surface.

Default deployment mode: **wrapper-first**.

Do **not** start by replacing your live global `~/.codex/config.toml` unless you are explicitly testing global integration on a non-production machine.

---

## Step 0: Check Your Installed Codex Version

```powershell
codex --version
where.exe codex
Get-Command codex | Format-List Source,Version
```

If `codex` resolves from more than one location, treat that as inventory drift and audit before continuing.

---

## Step 1: Install Monitoring And Governance Files

Install the external monitoring sink:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\\.codex" | Out-Null
New-Item -ItemType Directory -Force -Path "$HOME\\.codex\\monitoring" | Out-Null
Copy-Item ".\\monitoring\\codex-notify.ps1" "$HOME\\.codex\\monitoring\\codex-notify.ps1" -Force
```

Install the project governance files into the repo you want to protect:

```powershell
Copy-Item ".\\AGENTS.md" "C:\\path\\to\\your-project\\AGENTS.md" -Force
Copy-Item ".\\IDENTITY.md" "C:\\path\\to\\your-project\\IDENTITY.md" -Force
Copy-Item ".\\SOUL.md" "C:\\path\\to\\your-project\\SOUL.md" -Force
Copy-Item ".\\USER.md" "C:\\path\\to\\your-project\\USER.md" -Force
Copy-Item ".\\TOOLS.md" "C:\\path\\to\\your-project\\TOOLS.md" -Force
Copy-Item ".\\SUBAGENT-POLICY.md" "C:\\path\\to\\your-project\\SUBAGENT-POLICY.md" -Force
Copy-Item ".\\EVALUATION.md" "C:\\path\\to\\your-project\\EVALUATION.md" -Force
```

This is the project-local governance layer. It does not replace sandboxing or approvals; it shapes behavior and gives reviewers concrete artifacts to inspect.

---

## Step 2: Confirm The Codex Binary Path

On Windows, do not assume `codex` resolves from `PATH`.

```powershell
& "C:\Users\CyberStrategy1\AppData\Local\OpenAI\Codex\bin\codex.exe" --version
```

If that path differs on your machine, update the wrapper or use the detected path from:

```powershell
Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin"
```

---

## Step 3: Launch Codex Through The Wrapper

Do not launch high-trust sessions with raw `codex` when you want sovereign runtime controls. Use the wrapper:

```powershell
.\\scripts\\codex-jit-wrapper.ps1
```

Optional:

```powershell
.\\scripts\\codex-jit-wrapper.ps1 -Profile strict
.\\scripts\\codex-jit-wrapper.ps1 -SessionTimeoutSeconds 3600
.\\scripts\\codex-jit-wrapper.ps1 -AdditionalArgs @("--search")
```

The wrapper blocks dangerous startup flags, creates session logs, enforces a timeout, and injects a notification sink for external evidence.

Current Windows note: timeout enforcement may be disabled in favor of stable launch behavior. Use session review and CI gates as the stronger enforcement layer for now.

---

## Step 4: Audit Existing Codex Installations And Configs

```powershell
.\\scripts\\audit-codex-install.ps1
.\\scripts\\scan-dangerous-config.ps1
```

These scripts identify:

- multiple Codex binaries
- risky config values
- dangerous startup aliases
- over-broad MCP definitions
- unsafe approval or sandbox settings

---

## Step 5: Verify Monitoring

Run a short Codex session through the wrapper, exit, then summarize the session:

```powershell
.\\monitoring\\summarize-session.ps1
```

Expected outputs:

- a session log under `%USERPROFILE%\\.codex\\logs`
- a notification log entry
- a summary file you can retain as audit evidence
- if home-directory logging is blocked, fallback logs under `.codex-runtime-logs` in the workspace

---

## What You Just Deployed

| Control | What It Does |
|---|---|
| Governance files (`IDENTITY.md`, `SOUL.md`, `AGENTS.md`, `USER.md`, `TOOLS.md`, `SUBAGENT-POLICY.md`) | Define identity, constraints, tool surface, user data handling, and delegation rules |
| `codex-jit-wrapper.ps1` | Blocks dangerous launch flags, enforces approval/sandbox mode, injects notification logging |
| `audit-codex-install.ps1` | Inventories binaries, aliases, configs, and MCP surfaces |
| `scan-dangerous-config.ps1` | Flags unsafe approvals, sandbox modes, and config overrides |
| `codex-notify.ps1` | Captures external completion metadata for audit evidence |
| `EVALUATION.md` | Defines the verification model and known platform caveats |

---

## Emergency Response

If you suspect a Codex session operated unsafely:

```powershell
Get-Process codex -ErrorAction SilentlyContinue | Stop-Process -Force
.\\scripts\\audit-codex-install.ps1
.\\scripts\\scan-dangerous-config.ps1
.\\monitoring\\summarize-session.ps1
```

Then:

1. rotate any credentials that may have been exposed
2. review `%USERPROFILE%\\.codex\\logs`
3. revert or inspect untrusted file changes before merge or push

---

## Optional: Global Config Integration

If you explicitly want to test global Codex config integration, use files in `managed-settings/`, but treat that as advanced deployment. Validate on a non-production machine first.

*This quickstart documents the v2 wrapper-first deployment model.*
