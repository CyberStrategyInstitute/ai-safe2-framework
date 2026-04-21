"""
AI SAFE2 MCP Server — Resource Registry
Exposes governance templates, schemas, and reference documents as MCP resources.
These are read-only artifacts the model can retrieve on demand.

Free tier: 3 resources (quick-start checklist, pillar overview, ACT tier reference).
Pro tier:  all resources including policy templates and audit scorecard schema.
"""
from __future__ import annotations

from mcp_server.tiers import gate_tool

# Resource registry
RESOURCES: dict[str, dict] = {
    # ── Free tier resources ────────────────────────────────────────────────────
    "quick_start_checklist": {
        "name": "AI SAFE2 v3.0 Quick-Start Security Checklist",
        "tier_required": "free",
        "description": "5-minute security checklist for AI builders — top 20 critical controls across all 5 pillars.",
        "content": """# AI SAFE2 v3.0 Quick-Start Security Checklist
**For builders deploying AI agents in production. Complete before launch.**

## Pillar 1: Sanitize & Isolate
- [ ] P1.T1.2 / S1.6 — Prompt injection defense active on all user and tool inputs
- [ ] P1.T1.5 — PII/PHI masking enabled before any data reaches the model
- [ ] P1.T1.10 — Every non-prompt input channel (RAG, tools, emails) sanitized
- [ ] S1.5 — Memory governance: all writes to persistent memory are authorized and logged
- [ ] S1.7 — If using n8n/Zapier/Power Automate: sandbox isolation verified, credentials scoped

## Pillar 2: Audit & Inventory
- [ ] A2.4 — Agent registered in state inventory with owner_of_record
- [ ] A2.5 — Semantic execution trace logging active, append-only store
- [ ] P2.T4.1 — All agents, models, and RAG sources catalogued

## Pillar 3: Fail-Safe & Recovery
- [ ] F3.2 — Recursion limit governor at API gateway (not system prompt), max depth 4
- [ ] P3.T5.2 — Emergency shutdown path defined and tested
- [ ] P3.T5.8 — Blast radius: agent cannot take down more than its defined scope

## Pillar 4: Engage & Monitor
- [ ] P4.T7.1 — Human approval required for irreversible or high-impact actions
- [ ] P4.T8.3 — Security events forwarded to SIEM
- [ ] M4.8 — If using Bedrock/Azure AI: platform-specific API monitoring active

## Pillar 5: Evolve & Educate
- [ ] P4.T7.7 / E5.1 — Adversarial testing completed before this deployment
- [ ] P5.T9.4 — AI framework dependencies checked against CVE database

## Cross-Pillar Governance
- [ ] CP.3 — ACT tier classified (ACT-1 through ACT-4)
- [ ] CP.6 — AIID quarterly incident review scheduled
- [ ] CP.8 — Catastrophic Risk Thresholds defined if ACT-3 or ACT-4
- [ ] CP.10 — HEAR designated if ACT-3 or ACT-4 (named human with kill-switch authority)

---
**Score 20/20 before production deployment.**
Full 161-point audit: cyberstrategyinstitute.com/ai-safe2/
""",
    },

    "pillar_overview": {
        "name": "AI SAFE2 v3.0 Five-Pillar Overview",
        "tier_required": "free",
        "description": "One-page reference for all 5 pillars plus cross-pillar governance layer.",
        "content": """# AI SAFE2 v3.0 — Five-Pillar + Cross-Pillar Overview

| Pillar | Role | Key v3.0 Controls |
|--------|------|-------------------|
| P1: Sanitize & Isolate | The Shield | S1.5 Memory Governance, S1.6 Cognitive Injection, S1.7 No-Code Security, P1.T1.10 Indirect Injection |
| P2: Audit & Inventory | The Ledger | A2.5 Execution Trace Logging, A2.6 RAG Corpus Diff, A2.3 Model Lineage, A2.4 Agent State Inventory |
| P3: Fail-Safe & Recovery | The Brakes | F3.2 Recursion Governor, F3.3 Swarm Quorum Abort, F3.4 Drift Rollback, F3.5 Cascade Containment |
| P4: Engage & Monitor | The Control Room | M4.4 Adversarial Detection, M4.5 Tool-Misuse, M4.8 Cloud AI Monitoring, M4.7 Jailbreak Telemetry |
| P5: Evolve & Educate | The Feedback Loop | E5.1 Continuous Evaluation, E5.2 Capability Emergence, E5.4 Red-Team Artifacts |
| Cross-Pillar (CP.1-CP.10) | The Governance OS | CP.3 ACT Tiers, CP.4 Control Plane, CP.9 Replication Governance (first in field), CP.10 HEAR Doctrine (first in field) |

## Risk Formula (v3.0)
```
Combined Risk Score = CVSS_Base + ((100 - Pillar_Score) / 10) + (AAF / 10)
```
AAF = OWASP AIVSS v0.8 Agentic Amplification Factor (10 factors, 0-10 each)
First framework to integrate AAF in a GRC formula.

## ACT Capability Tiers
| Tier | Name | Kill-Switch Required |
|------|------|---------------------|
| ACT-1 | Assisted | No |
| ACT-2 | Supervised | No |
| ACT-3 | Autonomous | Yes — CP.10 HEAR required |
| ACT-4 | Orchestrator | Yes — CP.10 HEAR + CP.9 ARG required |

## First-in-Field Controls
- **CP.9 Agent Replication Governance** — The only governance standard for agent replication. NIST/ISO/OWASP have nothing.
- **CP.10 HEAR Doctrine** — Named human with cryptographic signing key and unilateral kill-switch authority.
- **CP.7 Deception & Active Defense** — The only deception-class control in any AI governance framework.
- **OWASP AIVSS AAF Integration** — First framework to integrate amplification scoring in a GRC risk formula.
""",
    },

    "act_tier_reference": {
        "name": "ACT Capability Tier Quick Reference",
        "tier_required": "free",
        "description": "Complete ACT tier definitions, mandatory controls per tier, and governance evidence required.",
        "content": """# ACT Capability Tier Reference (AI SAFE2 v3.0 CP.3)

## Tier Definitions

### ACT-1: Assisted
Human reviews ALL outputs before any action is taken.
- State: read-only, no persistent state
- Mandatory controls: Standard P1-P5 baseline controls
- HEAR required: No
- CP.9 required: No

### ACT-2: Supervised
Agent acts with human checkpoints for critical decisions.
- State: limited tools, session state only
- Mandatory additional controls: CP.2 AMLTM, AAF scoring, S1.3, S1.5, A2.4, A2.5, F3.2, M4.4, M4.5, E5.1
- HEAR required: No
- CP.9 required: No

### ACT-3: Autonomous
Agent operates with post-hoc human review.
- State: broad tools, persistent state, multi-agent interactions
- Mandatory additional controls: All ACT-2 + CP.3, CP.4, CP.8, CP.10 HEAR, A2.3, A2.6, F3.4, F3.5, M4.6, M4.8, E5.2, E5.4
- HEAR required: YES — named individual with cryptographic signing key must be registered before deployment
- CP.9 required: If spawning sub-agents

### ACT-4: Orchestrator
Agent controls other agents with enterprise-scale authority.
- State: full tools, cross-org scope, agent spawning
- Mandatory additional controls: All ACT-3 + CP.9 ARG, F3.3, P4.T1.1_ADV
- HEAR required: YES
- CP.9 required: YES — max 3 delegation hops, 500ms kill-switch SLA

## Governance Evidence Required

| Evidence Artifact | ACT-1 | ACT-2 | ACT-3 | ACT-4 |
|-------------------|-------|-------|-------|-------|
| A2.4 inventory entry + owner_of_record | ✓ | ✓ | ✓ | ✓ |
| CP.2 threat model document | | ✓ | ✓ | ✓ |
| CP.3 tier classification in manifest | | ✓ | ✓ | ✓ |
| CP.4 control plane governance artifact | | | ✓ | ✓ |
| CP.8 Catastrophic Risk Thresholds doc | | | ✓ | ✓ |
| CP.10 HEAR designation + signing key | | | ✓ | ✓ |
| CP.9 replication governance spec | | | If spawning | ✓ |
| A2.5 execution trace logging verified | | | ✓ | ✓ |
| F3.2 recursion governor active at gateway | | ✓ | ✓ | ✓ |
""",
    },

    # ── Pro tier resources ─────────────────────────────────────────────────────
    "governance_policy_template": {
        "name": "Enterprise AI Governance Policy Template (AI SAFE2 v3.0)",
        "tier_required": "pro",
        "description": "Word-document-ready governance policy template with ACT tier assignments, HEAR designation clauses, and CP.9 replication language. Maps to ISO 42001 and EU AI Act.",
        "content": """# Enterprise AI Governance Policy
## AI SAFE2 v3.0 Aligned | ISO 42001 | EU AI Act

**Policy Version:** 3.0
**Framework:** AI SAFE2 v3.0 — Cyber Strategy Institute
**Review Cycle:** Annual + triggered by significant model or system change

---

## 1. Scope
This policy governs all AI systems, AI agents, automated workflows, and non-human identities (NHIs) operated by [Organization Name], including systems operated by third parties on behalf of the organization.

## 2. ACT Tier Classification Requirement
All AI agents MUST be classified by ACT Capability Tier before deployment to production.
No ACT-3 or ACT-4 agent may be deployed without:
- A completed A2.4 Dynamic Agent State Inventory entry
- A designated Human Ethical Agent of Record (HEAR) per CP.10
- Documented Catastrophic Risk Thresholds per CP.8
- Security review sign-off by [CISO / designated approver]

## 3. Human Ethical Agent of Record (HEAR) — CP.10
For all ACT-3 and ACT-4 deployments, a named Human Ethical Agent of Record MUST be designated.

**HEAR Requirements:**
- Named individual (not a team or role)
- Must hold a cryptographic signing key registered with [key management system]
- Must be reachable in real-time during all hours the agent operates
- Holds unilateral authority to halt the deployment without prior approval

**Class-H Action Protocol:**
Actions that are irreversible, financially material (>$[threshold]), security-control-modifying, physical-infrastructure-crossing, or cross-organizational MUST:
1. Pause agent execution
2. Present plain-language consequence to HEAR
3. Receive HEAR cryptographic signature
4. Log authorization to A2.5 before proceeding
Fail-closed: if HEAR is unreachable, Class-H actions are blocked.

## 4. Agent Replication Governance — CP.9
Any agent capable of spawning sub-agents MUST implement:
- Explicit replication authority in deployment manifest
- Ephemeral credentials with scope narrowing at each delegation hop
- Cryptographic lineage tokens on every spawned agent
- Maximum 2 delegation hops (ACT-3) or 3 hops (ACT-4)
- Kill-switch architecture that severs full delegation tree within 500ms

## 5. Compliance Mapping
This policy satisfies:
- ISO/IEC 42001:2023 Sections 6.1, 8.1, 8.4
- EU AI Act Articles 9 and 14 (human oversight for high-risk AI)
- SOC 2 CC.7.4 (incident response)
- GDPR Article 22 (automated decision safeguards)
- SEC Cybersecurity Disclosure accountability requirements

---
*Based on AI SAFE2 v3.0 — cyberstrategyinstitute.com/ai-safe2/*
""",
    },

    "audit_scorecard_schema": {
        "name": "AI SAFE2 v3.0 Audit Scorecard Schema",
        "tier_required": "pro",
        "description": "JSON schema for the 161-point audit scorecard. Use to build automated compliance assessment tools.",
        "content": """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AI SAFE2 v3.0 Audit Scorecard",
  "description": "161-point assessment across 5 pillars + 10 cross-pillar governance controls",
  "type": "object",
  "required": ["organization", "assessment_date", "assessor", "pillar_scores", "cp_scores"],
  "properties": {
    "organization": {"type": "string"},
    "assessment_date": {"type": "string", "format": "date"},
    "assessor": {"type": "string"},
    "scope": {"type": "string", "description": "Systems and deployments in scope"},
    "pillar_scores": {
      "type": "object",
      "properties": {
        "P1": {"$ref": "#/$defs/pillar_assessment"},
        "P2": {"$ref": "#/$defs/pillar_assessment"},
        "P3": {"$ref": "#/$defs/pillar_assessment"},
        "P4": {"$ref": "#/$defs/pillar_assessment"},
        "P5": {"$ref": "#/$defs/pillar_assessment"}
      }
    },
    "cp_scores": {
      "type": "array",
      "items": {"$ref": "#/$defs/control_assessment"}
    },
    "combined_risk_score": {
      "type": "number",
      "description": "CVSS + ((100 - Pillar_Score) / 10) + (AAF / 10)"
    },
    "overall_risk_level": {
      "type": "string",
      "enum": ["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW"]
    }
  },
  "$defs": {
    "pillar_assessment": {
      "type": "object",
      "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "controls_assessed": {"type": "integer"},
        "controls_compliant": {"type": "integer"},
        "critical_gaps": {"type": "array", "items": {"type": "string"}}
      }
    },
    "control_assessment": {
      "type": "object",
      "properties": {
        "control_id": {"type": "string"},
        "status": {"type": "string", "enum": ["compliant", "partial", "non_compliant", "not_applicable"]},
        "evidence": {"type": "string"},
        "notes": {"type": "string"}
      }
    }
  }
}""",
    },

    "hear_designation_template": {
        "name": "HEAR Designation and Class-H Action Protocol Template",
        "tier_required": "pro",
        "description": "Operational template for designating the Human Ethical Agent of Record and documenting Class-H action authorization. Satisfies EU AI Act Art. 14, SOC 2 CC.7.4, GDPR Art. 22.",
        "content": """# HEAR Designation Record (AI SAFE2 v3.0 CP.10)

## Deployment Details
- **Agent Name / ID:** _______________
- **ACT Tier:** ACT-3 / ACT-4 (circle one)
- **Deployment Date:** _______________
- **Deployment Environment:** Production / Staging (circle one)

## HEAR Designation
- **HEAR Full Name:** _______________
- **HEAR Title / Role:** _______________
- **HEAR Contact (24/7):** _______________
- **Public Key ID (Key Management System):** _______________
- **Key Registration Date:** _______________
- **Backup HEAR (required for ACT-4):** _______________

## Class-H Action Categories (check all that apply to this deployment)
- [ ] Irreversible actions (data deletion, contract execution, etc.)
- [ ] Financially material actions (threshold: $_____)
- [ ] Security-control-modifying actions
- [ ] Physical infrastructure boundary-crossing
- [ ] Cross-organizational commitments

## Authorization Protocol
1. Agent detects Class-H action trigger
2. Agent PAUSES execution — no action taken
3. Agent presents semantic consequence in plain language (not technical parameters)
4. HEAR reviews and signs with private key
5. Agent verifies signature cryptographically
6. Authorization logged to A2.5 BEFORE execution
7. Action proceeds

FAIL-CLOSED: If HEAR is unreachable or signature verification fails, the action is BLOCKED.
There is no automatic approval path for any Class-H category.

## Acknowledgment
I understand and accept my responsibilities as Human Ethical Agent of Record
for the above deployment. I hold unilateral kill-switch authority and accept
accountability for Class-H action authorizations.

**HEAR Signature:** _______________
**Date:** _______________
**Witness:** _______________

---
*AI SAFE2 v3.0 CP.10 | cyberstrategyinstitute.com/ai-safe2/*
""",
    },
}


