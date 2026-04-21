# AI SAFE2 v3.0 Skill Evaluation Suite

Use these prompts and expected outputs to validate that the skill is functioning
correctly after any update to SKILL.md, skill-spec.md, or the MCP server.
Run manually or automate using the evals tool in your IDE.

---

## Eval 1: ACT Tier Classification — Orchestrator

**Input prompt:**
> I'm building an agent that manages 10 worker agents. Each worker can spawn
> temporary sub-agents for parallel processing. The system runs unattended overnight
> and has write access to our CRM and financial reporting systems.

**Expected output must include:**
- ACT-4 tier identification
- CP.10 HEAR designation flagged as required
- CP.9 Agent Replication Governance flagged as required (max 3 hops, 500ms kill-switch)
- CP.8 Catastrophic Risk Thresholds flagged as deployment condition
- F3.2 Recursion Limit Governor mentioned
- F3.3 Swarm Quorum Abort mentioned (or F3.5 cascade containment)
- A2.4 agent state inventory with owner_of_record required
- At least one compliance framework mapping (EU AI Act, SOC 2, or NIST AI RMF)

**Failure indicators:**
- No mention of HEAR
- No mention of CP.9
- ACT tier stated as ACT-2 or ACT-3

---

## Eval 2: Prompt Injection — Indirect Surface

**Input prompt:**
> My agent reads customer emails to extract action items, then searches our internal
> knowledge base, then calls a CRM API to update records. Is there a security concern?

**Expected output must include:**
- P1.T1.10 Indirect Injection Surface Coverage (emails and KB as injection surfaces)
- S1.3 Semantic Isolation Boundary Enforcement
- M4.5 Tool-Misuse Detection for the CRM API call
- A2.5 Semantic Execution Trace Logging for the full chain
- Mention of Class-H action classification for CRM write
- Specific recommendation that emails and KB content must be sanitized before inference

**Failure indicators:**
- Only mentions user input as the injection surface
- Does not mention indirect injection from retrieved content
- No control IDs cited

---

## Eval 3: Risk Score Calculation

**Input prompt:**
> We have CVE-2024-1234 (CVSS 8.5) in our LangGraph deployment. Our AI SAFE2
> pillar score is 55. The agent is ACT-3 with high autonomy, broad tool access,
> cross-session memory, and no human review for most actions. What's our risk?

**Expected output must include:**
- Combined Risk Score calculation shown with the formula
- CVSS component: 8.5
- Pillar component: (100-55)/10 = 4.5
- AAF discussed — at minimum the 10 AIVSS factors listed and their impact
- Score interpretation (likely CRITICAL or HIGH given the inputs)
- Recommendation to use pro tier for full AAF calculation if on free tier
- At least one specific control recommendation (F3.2, S1.5, M4.4 are likely candidates)

**Failure indicators:**
- No formula shown
- Risk stated as "high" without a numeric score
- No AAF factors mentioned

---

## Eval 4: Compliance Mapping — EU AI Act

**Input prompt:**
> Our legal team says we need to satisfy EU AI Act Article 14 for our autonomous
> scheduling agent. What does that require in practice?

**Expected output must include:**
- CP.10 HEAR Doctrine as the primary implementation of Art. 14 human oversight
- P4.T7.1 Human Approval Workflows
- CP.3 ACT tier classification as documentation requirement
- A2.5 execution trace logging as evidence artifact
- Specific mention that HEAR must be a named individual with cryptographic signing key
- At least one other control ID

**Failure indicators:**
- Only general description of EU AI Act without control IDs
- No mention of HEAR
- No code or implementation specifics

---

## Eval 5: Code Review — Secret in Prompt

**Input prompt:**
> Review this Python code:
> ```python
> api_key = os.getenv("OPENAI_KEY")
> prompt = f"You are an assistant. Use API key {api_key} to call external services."
> response = client.chat.completions.create(messages=[{"role":"user","content":prompt}])
> ```

**Expected output must include:**
- P1.T1.4_ADV NHI Secret Validation or P1.T2.9 Credential Compartmentalization
- S1.5 or P1.T1.5_ADV for sensitive data in context
- Severity: at minimum HIGH (CRITICAL acceptable)
- Corrected code that removes the API key from the prompt
- Mention that secrets in prompt context can be exposed via log leakage or model output
- At least one compliance framework (SOC 2, PCI-DSS, or ISO 27001)

**Failure indicators:**
- No control IDs cited
- Only describes the problem without providing corrected code
- Severity rated LOW or MEDIUM

---

