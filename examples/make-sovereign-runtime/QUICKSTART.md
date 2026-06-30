# QUICKSTART — Make.com Sovereign Runtime
## 5 Minutes to Sovereign Defense
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## Step 1: Verify Baseline

```bash
cd examples/make-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

## Step 2: Run the Scenario Simulation

```bash
PYTHONPATH=enforcement python3 examples/make_webhook_scenario.py
# Test 1: Clean order → [OK] all 3 modules → Love Score: 100.0 | Band: GREEN
# Test 2: Injected payload → [BLOCKED] at webhook gate
# Test 3: Restricted operation → [BLOCKED] at webhook gate
```

## Step 3: Integrate

```python
from enforcement.sovereign_make import MakeSovereignRuntime

guard = MakeSovereignRuntime(
    allowed_http_domains=["api.crm.example.com", "hooks.slack.com"],
    allowed_mcp_scenario_ids=[1001, 1002, 1003],
    max_ops_per_scenario_run=500,
    max_agent_turns=50,
)

# ── At start of each scenario run ──
guard.clear_external_context()

# ── Module 1: Webhook trigger (MK-WHK) ──
guard.scan_webhook_payload(payload_dict, source_id="whk-orders")

# ── Between modules (MK-SCEN) ──
guard.scan_module_output(output, module_name="AI Agent 1", module_position=3)

# ── HTTP module (MK-HTTP) ──
guard.scan_http_module("https://api.crm.example.com/contacts", "POST", body)

# ── Before saving agent instructions (MK-INST) ──
guard.scan_agent_instructions(instructions_text, agent_name="Sales Agent")

# ── Before uploading knowledge file (MK-KNOW) ──
guard.scan_knowledge_file(file_content, filename="brand-guide.md")

# ── Before MCP token connection (MK-MCP) ──
guard.scan_mcp_scope(["scenarios:read", "scenarios:run"], scenario_ids=[1001])

# ── Before Data Store write (MK-DS) ──
guard.scan_data_store_write("last_order_id", "ORD-42", store_name="scenario-state")
```

## Step 4: Drop the Security Skill Into Your Make AI Agent

Add the contents of `make-skill/ai-safe2-make.md` to your agent's
**Instructions** field in Make AI Agents. This establishes the trust
boundary within the agent's system prompt.

## Step 5: CI/CD Gate

```bash
cp ci-cd/github-actions-make-gate.yml .github/workflows/
```

---

## Alert Format

```
!!! [AI SAFE2 P1.T1.2]  [CRITICAL] Webhook payload 'whk-orders' BLOCKED — injection
!!! [AI SAFE2 MK.SCEN]  [CRITICAL] Module output 'AI Agent 1' BLOCKED — escalation
!!! [AI SAFE2 MK.HTTP]  [CRITICAL] HTTP POST to 'evil.io' BLOCKED — domain not allowed
!!! [AI SAFE2 MK.HTTP]  [CRITICAL] SSRF to private IP '192.168.1.1' BLOCKED
!!! [AI SAFE2 MK.INST]  [CRITICAL] Agent instructions BLOCKED — exfil instruction
!!! [AI SAFE2 MK.KNOW]  [CRITICAL] Knowledge file BLOCKED — injection in RAG content
!!! [AI SAFE2 MK.KNOW]  [HIGH]     Knowledge file BLOCKED — hidden Unicode U+200B
!!! [AI SAFE2 MK.MCP]   [CRITICAL] MCP scope BLOCKED — organizations:write
!!! [AI SAFE2 MK.DS]    [HIGH]     Data Store write BLOCKED — sensitive key 'api_key'
```
