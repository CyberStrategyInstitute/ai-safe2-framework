# QUICKSTART — Lovable Sovereign Runtime
## 5 Minutes to Sovereign Defense
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## Step 1: Verify Baseline

```bash
cd examples/lovable-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

## Step 2: Drop Security Rules Into Lovable

**Workspace Knowledge (highest impact — do this first):**

1. Open Lovable → Settings → Knowledge → Workspace knowledge
2. Paste the contents of `workspace-knowledge/ai-safe2-workspace-knowledge.md`
3. Save — rules apply immediately to all future messages in all projects

## Step 3: Integrate (pick your surface)

### Before Saving Workspace Knowledge
```python
from enforcement.sovereign_lovable import LovableSovereignRuntime

guard = LovableSovereignRuntime()

# Scan before saving to Settings → Knowledge
content = open("my-workspace-rules.md").read()
guard.scan_workspace_knowledge(content, scope="workspace")
# Raises ValueError on injection/secrets — safe to save if no exception
```

### Before Approving a Plan
```python
# Scan the plan text before clicking Approve
guard.scan_plan(plan_text, project_id="proj-abc123")
```

### Before query_database (MCP)
```python
sql = "SELECT * FROM orders WHERE user_id = $1"
guard.scan_sql_query(sql, project_id="proj-abc123")
# Blocks: DROP, TRUNCATE, ALTER, SECURITY DEFINER, RLS bypass, SQL injection
```

### Before MCP Client Connection
```python
guard = LovableSovereignRuntime(
    allowed_mcp_projects=["proj-dev-001", "proj-staging-002"]
)

guard.scan_mcp_scope(
    scopes=["projects:read", "database:read"],
    project_ids=["proj-dev-001"],
)
# Blocks: database:write, projects:delete, workspace:admin
# Blocks: projects outside the allowlist
```

### After Code Generation, Before Deploy
```python
generated_code = open("src/utils/processor.ts").read()
guard.scan_generated_code(generated_code, "processor.ts")
# Blocks: eval(), hardcoded keys, process.env leaks, child_process
```

### Before Subagent File Reads
```python
guard.scan_subagent_file_access(
    [".env.production", "src/components/Hero.tsx"],
    project_id="proj-abc123"
)
# Blocks: .env*, private keys, credentials.json, .aws/credentials
```

## Step 4: CI/CD Gate

```bash
# Copy to .github/workflows/
cp ci-cd/github-actions-lovable-gate.yml .github/workflows/
```

---

## What Users See on a Violation

```
!!! [AI SAFE2 LV.KNOW] [CRITICAL] Knowledge content BLOCKED — injection pattern detected
!!! [AI SAFE2 LV.SQL] [CRITICAL] SQL query BLOCKED — DROP TABLE detected (full DB permissions)
!!! [AI SAFE2 LV.BUILD] [CRITICAL] Generated code BLOCKED — eval() in 'src/utils/runner.ts'
!!! [AI SAFE2 LV.MCP] [CRITICAL] MCP scope BLOCKED — database:write is full-account scoped
!!! [AI SAFE2 LV.SUBAGENT] [HIGH] Subagent file access BLOCKED — '.env.production' is sensitive
```
