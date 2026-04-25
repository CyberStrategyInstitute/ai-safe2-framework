---
name: ai-safe2-secure-build-copilot
description: Apply AI SAFE2 v3.0 to security architecture reviews, code reviews, compliance mapping, and governance decisions for AI agents, multi-agent systems, RAG pipelines, MCP servers, tool-calling workflows, and AI-enabled automations. Use when the task involves agent autonomy classification, HEAR or CP.9 governance, prompt injection, tool misuse, model or memory security, AI compliance evidence, or mapping controls to ISO 42001, NIST AI RMF, EU AI Act, SOC 2, HIPAA, PCI-DSS, GDPR, FedRAMP, CMMC 2.0, or DORA.
---

# AI SAFE2 Secure Build Copilot

Apply AI SAFE2 as a control-anchored governance and security review layer for agentic systems. Treat this as a security and compliance skill, not a general-purpose AI coding skill.

## Quick Start

Use this skill when the user needs one of these outcomes:

- Security architecture review for an AI system, agent, orchestrator, RAG pipeline, MCP server, or AI automation
- Code review focused on prompt injection, secret exposure, memory governance, tool misuse, monitoring, and fail-safe controls
- ACT tier classification, HEAR determination, CP.8 catastrophic-risk gating, or CP.9 replication governance
- Compliance mapping or audit evidence for AI-related requirements
- Risk scoring that combines a vulnerability with AI SAFE2 posture and agentic amplification

If the task is mostly general software engineering without AI governance or agent security scope, do not force AI SAFE2 framing.

## Workflow

### 1. Triage the request

Classify the task before answering:

- Architecture review: assess design across all five pillars plus cross-pillar governance
- Code review: report findings first, include control IDs and concrete fixes
- Governance decision: determine ACT tier, HEAR requirement, CP.9 applicability, and deployment gates
- Compliance request: map requirements to AI SAFE2 controls and name the evidence artifacts
- Vulnerability or incident: calculate or estimate combined risk and recommend immediate controls

### 2. Apply the mandatory governance rules

For any agent design or review:

- State the ACT tier
- Flag CP.10 HEAR for ACT-3 and ACT-4
- Flag CP.9 when the agent can spawn or delegate to sub-agents
- Flag CP.8 catastrophic-risk thresholds for high-autonomy or regulated deployments

For any code review:

- Look for prompt injection, indirect injection, tool misuse, secrets in context, unsafe memory writes, missing trace logging, missing recursion limits, and absent human approval paths
- Give code or configuration fixes, not only conceptual advice

For any compliance request:

- Map each recommendation to specific AI SAFE2 control IDs
- Name the evidence artifacts the implementation should produce

## Response Contract

Prefer this structure:

```markdown
## Task

### Assessment
[Relevant pillars, ACT tier, HEAR or CP.9 status]

### Findings
**[Control ID] [Control Name]**
- Issue: [Specific problem]
- Risk: [Impact and likelihood]
- Fix: [Code or configuration change]
- Evidence: [Artifact created or required]

### Roadmap
1. Immediate
2. Short-term
3. Longer-term
```

For code review tasks, findings come first. For architecture or compliance tasks, keep the assessment concise and actionable.

## References

Read only the reference file needed for the task:

- `references/governance-core.md`: ACT tiers, HEAR, CP.9, risk scoring, and universal decision rules
- `references/review-and-mapping.md`: review workflow, five-pillar coverage, compliance evidence patterns, and response guidance
- `references/evals.md`: regression prompts and expected outputs for forward-testing or validation
