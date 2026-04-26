# QUICKSTART -- 15-Minute Codex Sovereign Runtime Setup

This guide deploys the highest-priority AI SAFE2 controls for Codex with the current Codex runtime surface.

---

## Step 0: Check Your Installed Codex Version

```powershell
codex --version
where.exe codex
Get-Command codex | Format-List Source,Version
```

If `codex` resolves from more than one location, treat that as inventory drift and audit before continuing.

---

## Step 1: Install The Managed Codex Config

Back up your current user config, then copy a hardened baseline:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\\.codex" | Out-Null
Copy-Item "$HOME\\.codex\\config.toml" "$HOME\\.codex\\config.toml.bak" -ErrorAction SilentlyContinue
Copy-Item ".\\managed-settings\\config.strict.toml" "$HOME\\.codex\\config.toml" -Force
```

If you need team MCP servers, start from `managed-settings/config.team.toml` instead of weakening `config.strict.toml` ad hoc.

---

## Step 2: Install The Hardened Project Policy

Copy the Codex-focused `AGENTS.md` into the project you want to protect:

```powershell
Copy-Item ".\\AGENTS.md" "C:\\path\\to\\your-project\\AGENTS.md" -Force
```

This is the project-local behavioral policy layer. It does not replace sandboxing or approvals; it constrains the reasoning layer above them.

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

---

## What You Just Deployed

| Control | What It Does |
|---|---|
| `config.strict.toml` | Keeps Codex in `workspace-write` with `on-request` approvals and minimal MCP exposure |
| `AGENTS.md` | Hardens the reasoning layer against prompt injection and unsafe execution norms |
| `codex-jit-wrapper.ps1` | Blocks dangerous launch flags, adds timeout, injects notification logging |
| `audit-codex-install.ps1` | Inventories binaries, aliases, configs, and MCP surfaces |
| `scan-dangerous-config.ps1` | Flags unsafe approvals, sandbox modes, and config overrides |
| `codex-notify.ps1` | Captures external completion metadata for audit evidence |

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

*This quickstart is intentionally stricter than convenience defaults.*
