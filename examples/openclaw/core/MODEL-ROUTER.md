# MODEL-ROUTER.md
# OpenClaw Model Routing Policy — AI SAFE² Standard

**Load context:** All sessions. Referenced by AGENTS.md and SUBAGENT-POLICY.md. Full routing config lives in `config/model-routing.json`; this file is the human-readable policy that governs it.  
**Governed by:** AI SAFE² Framework · Dual License MIT + CC-BY-SA  
**AI SAFE² Pillar:** S — Sanitize & Isolate (model tier = trust boundary)

---

## 1. Why Model Routing Matters for Governance

An agent that sends every request to the most capable model is not just expensive — it is a governance failure. Different models have different capability profiles, cost structures, data handling characteristics, and failure modes. Routing all tasks to Tier 1 means:

- Private context (USER.md, MEMORY.md) goes to external APIs when a local model could handle the task
- API costs scale with agent usage instead of with task complexity
- You cannot enforce data residency requirements for sensitive operations
- When the primary model is unavailable, the entire agent stops instead of gracefully degrading

This policy defines routing as a **security and governance control**, not just a performance optimization.

---

## 2. Model Tiers

### Tier 1 — Primary (Reasoning)

**Purpose:** Complex reasoning, sensitive decisions, anything touching the agent's identity files.  
**Examples:** Claude Opus, GPT-4o, Gemini Ultra  
**Configured in:** `config/model-routing.json → tier1`

**Route Tier 1 for:**
- Tasks that require SOUL.md alignment judgment
- Any action involving MEMORY.md or USER.md content
- Decisions with irreversible consequences
- Security incident assessment
- Tasks where the output will be acted on directly without human review
- Love Equation C/D band evaluation (Green/Yellow/Red determination)

**Do not use Tier 1 for:**
- Routine research or summarization
- Code generation that will be reviewed before use
- Sub-agent tasks unless the task explicitly requires Tier 1 capability

---

### Tier 2 — Worker (Efficient)

**Purpose:** Research, summarization, code review, data processing — tasks where quality matters but full reasoning depth is not required.  
**Examples:** Claude Sonnet, GPT-4o-mini, Gemini Flash  
**Configured in:** `config/model-routing.json → tier2`

**Route Tier 2 for:**
- Web research and document synthesis
- Code analysis, review, and generation (reviewed before use)
- Email drafting (reviewed before send)
- Data processing and transformation
- Most sub-agent tasks
- Summarization of internal documents

**Memory access:** Task-scoped only. Excerpt what's needed; never pass full MEMORY.md or USER.md.

---

### Tier 3 — Local (Offline / PII-Safe)

**Purpose:** Tasks that should not leave the local machine — PII-sensitive operations, offline capability, cost-zero operations.  
**Examples:** Ollama + Llama 3, LM Studio, Mistral local  
**Configured in:** `config/model-routing.json → tier3`

**Route Tier 3 for:**
- Operations involving PII that should not leave the local network
- Offline or air-gapped tasks
- High-volume, low-complexity classification or extraction
- Tasks where latency is acceptable and cost control is critical

**Important:** Local does not mean trusted. A local model with a poisoned system prompt is still dangerous. Trust level is determined by task scope and memory access, not deployment location.

**Memory access:** None by default. Local models never receive MEMORY.md or USER.md content unless explicitly authorized.

---

## 3. Routing Decision Matrix

| Task Type | Default Tier | Memory Access | Notes |
|---|---|---|---|
| SOUL/alignment judgment | Tier 1 | Full | Only tier that may evaluate alignment bands |
| MEMORY.md / USER.md operations | Tier 1 | Full | Never route to Tier 2/3 |
| Irreversible action decisions | Tier 1 | Full | Humans confirm; Tier 1 reasons |
| Security incident assessment | Tier 1 | Full | Requires full context |
| Research / web synthesis | Tier 2 | None | Sub-agent; task-scoped context only |
| Code review / generation | Tier 2 | None | Human reviews output before use |
| Email / message drafting | Tier 2 | None | Human reviews before send |
| PII-sensitive classification | Tier 3 | None | Stays local |
| High-volume extraction | Tier 3 | None | Cost control |
| Offline / air-gapped | Tier 3 | None | By design |

---

## 4. Failure Routing — Graceful Degradation

