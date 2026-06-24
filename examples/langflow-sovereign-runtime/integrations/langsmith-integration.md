# LangSmith Observability Integration
## AI SAFE2 v3.0 + Langflow | Cyber Strategy Institute

## AI SAFE2 + LangSmith: Complementary Evidence

AI SAFE2 sovereign runtime produces:
- SHA-256-chained JSONL for tamper-evident audit (P2 pillar)
- Love Score + band for compliance reporting (P5 pillar)
- Real-time CRITICAL events to stderr for SIEM (P4 pillar)

LangSmith (if deployed) provides:
- Token-level trace of each DAG component
- LLM prompt/response pairs for replay analysis
- Dataset + evaluation pipelines

Together they satisfy: pre-execution enforcement (AI SAFE2) + 
post-execution observability (LangSmith). Both are required for 
full compliance coverage.

## Integration Pattern

```python
# Configure LangSmith tracing
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"]    = "your-langsmith-key"
os.environ["LANGCHAIN_PROJECT"]    = "langflow-production"

# AI SAFE2 runs BEFORE Langflow processes the request
guard.scan_webhook_payload(payload, flow_id)
# → If clean, request proceeds to Langflow
# → LangSmith traces the Langflow execution
# → AI SAFE2 JSONL records the pre-execution decision

# Both audit trails are required for full coverage
```

## SIEM Forward Pattern

```bash
# Forward AI SAFE2 JSONL to Splunk alongside LangSmith traces:
tail -F reports/nexus-audit.jsonl | \
  curl -H "Authorization: Splunk $SPLUNK_TOKEN" \
       -H "Content-Type: application/json" \
       --data-binary @- \
       https://splunk.corp/services/collector/raw
```
