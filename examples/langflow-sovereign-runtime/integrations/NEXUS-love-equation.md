# NEXUS Love Equation — Langflow Integration
## AI SAFE2 v3.0 | Cyber Strategy Institute

## The Proxy Architecture

Langflow has no Python callback to intercept. The enforcement pattern is:

```
External Client
      │
      ▼
┌─────────────────────┐
│  AI SAFE2 Proxy     │  ← scan_webhook_payload(), scan_run_request(),
│  (your API layer)   │    scan_global_var_headers()
└──────────┬──────────┘
           │ clean request only
           ▼
┌─────────────────────┐
│  Langflow API       │  ← /api/v1/webhook/, /api/v1/run/, /api/v1/predict/
│  :7860              │
└──────────┬──────────┘
           │ DAG execution
           ▼
┌─────────────────────┐
│  safe2_guardian     │  ← scan_component_output() inline DAG node
│  (inside the DAG)   │    between fetchers and Agent nodes
└─────────────────────┘
```

## Unified Score Pattern

```python
from enforcement.ai_safe2_engine import AISAFE2Engine
from enforcement.sovereign_langflow import LangflowSovereignRuntime

shared_engine = AISAFE2Engine(session_id="pipeline-001")
langflow_guard = LangflowSovereignRuntime()
langflow_guard._engine = shared_engine  # inject for unified score

status = shared_engine.get_status()
# {"love_score": 96.0, "alignment_band": "GREEN", "dag_hops": 3}
```

## Flow Run Boundary Pattern

```python
# At start of each flow run:
guard.reset_dag_state()

# Proxy: before webhook
guard.scan_webhook_payload(payload, flow_id)

# DAG: between components (via safe2_guardian_component.py)
guard.scan_component_output(output, "URLFetcher", position=1)
guard.scan_component_output(output, "Parser", position=2)

# After flow:
report = guard.compliance_report()
guard.reset_dag_state()
```

## Pipeline Gate

```python
status = guard.get_status()
if status["alignment_band"] != "GREEN":
    print(f"LANGFLOW GATE: {status['alignment_band']} — deployment blocked")
    sys.exit(1)
```
