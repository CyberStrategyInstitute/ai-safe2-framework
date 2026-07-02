# QUICKSTART — xAI/Grok Sovereign Runtime
## 5 Minutes to Sovereign Defense
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## Step 1: Install

```bash
cd examples/xai-grok-sovereign-runtime
# No pip install needed — enforcement/ is stdlib-only
```

## Step 2: Verify Baseline

```bash
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

## Step 3: Integrate (pick your surface)

### Interactive Session
```python
from enforcement.sovereign_xai_grok import GrokSovereignRuntime

guard = GrokSovereignRuntime()
guard.start_session("my-session-001")

# Every prompt through the guard
guard.scan_prompt("Review my code for security issues")
```

### Before Installing a Skill
```bash
# Validate any .md before adding to .grok/skills/
python3 - << 'EOF'
import sys
sys.path.insert(0, 'enforcement')
from sovereign_xai_grok import GrokSovereignRuntime

guard = GrokSovereignRuntime()
skill_content = open(sys.argv[1]).read()
try:
    guard.scan_skill_file(skill_content, sys.argv[1])
    print(f"SAFE: {sys.argv[1]} — ok to install")
except ValueError as e:
    print(f"BLOCKED: {e}")
    sys.exit(1)
EOF .grok/skills/myskill/SKILL.md
```

### Before Installing a Hook
```python
from pathlib import Path
from enforcement.sovereign_xai_grok import GrokSovereignRuntime

guard = GrokSovereignRuntime()

# Validate before writing to .grok/hooks/
hook_content = Path(".grok/hooks/pre-tool.sh").read_text()
guard.scan_hook_script(hook_content, event="before_tool_use")
```

### Multi-Agent Research
```python
guard.scan_multi_agent_request(
    prompt="Research post-quantum cryptography standards",
    tool_list=["web_search", "x_search"],   # NOT code_execution
    agent_count=4,                           # NOT 16 by default
)
```

### CI/CD Headless
```bash
# SAFE pattern (use this):
grok --permission-mode dontAsk --sandbox strict \
     --allow 'Bash(git status)' --allow 'Read' \
     --allow 'Bash(npm test)' \
     -p "Run tests and report failures"

# BLOCKED pattern (AI SAFE2 GK-HEAD will catch this):
# grok --always-approve -p "Run tests"   ← zero HITL, zero sandbox
```

## Step 4: Enterprise Config

Copy to `/etc/grok/requirements.toml` (root-owned):

```toml
[grok_com_config]
disable_api_key_auth = true
force_login_team_uuid = "YOUR-TEAM-UUID"

[ui]
disable_bypass_permissions_mode = true

[sandbox]
profile = "workspace"
```

## Step 5: CI/CD Gate

```yaml
# .github/workflows/ — see ci-cd/github-actions-xai-grok-gate.yml
```

Copy `ci-cd/github-actions-xai-grok-gate.yml` to `.github/workflows/`.
Pipeline fails if any test falls below GREEN.

---

## What Users See on a Violation

```
!!! [AI SAFE2 P1.T1.2] [CRITICAL] Injection in 'skill_file[evil.md]'
!!! [AI SAFE2 GK.PERM] [CRITICAL] always-approve in 'config.toml' must be in requirements.toml
!!! [AI SAFE2 GK.MULTI.TOOL] [CRITICAL] Dangerous server-side tool(s): ['code_execution']
!!! [AI SAFE2 GK.HEAD] [CRITICAL] Headless flag '--always-approve' bypasses all HITL
```

## Drop the AI SAFE2 Skill Into Grok

```bash
# Copy the skill to your .grok/skills/ directory
cp .grok/skills/ai-safe2/SKILL.md ~/.grok/skills/ai-safe2/SKILL.md
```

The `/ai-safe2 status` and `/ai-safe2 report` commands will be available in every Grok session.

---

## Next: Connect to the NEXUS Mesh

See `integrations/NEXUS-love-equation.md` to share one `AISAFE2Engine`
instance across all sovereign runtimes (LangChain, CrewAI, Make.com, Cursor)
for a unified Love Score and audit chain across your entire agentic stack.
