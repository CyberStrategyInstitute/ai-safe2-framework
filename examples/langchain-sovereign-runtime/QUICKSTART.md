# LangChain Sovereign Runtime — 15-Minute Quickstart

**AI SAFE² v3.0 | Cyber Strategy Institute**

---

## Prerequisites

- Python 3.9+
- pip
- LangChain project (existing or new)

---

## Step 1 — Clone and verify baseline (2 min)

```bash
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework
cd examples/langchain-sovereign-runtime
pip install -r requirements.txt
python smoke_test.py
# Expected: 15/15 — SOVEREIGN BASELINE VERIFIED
```

---

## Step 2 — Configure your ACT tier (2 min)

Copy `.env.example` to `.env` and set your tier:

```bash
cp .env.example .env
```

Edit `.env`:
```env
AISAFE2_ACT_TIER=ACT3           # ACT1 | ACT2 | ACT3 | ACT4
AISAFE2_ALLOWED_DOMAINS=api.openai.com,api.anthropic.com,your-api.com
AISAFE2_AUDIT_LOG_DIR=~/.ai_safe2/audit
```

**ACT tier guide:**
- `ACT1` / `ACT2` — development, human in the loop → log only
- `ACT3` — autonomous production → fail-closed (recommended)
- `ACT4` — orchestrator agents → fail-closed + HEAR gate

---

## Step 3 — Add to an existing chain (3 min)

**Option A — One callback line (no chain changes):**

```python
from enforcement import SovereignCallbackHandler, ACTTier

handler = SovereignCallbackHandler(act_tier=ACTTier.ACT3)

# Works with any LangChain chain, agent, or LCEL expression
result = chain.invoke(
    {"input": user_input},
    config={"callbacks": [handler]}
)

# Check status after run
print(handler.get_status())
```

**Option B — Full wrapper with tool protection:**

```python
from enforcement import SovereignLangChain, ACTTier

sovereign = SovereignLangChain(
    act_tier=ACTTier.ACT3,
    allowed_domains=["api.openai.com", "your-api.com"],
)

# Wrap tools with P1.T1.10 IPI scanning + P1.T2.3 domain allowlist
search_tool = sovereign.wrap_tool(your_search_tool)
file_tool   = sovereign.wrap_tool(your_file_tool)

# Wrap memory with S1.5 governance
sovereign.protect_memory(memory)

# Run with sovereign callbacks auto-injected
result = sovereign.run(chain, {"input": user_input})
```

---

## Step 4 — Register your agent identity (2 min)

Required for ACT-3/ACT-4 deployments (CP.4):

```python
sovereign.engine.register_nhi(
    agent_id="my-research-agent-prod-01",
    owner_of_record="your.name@company.com",
    act_tier=ACTTier.ACT3,
    tool_authorizations=["web_search", "read_file"],
    control_plane_id="langchain-prod-cp-001",
)
```

Fill out [core/IDENTITY.md](./core/IDENTITY.md) for your deployment record.

---

## Step 5 — Add the CI/CD gate (3 min)

Copy the GitHub Actions workflow to your repo:

```bash
cp ci-cd/github-actions-langchain-safe.yml \
   /path/to/your/repo/.github/workflows/
```

This runs `smoke_test.py` and the static validation on every PR.
The build fails if any adversarial scenario is not blocked.

---

## Step 6 — Verify (3 min)

```bash
bash validation/pass1_static.sh   # imports, config, policy.yaml integrity
bash validation/pass2_runtime.sh  # live enforcement + audit log verification
```

---

## That's It

| Surface | Control | Status |
|---|---|---|
| LLM input injection | P1.T1.2 | ✅ Blocked |
| IPI via tool returns | P1.T1.10 | ✅ Blocked |
| Credential leak | P1.T1.5 | ✅ Masked |
| Memory write poisoning | S1.5 | ✅ Gated |
| Agent recursion | F3.2 | ✅ Hard ceiling |
| Chain error cascade | F3.5 | ✅ Isolated |
| SSRF / private IP | P1.T2.3 | ✅ Blocked |
| Path traversal | P1.T1.2 | ✅ Blocked |
| Class-H actions | CP.10 | ✅ HEAR gated |
| Audit trail | A2.5 | ✅ SHA-256 chain |

---

*AI SAFE² v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com*
