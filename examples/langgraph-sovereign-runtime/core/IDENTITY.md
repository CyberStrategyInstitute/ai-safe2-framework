# Agent Identity Declaration — CP.4
## AI SAFE² v3.0 Agentic Control Plane Governance

This file is the Non-Human Identity (NHI) registration record for this agent.
Required for all ACT-3 and ACT-4 LangChain deployments.

Fill placeholders before deploying to production. The `register_nhi()` call
in your startup code should mirror the values here.

---

## NHI Record

| Field | Value |
|---|---|
| **Agent ID** | `[SET: your-agent-id-prod-01]` |
| **Runtime** | LangChain Sovereign Runtime v3.0 |
| **Owner of Record** | `[SET: owner.name@yourcompany.com]` |
| **ACT Tier** | `[SET: ACT3]` |
| **Control Plane ID** | `[SET: langchain-prod-cp-001]` |
| **Registered At** | `[SET: YYYY-MM-DDTHH:MM:SSZ]` |
| **Review Cadence** | Quarterly (minimum) |

---

## Authorized Tool Inventory — P1.T2.5

List every tool this agent is authorized to invoke. Unlisted tools must not run.

| Tool Name | Purpose | Domain Restriction | Max Calls/Session |
|---|---|---|---|
| `[TOOL_NAME]` | `[PURPOSE]` | `[allowed-domain.com]` | `[N]` |

---

## ACT Tier Justification — CP.3

**Declared Tier:** `[ACT-1 / ACT-2 / ACT-3 / ACT-4]`

**Rationale:**
- [ ] Human reviews all outputs before action (ACT-1)
- [ ] Agent acts with defined human checkpoints (ACT-2)
- [ ] Agent operates with post-hoc review (ACT-3)
- [ ] Agent controls other agents; HEAR required (ACT-4)

---

## HEAR Designation — CP.10

Required for ACT-3 and ACT-4:

| Field | Value |
|---|---|
| **HEAR Name** | `[SET: Full Name]` |
| **HEAR Contact** | `[SET: email + phone]` |
| **Kill Switch Authority** | Unilateral — no pre-approval required |
| **Response SLA** | 15 minutes for Class-H actions |

---

## Replication Authority — CP.9

- [ ] This agent **does not** have authority to spawn sub-agents
- [ ] This agent **does** have replication authority (requires CP.9 documentation)

Max delegation hops if replication is authorized: `[ACT-3: 2 / ACT-4: 3]`

---

## Code: Register This Agent at Startup

```python
from enforcement import AISAFE2Engine, ACTTier

engine = AISAFE2Engine(act_tier=ACTTier.ACT3)
engine.register_nhi(
    agent_id="your-agent-id-prod-01",
    owner_of_record="owner.name@yourcompany.com",
    act_tier=ACTTier.ACT3,
    tool_authorizations=["tool_name_1", "tool_name_2"],
    control_plane_id="langchain-prod-cp-001",
)
```

---

*AI SAFE² v3.0 | Cyber Strategy Institute | CP.4 Agentic Control Plane*
