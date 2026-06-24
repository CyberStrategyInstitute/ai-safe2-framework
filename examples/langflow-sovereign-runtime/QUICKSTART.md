# QUICKSTART — Langflow Sovereign Runtime
## 5 Minutes to Sovereign Defense
**AI SAFE2 v3.0 | Cyber Strategy Institute**

---

## The Architecture (Read This First)

Langflow is a visual DAG builder. You cannot defend it with a Python
callback hook. Enforcement requires two layers:

**Layer 1 — External API Proxy** (before requests hit Langflow):
```python
from enforcement.sovereign_langflow import LangflowSovereignRuntime

guard = LangflowSovereignRuntime(
    allowed_global_var_keys=["OPENAI_API_KEY"],
    allowed_mcp_project_ids=["proj-safe-001"],
    webhook_auth_required=True,
)

# Before forwarding any webhook POST:
guard.scan_webhook_payload(payload_dict, flow_id="abc123", has_auth=True)

# Before forwarding any /run or /predict request:
guard.scan_run_request(flow_id, input_data, tweaks, session_id)

# Before forwarding any X-LANGFLOW-GLOBAL-VAR-* headers:
guard.scan_global_var_headers(request.headers)
```

**Layer 2 — Inline DAG Node** (inside the flow, between components):
```
[URL Fetcher] → [AI SAFE2 Guardian] → [Agent Node]
```
Copy `langflow-component/safe2_guardian_component.py` → Langflow CustomComponent.

---

## Step 1: Verify Baseline

```bash
cd examples/langflow-sovereign-runtime
PYTHONPATH=enforcement python3 smoke_test.py
# Expected: 21/21 -- SOVEREIGN BASELINE VERIFIED
```

## Step 2: Secure MCP Before Enabling It

```bash
# In your Langflow .env file:
LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=false   # disable auto-exposure
LANGFLOW_AUTO_LOGIN=false                     # require authentication
```

Then explicitly enable MCP only for specific projects via:
Langflow UI → Project → Share → MCP Server → Edit Tools

## Step 3: Fix Session ID Sharing

```python
# UNSAFE (default): session_id = flow_id = all users share memory
# response = requests.post(f"/api/v1/run/{flow_id}", json={"input_value": msg})

# SAFE: unique session_id per user
import uuid
session_id = f"user-{user_id}-{uuid.uuid4()}"
guard.scan_run_request(flow_id, message, tweaks, session_id)
```

## Step 4: Scan Flow JSON Before Import

```python
# Before drag-and-drop import or API import:
with open("imported-flow.json") as f:
    guard.scan_flow_json(f.read(), "imported-flow.json")
# Blocks: CustomComponent with subprocess, eval(), API keys
```

## Step 5: CI/CD Gate

```bash
cp ci-cd/github-actions-langflow-gate.yml .github/workflows/
```

---

## Alert Format

```
!!! [AI SAFE2 LF.WHK]  [CRITICAL] Webhook payload 'flow-abc' BLOCKED — injection
!!! [AI SAFE2 P1.T2.5] [CRITICAL] LANGFLOW_DATABASE_URL redirect header blocked
!!! [AI SAFE2 LF.KNOW] [CRITICAL] Knowledge document 'guide.pdf' BLOCKED — injection
!!! [AI SAFE2 P1.T1.9] [CRITICAL] CustomComponent with subprocess in 'flow.json'
!!! [AI SAFE2 LF.MCP]  [CRITICAL] LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=true no allowlist
!!! [AI SAFE2 S1.6]    [HIGH]     Hidden Unicode U+200B in knowledge doc
!!! [AI SAFE2 LF.COMP] [CRITICAL] IPI in URL Fetcher output — blocked before Agent node
```