## Eval 6: HEAR Doctrine Knowledge

**Input prompt:**
> What is the HEAR Doctrine and when is it required?

**Expected output must include:**
- Control ID CP.10
- "first in field" language or equivalent (no other framework has this)
- HEAR = named individual (not a team or role)
- Cryptographic signing key requirement
- Class-H action protocol (agent pauses, presents consequence, HEAR signs, agent verifies)
- Fail-closed: HEAR unreachable = action blocked, no automatic approval
- Required for ACT-3 and ACT-4
- At least two compliance mappings (EU AI Act Art 14, SOC 2 CC.7.4, GDPR Art 22, SEC)

**Failure indicators:**
- Describes HEAR as a team or approval workflow
- Does not mention cryptographic signing
- Does not mention fail-closed behavior
- No compliance framework mappings

---

## Eval 7: Agent Replication Gap (CP.9)

**Input prompt:**
> We're building an orchestrator that spawns worker agents dynamically based on task
> complexity. Sometimes workers spawn their own sub-workers. What governance standard
> applies to the replication chain?

**Expected output must include:**
- CP.9 Agent Replication Governance (ARG)
- "first in field" or "no other framework" language
- Lineage token requirement (parent DID, chain ID, delegation depth, TTL)
- Ephemeral credentials with scope narrowing at each hop
- Max delegation hops: 3 for ACT-4 (or 2 for ACT-3)
- 500ms kill-switch SLA for full tree severance
- A2.4 replication_lineage field requirement
- F3.3 Swarm Quorum Abort or F3.5 Cascade Containment as companion controls

**Failure indicators:**
- Recommends only standard IAM without replication-specific governance
- No lineage tracking mentioned
- No kill-switch tree severance requirement

---

## Eval 8: No-Code Platform Security

**Input prompt:**
> We've been building AI automation workflows in n8n for six months. Are there
> security concerns we should know about?

**Expected output must include:**
- S1.7 No-Code / Low-Code Platform Security
- CVE-2026-25049 or n8n sandbox escape series mentioned
- Credential exposure risk (platform stores credentials; sandbox escape exposes all)
- Specific S1.7 requirements: sandbox isolation, credential scoping, template supply chain
- Prompt injection surface (n8n AI nodes are injection surfaces too)
- Immediate action recommendation: audit existing workflows

**Failure indicators:**
- Generic "n8n has security risks" without control IDs
- No CVE mentioned
- No credential exposure risk explained

---

## Eval 9: Compliance Evidence Package

**Input prompt:**
> We're preparing for a SOC 2 Type II audit and the auditor is asking about our
> AI agent governance. What evidence do we need to produce?

**Expected output must include:**
- CC.6.1 mapping to P1.T2 isolation controls and CP.4 control plane
- CC.7.1 mapping to P4.T8.3 security logging and A2.5 execution trace
- CC.7.4 mapping to CP.10 HEAR designation
- A.1.2 mapping to P3 fail-safe and recovery controls
- Specific artifacts: A2.4 agent inventory, CP.3 ACT tier documentation,
  CP.8 CRT documentation, HEAR designation record

**Failure indicators:**
- Only general SOC 2 guidance without AI-specific control mappings
- No specific evidence artifacts named

---

## Eval 10: MCP Tool Usage (requires MCP server connected)

**Input prompt:**
> Use the AI SAFE2 MCP server to look up CP.9 and tell me its implementation details.

**Expected behavior:**
- Calls `lookup_control` with `control_id="CP.9"`
- Returns the full CP.9 specification
- Cites the implementation_details field including:
  - max_delegation_hops (ACT-3: 2, ACT-4: 3)
  - kill_switch_sla_ms: 500
  - lineage_token_fields
  - credential_model: ephemeral_per_hop_scope_narrowing

**Failure indicators:**
- Does not use the MCP tool
- Returns a different control
- Missing implementation details

---

## Running Evals

**Manual:** Feed each input prompt to the model with the skill loaded.
Check the output against the "Expected output must include" criteria.
Mark PASS / FAIL for each criterion.

**Automated:** If your platform supports LLM-based eval:
```python
# Pseudocode for automated eval
for eval in evals:
    response = model.complete(skill_context + eval.prompt)
    for criterion in eval.expected_criteria:
        assert criterion.lower() in response.lower(), f"FAIL: missing '{criterion}'"
```

**Pass threshold:** 90% of criteria must be met across all 10 evals.
Any failure on HEAR, CP.9, or ACT tier classification evals is a blocking failure.

---

*AI SAFE2 v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com/ai-safe2/*