def get_resource(resource_name: str, tier: str = "free") -> dict:
    """
    Retrieve a governance resource by name.

    Args:
        resource_name: Resource identifier. Available resources:
            Free: quick_start_checklist, pillar_overview, act_tier_reference
            Pro: governance_policy_template, audit_scorecard_schema, hear_designation_template
        tier: Caller access tier.

    Returns:
        dict with 'resource' content or error.
    """
    gate = gate_tool(tier, "get_resource")
    if gate is not None:
        # Free tier gets access to free resources only
        free_resources = {k: v for k, v in RESOURCES.items() if v["tier_required"] == "free"}
        if resource_name in free_resources:
            r = free_resources[resource_name]
            return {"resource_name": resource_name, "name": r["name"], "content": r["content"], "tier": "free"}
        # Explain what is available
        return {
            **gate,
            "free_resources_available": list(free_resources.keys()),
            "pro_resources_locked": [k for k, v in RESOURCES.items() if v["tier_required"] == "pro"],
        }

    if resource_name not in RESOURCES:
        return {
            "error": f"Resource '{resource_name}' not found",
            "available": list(RESOURCES.keys()),
        }

    r = RESOURCES[resource_name]
    return {
        "resource_name": resource_name,
        "name": r["name"],
        "description": r["description"],
        "tier_required": r["tier_required"],
        "content": r["content"],
        "tier": tier,
    }


def list_resources(tier: str = "free") -> dict:
    """List available resources for the given tier."""
    available = {
        k: {"name": v["name"], "description": v["description"], "tier_required": v["tier_required"]}
        for k, v in RESOURCES.items()
        if tier == "pro" or v["tier_required"] == "free"
    }
    locked = (
        {}
        if tier == "pro"
        else {
            k: {"name": v["name"], "description": v["description"]}
            for k, v in RESOURCES.items()
            if v["tier_required"] == "pro"
        }
    )
    result: dict = {"available_resources": available}
    if locked:
        result["locked_resources"] = locked
        result["upgrade_url"] = "https://cyberstrategyinstitute.com/ai-safe2/"
    return result
