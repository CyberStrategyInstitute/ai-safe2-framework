# Codex Sovereign Runtime v2 Evaluation

## Purpose

This file defines how to verify the Codex sovereign runtime in practice.

## Verification Targets

### 1. Launch Control

Expected:

- wrapper blocks dangerous bypass startup
- wrapper launches Codex with explicit approval and sandbox settings
- Codex executable resolution does not depend on `PATH` alone

Manual checks:

```powershell
& "C:\Users\CyberStrategy1\AppData\Local\OpenAI\Codex\bin\codex.exe" --version
powershell -ExecutionPolicy Bypass -File .\scripts\codex-jit-wrapper.ps1 -Profile sovereign
```

### 2. External Logging

Expected:

- `wrapper-sessions.log` created
- `notify.log` created when Codex emits notifications
- session summary written

Check:

- `C:\Users\<user>\.codex\logs`
- fallback `.codex-runtime-logs` in the workspace

### 3. Config Safety

Expected:

- scanner flags risky sandbox or approval settings
- audit script identifies binary drift and shell alias risk

Manual checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\audit-codex-install.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\scan-dangerous-config.ps1 -SearchRoot "C:\path\to\repos"
```

### 4. Governance File Presence

Expected in protected repos:

- `IDENTITY.md`
- `SOUL.md`
- `AGENTS.md`
- `USER.md`
- `TOOLS.md`
- `SUBAGENT-POLICY.md`

### 5. CI Enforcement

Expected:

- Codex invoked under explicit sandbox/approval settings
- no reliance on unsafe workstation defaults

## Known Platform Caveats

Observed during Windows validation:

1. `codex` may not resolve from `PATH` in all PowerShell sessions.
2. writes to `~/.codex/logs` may fail in constrained contexts.
3. global `~/.codex/config.toml` mutation is less reliable than wrapper-scoped controls.
4. `Start-Process` can fail because of duplicate `Path` / `PATH` environment handling.

These are design constraints for the package, not user mistakes.

## Maturity Levels

- `Level 1`: governance files present, audits runnable
- `Level 2`: wrapper launch working with external logs
- `Level 3`: CI enforcement active
- `Level 4`: optional post-run alignment scoring / drift review

## Next Optimization Layer

The next layer should borrow from `love_equation`:

- event schema for cooperative vs defective runtime behavior
- Green/Yellow/Red session trust bands
- drift scoring over repeated sessions
- escalation thresholds for high-risk actions

That should be implemented as a separate evaluation module, not merged into first-run workstation setup.