When a model tier is unavailable, the agent does not silently escalate or silently fail. It follows this cascade:

| Scenario | Behavior |
|---|---|
| Tier 1 unavailable | Stop sensitive/SOUL-bound tasks. Route non-sensitive tasks to Tier 2 with explicit notification to user. |
| Tier 2 unavailable | Attempt Tier 3 for compatible tasks. Notify user. Queue Tier 2-required tasks. |
| Tier 3 unavailable | Continue with Tier 2 for tasks that don't have data residency requirements. Log. |
| All tiers unavailable | Agent enters safe-hold mode. Notify user. Do not queue or retry silently. |

**The agent must never silently escalate a task to a higher tier than intended** — especially not escalating a Tier 3 (local/PII) task to Tier 1 (external API) because Tier 3 is unavailable. That is a data residency violation, not graceful degradation.

---

## 5. Multi-Model Prompt Stack

Some workspaces run a dual or multi-model prompt stack where different contexts use different models. Example:

| Context | Model | Prompt Stack |
|---|---|---|
| Main agent (DM, primary tasks) | Tier 1 primary | Root `.md` files |
| Sub-agents | Tier 2 worker | AGENTS.md excerpt + task brief |
| Coding agent | Tier 2 specialized | Code-focused system prompt |
| Fallback / offline | Tier 3 local | Minimal prompt — IDENTITY.md + task only |

**Switching the prompt stack requires a gateway restart.** Document stack switches in today's `memory/YYYY-MM-DD.md`.

---

## 6. Cost Controls

These limits are enforced at the gateway level (see `TOOLS.md → AI SAFE² Gateway Integration`). This policy file defines the intent; the gateway enforces it.

| Control | Default | Override |
|---|---|---|
| Max request size | 50,000 tokens | Workspace owner via config |
| Max response tokens | 4,000 | Task-specific override in spawn |
| Tier 1 sessions per hour | `<set per workspace>` | Workspace owner |
| Tier 2 sub-agent spawns per session | `<set per workspace>` | Workspace owner |
| Daily API cost ceiling | `<set per workspace>` | Workspace owner; alert at 80% |

If cost limits are approaching, the agent alerts the user before hitting the ceiling — not after.

---

## 7. Data Handling by Model Tier

| Concern | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| MEMORY.md access | Allowed (private sessions) | Never | Never |
| USER.md access | Allowed | Excerpt only | Never |
| PII in prompt | With user consent | Avoid | Preferred for PII tasks |
| Data leaves local network | Yes (external API) | Yes (external API) | No |
| Audit log entry required | Yes | Yes | Yes |
| Compliance applicable | All regulations | Most regulations | Local data only |

---

## 8. Announcing Model Usage

Per SUBAGENT-POLICY.md, whenever a sub-agent is spawned, the agent announces which model and provider are being used. This makes routing visible and auditable:

> "Spawning a sub-agent with Claude Sonnet via Anthropic API to research [topic]."

If the model used differs from what was announced (e.g., fallback triggered), note the actual model in the completion message.

---

## 9. config/model-routing.json Structure

The JSON config is the machine-readable version of this policy. It is what the gateway and routing layer actually read.

```json
{
  "tier1": {
    "model": "<model-id>",
    "provider": "<anthropic | openai | google>",
    "apiKeyEnvVar": "TIER1_API_KEY",
    "maxTokens": 4000,
    "allowedTaskTypes": ["soul_judgment", "memory_ops", "irreversible_decisions"]
  },
  "tier2": {
    "model": "<model-id>",
    "provider": "<anthropic | openai | google>",
    "apiKeyEnvVar": "TIER2_API_KEY",
    "maxTokens": 2000,
    "allowedTaskTypes": ["research", "code_review", "drafting", "summarization"]
  },
  "tier3": {
    "model": "<model-id>",
    "provider": "local",
    "endpoint": "http://localhost:11434",
    "maxTokens": 1000,
    "allowedTaskTypes": ["pii_classification", "offline", "high_volume"]
  },
  "fallback": {
    "tier1_unavailable": "tier2_non_sensitive",
    "tier2_unavailable": "tier3_compatible",
    "all_unavailable": "safe_hold"
  }
}
```

Changes to `model-routing.json` require a gateway restart and an entry in today's memory log.

---

*Part of the AI SAFE² OpenClaw Core File Standard.*
