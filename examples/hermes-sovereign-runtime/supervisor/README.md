# Supervisor — Ishi Policy Agent

The `supervisor/` directory contains the Ishi supervisor agent configuration and its Open Policy Agent (OPA) policy ruleset.

## What Ishi Does

Ishi is the AI SAFE² judgment layer. It sits between operators and the Hermes agent core, enforcing policy decisions that Hermes cannot make about itself:

- **Tool approval gates** — High-risk tools route through Ishi before execution
- **Subagent governance** — All capability delegation decisions are policy-enforced
- **Cron authorization** — No unattended automation without explicit operator approval
- **Kill switch control** — Ishi broadcasts the kill signal across all instances
- **Alignment monitoring** — Love Equation scores gate operational autonomy bands

## Files

| File | Purpose |
|------|---------|
| `ishi_config.yaml` | Full Ishi configuration: thresholds, gates, HITL, audit settings |
| `policies/tool_approval.rego` | OPA policy: which tools require human approval |
| `policies/cron_governance.rego` | OPA policy: cron job creation and execution rules |
| `policies/subagent_scope.rego` | OPA policy: capability inheritance and memory isolation |

## OPA Integration

Ishi evaluates policies via OPA running as an external sidecar (port 8181). Policies are loaded at startup from `policies/` and hot-reloaded on change.

```bash
# Start OPA sidecar
docker run -d --name opa \
  -v $(pwd)/supervisor/policies:/policies \
  -p 8181:8181 \
  openpolicyagent/opa:latest run \
  --server /policies

# Query a policy decision
curl -X POST http://localhost:8181/v1/data/hsr/tool_approval/allow \
  -H "Content-Type: application/json" \
  -d '{"input": {"tool": "terminal", "parameters": {"yolo": false}, "alignment_score": {"E": 7.0, "I": 6.0}}}'
```

## Decision Flow

```
Hermes requests tool execution
        ↓
Ishi receives request
        ↓
OPA evaluates tool_approval.rego
        ↓
   ┌────┴────┐
allow?      deny?
   ↓           ↓
Check     Log + block
escalate?
   ↓
HITL queue → operator notified
   ↓
Operator approves / denies (5-min window)
   ↓
Ishi executes or blocks
```

## HITL Configuration

Configure operator notification channels in `.env`:

```bash
ISHI_SLACK_WEBHOOK=https://hooks.slack.com/...
ISHI_ALERT_EMAIL=ops@yourorg.com
ISHI_PD_KEY=your-pagerduty-key
```

## Customizing Policies

Policies are standard OPA/Rego. To add a new tool restriction:

```rego
# In tool_approval.rego
deny if {
    input.tool == "your_tool"
    input.parameters.risky_param == true
}
```

Test your policy changes before deploying:
```bash
opa test supervisor/policies/ -v
```

## Alignment Band Reference

| Band | E Score | I Score | Policy |
|------|---------|---------|--------|
| Green | ≥ 6.0 | ≥ 5.0 | Standard approval gates active |
| Yellow | ≥ 4.0 | ≥ 3.5 | All high-risk tools escalate to human |
| Red | < 4.0 | < 3.5 | Operations suspended; escalate immediately |

---
*Ishi: The judgment layer autonomous AI cannot provide for itself.*
