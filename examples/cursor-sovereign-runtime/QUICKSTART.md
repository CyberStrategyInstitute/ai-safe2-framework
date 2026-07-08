# QUICKSTART — Cursor Sovereign Runtime
## 5 Minutes to Sovereign Defense
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## Step 1: Verify Baseline

```bash
cd examples/cursor-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

## Step 2: Highest-Impact First Actions (no code required)

**Action 1 — Pin Cursor version to 2.5+ via MDM**
Closes CVE-2026-26268 (CVSS 9.9), all 2025 MCP CVEs, .cursorignore bypass. One MDM push.

**Action 2 — Drop the sovereign rules file**
Copy `.cursor/rules/ai-safe2-sovereign.mdc` into your workspace.
This injects trust boundary rules into every Cursor context window.

**Action 3 — Block project-local MCP servers (TrustFall mitigation)**
Until Anysphere patches TrustFall, add to managed workspace settings:
```json
{ "cursor.mcp.disableProjectLocalServers": true }
```

## Step 3: Integrate

```python
from enforcement.sovereign_cursor import CursorSovereignRuntime

guard = CursorSovereignRuntime(
    allowed_mcp_servers=["github-mcp", "notion-mcp"],
    shell_command_allowlist=["git status", "npm test", "python -m pytest"],
    require_mcp_hitl=True,
)

# Before committing any .mdc rules file
guard.scan_rules_file(content, ".cursor/rules/my-rules.mdc")

# Before writing .cursor/mcp.json (CurXecute defense)
guard.scan_mcp_json(mcp_json_content, ".cursor/mcp.json")

# Before approving MCP registration (MCPoison defense)
guard.scan_mcp_server_registration("my-server", "npx my-mcp@1.0.0")

# Before processing repo files in agent context (CVE-2026-26268)
guard.scan_repo_file(readme_content, "README.md")

# Before shell command Auto-Run (CVE-2026-22708 builtins)
guard.scan_shell_command("npm test", context="agent")

# Before writing .cursorignore (CVE-2025-64110)
guard.scan_cursorignore(ignore_content)

# Before cloud agent dispatch
guard.scan_cloud_agent_task(task, repo_url="https://github.com/org/repo")

# Before MCP package install (CVE-2025-64106)
guard.scan_mcp_install("playwright-mcp", "npx @playwright/mcp@1.2.3")
```

## Step 4: CI/CD Gate

```bash
cp ci-cd/github-actions-cursor-gate.yml .github/workflows/
```

---

## Alert Examples

```
!!! [AI SAFE2 CU.RULES]   [CRITICAL] [CU.RULES.BACKDOOR] Backdoor instruction in 'standards.mdc'
!!! [AI SAFE2 CU.MCP]     [CRITICAL] [CU.MCP.CMDINJEC] Shell injection in .cursor/mcp.json
!!! [AI SAFE2 CU.TRUST]   [CRITICAL] [MCPoison] MCP 'legit-server' command changed since approval
!!! [AI SAFE2 CU.REPO]    [CRITICAL] [CU.REPO.GIT_WRITE] .git/config write IPI in 'README.md'
!!! [AI SAFE2 CU.CMD]     [CRITICAL] [CU.CMD.ENVPOISON] export PATH poisoning blocked
!!! [AI SAFE2 CU.IGNORE]  [HIGH]     [CU.IGNORE.NEGATE_ENV] !.env bypass in .cursorignore
!!! [AI SAFE2 CU.SUPPLY]  [HIGH]     [CU.SUPPLY.UNPINNED] unpinned npx MCP install blocked
```
