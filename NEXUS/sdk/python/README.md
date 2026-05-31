# nexus-a2a-sdk

**NEXUS-A2A Python SDK** -- Cryptographic governance for agentic AI communication.

[![Version](https://img.shields.io/pypi/v/nexus-a2a-sdk)](https://pypi.org/project/nexus-a2a-sdk/)
[![License](https://img.shields.io/pypi/l/nexus-a2a-sdk)](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/nexus-a2a/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/nexus-a2a-sdk)](https://pypi.org/project/nexus-a2a-sdk/)

The Python SDK for the [NEXUS-A2A Protocol](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/nexus-a2a) -- the sovereign security layer for agentic AI that MCP, ACS, and A2A don't provide.

## Install

```bash
pip install nexus-a2a-sdk

# Full production stack (embeddings + OPA client + OpenTelemetry)
pip install "nexus-a2a-sdk[full]"
```

## What's Included

| Module | What it does |
|:-------|:-------------|
| `nexus_sdk.cael` | CAEL envelope, APEM message types, JouleWork economic accounting |
| `nexus_sdk.memory` | Memory Vaccine: injection detection, drift scoring, provenance |
| `nexus_sdk.guardian` | Guardian Integration Profile: per-call argument inspection |
| `nexus_sdk.otel` | NOR output receipts, OpenTelemetry/OCSF audit export |
| `nexus_sdk.agbom` | Dynamic Agent Bill of Materials: real-time, hash-chained |
| `nexus_sdk.bridges` | Protocol bridges: MCP, ACS, A2A, LangChain, CrewAI, n8n, REST |

## Quick Example

```python
from nexus_sdk.guardian import GuardianPolicy, NEXUSGuardianClient, build_tool_call_step

policy   = GuardianPolicy(blocked_argument_patterns=["../"])
guardian = NEXUSGuardianClient(inline_policy=policy,
                               fail_mode=NEXUSGuardianClient.FAIL_CLOSED)

step    = build_tool_call_step(
    agent_did="did:nexus:agent:my-agent",
    spiffe_id="spiffe://nexus.local/agent/my-agent",
    tool_name="read_file",
    tool_arguments={"path": "../../etc/passwd"},
    act_tier=2,
)
verdict = guardian.evaluate(step)
print(verdict.decision)   # deny
```

## Documentation

Full documentation, reference deployment, OPA policies, JSON schemas, and the IETF draft:
[github.com/CyberStrategyInstitute/ai-safe2-framework/nexus-a2a](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/nexus-a2a)

## License

Apache 2.0. See [LICENSE](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/nexus-a2a/LICENSE).
