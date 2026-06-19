# LangSmith Integration — AI SAFE² v3.0
## Combining LangSmith Tracing with Sovereign Enforcement

---

## Architecture

LangSmith provides observability. AI SAFE² provides enforcement. They are
complementary, not redundant:

| Concern | LangSmith | AI SAFE² A2.5 |
|---|---|---|
| Token counts, latency, LLM response quality | ✅ | ❌ |
| Prompt injection detection + blocking | ❌ | ✅ |
| Credential leak detection | ❌ | ✅ |
| Tool-call loop detection (F3.2 / M4.5) | ❌ | ✅ |
| Tamper-evident SHA-256 audit chain | ❌ | ✅ |
| HEAR gate enforcement (CP.10) | ❌ | ✅ |
| NHI identity registry (CP.4) | ❌ | ✅ |

**Run both.** LangSmith for product observability. AI SAFE² for security enforcement.

---

## Setup: Both Handlers

```python
import os
from enforcement import SovereignCallbackHandler, ACTTier

# LangSmith — set env vars (standard LangChain approach)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"]     = "ls__your-api-key"
os.environ["LANGCHAIN_PROJECT"]     = "my-project"

# AI SAFE² — explicit instantiation
sovereign_handler = SovereignCallbackHandler(act_tier=ACTTier.ACT3)

# Pass both — order matters:
# sovereign_handler fires first (enforcement before tracing)
result = chain.invoke(
    {"input": user_input},
    config={
        "callbacks": [
            sovereign_handler,   # ← AI SAFE² enforcement (first)
                                 # ← LangSmith auto-injects from env (second)
        ]
    }
)
```

---

## What LangSmith Traces Look Like With AI SAFE² Running

When AI SAFE² blocks an injection at ACT-3, LangSmith sees the raised
`AISAFE2Violation` exception and logs it as a chain error. This gives you:

1. The full LLM prompt that triggered the violation (LangSmith trace)
2. The exact P1.T1.2 injection pattern matched (AI SAFE² OCSF log)
3. The run_id linking the two logs (same UUID in both systems)

---

## Correlating run_id Across Both Systems

```python
import uuid
from langchain_core.callbacks import CallbackManagerForChainRun

# Explicitly set a run_id so LangSmith and AI SAFE² logs correlate
run_id = str(uuid.uuid4())

result = chain.invoke(
    {"input": user_input},
    config={
        "callbacks": [sovereign_handler],
        "run_id": uuid.UUID(run_id),
    }
)

# Now query LangSmith by run_id and cross-reference with:
audit_log = sovereign_handler.engine.audit_log_path
# Filter audit_log events where run_id == run_id
```

---

## Don't Send Violations to LangSmith

If AI SAFE² is running at ACT-3, violations raise exceptions before LangSmith
can capture the full payload — which is correct. You don't want blocked injections
or masked credentials appearing in your LangSmith project.

For ACT-1/ACT-2 deployments (log-only mode), violations are recorded in the AI SAFE²
OCSF log but the chain continues, so LangSmith does trace the full run. Keep LangSmith
project access controls tight in this case.

---

## LangSmith Dataset Eval + AI SAFE² Baseline

Running a LangSmith evaluation dataset? Add the sovereign handler to every eval run:

```python
from langsmith import Client
from enforcement import SovereignCallbackHandler, ACTTier

client = Client()
handler = SovereignCallbackHandler(act_tier=ACTTier.ACT2)  # log-only for evals

results = client.run_on_dataset(
    dataset_name="my-eval-dataset",
    llm_or_chain_factory=lambda: chain,
    # LangSmith accepts extra_tags, not callbacks directly in v0.1
    # Wrap your chain factory to inject the callback
)

# After eval: check if any examples triggered AI SAFE² violations
status = handler.get_status()
if status["total_violations"] > 0:
    print(f"⚠️  {status['total_violations']} AI SAFE² violations in eval dataset")
    print(handler.compliance_report())
```

---

## LangSmith API Key Security (P1.T1.5)

Your LangSmith API key (`ls__...`) is in `_CREDENTIAL_PATTERNS` in `ai_safe2_engine.py`.
If any chain output, tool return, or memory read contains your LangSmith key,
AI SAFE² will flag it as P1.T1.5.

Set keys via environment variables, not in code.

---

*AI SAFE² v3.0 | Cyber Strategy Institute | A2.5 Semantic Execution Trace Logging*
