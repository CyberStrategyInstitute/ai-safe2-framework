"""
AI SAFE2 MCP Server — Prompt Registry
Reusable task-starter prompts for common AI SAFE2 v3.0 workflows.
These are parameterized prompt fragments clients can invoke to bootstrap workflows.
"""
from __future__ import annotations


PROMPTS: dict[str, dict] = {
    "security_architecture_review": {
        "name": "AI System Security Architecture Review",
        "description": "Start a comprehensive AI SAFE2 v3.0 security review of a system design or architecture.",
        "arguments": [
            {"name": "system_description", "description": "What the AI system does", "required": True},
            {"name": "deployment_environment", "description": "Where it runs (cloud, on-prem, edge)", "required": False},
            {"name": "compliance_requirements", "description": "Relevant regulations (HIPAA, GDPR, SOC 2, etc.)", "required": False},
        ],
        "template": (
            "Conduct a comprehensive AI SAFE2 v3.0 security architecture review for: {system_description}\n\n"
            "Environment: {deployment_environment}\n"
            "Compliance requirements: {compliance_requirements}\n\n"
            "Structure your review across all 5 AI SAFE2 pillars plus the Cross-Pillar Governance Layer:\n"
            "1. P1 Sanitize & Isolate: trust boundaries, injection surfaces, memory governance\n"
            "2. P2 Audit & Inventory: what needs to be logged, traced, and inventoried\n"
            "3. P3 Fail-Safe & Recovery: failure modes, recursion risks, cascade paths\n"
            "4. P4 Engage & Monitor: anomaly detection strategy, HITL requirements\n"
            "5. P5 Evolve & Educate: evaluation cadence, red team needs\n"
            "6. Cross-Pillar: ACT tier classification, HEAR requirement, CP.9 if agents spawn agents\n\n"
            "Use the control_lookup tool to retrieve specific control requirements as needed. "
            "Use calculate_risk_score with the system's CVSS exposure and pillar score estimate. "
            "Return structured findings with control IDs and prioritized remediation."
        ),
    },

    "compliance_gap_analysis": {
        "name": "AI Compliance Gap Analysis",
        "description": "Identify gaps between current AI controls and a specific compliance framework.",
        "arguments": [
            {"name": "framework", "description": "Framework to analyze against (e.g., EU_AI_Act, SOC2_Type2, ISO_42001)", "required": True},
            {"name": "current_controls", "description": "Description of controls currently in place", "required": True},
        ],
        "template": (
            "Conduct a gap analysis between the current AI controls and {framework}.\n\n"
            "Current controls in place:\n{current_controls}\n\n"
            "Steps:\n"
            "1. Use map_to_frameworks with framework='{framework}' to retrieve all relevant AI SAFE2 v3.0 controls\n"
            "2. For each required control, assess whether it is: Compliant / Partial / Gap\n"
            "3. Prioritize gaps by severity (CRITICAL first)\n"
            "4. For each gap, specify the exact AI SAFE2 control ID, implementation requirement, and evidence needed\n"
            "5. Produce a remediation roadmap: Week 1 (Critical), Month 1 (High), Quarter (Medium)\n\n"
            "Output as a structured gap table followed by a prioritized remediation plan."
        ),
    },

    "incident_response_runbook": {
        "name": "AI Security Incident Response Runbook",
        "description": "Generate an AI-specific incident response runbook for a given incident type.",
        "arguments": [
            {"name": "incident_type", "description": "Type of incident (e.g., prompt injection, RAG poisoning, agent loop, secret leakage, HEAR unavailable)", "required": True},
            {"name": "system_context", "description": "Brief description of the affected system", "required": False},
        ],
        "template": (
            "Generate an AI SAFE2 v3.0 incident response runbook for: {incident_type}\n"
            "System context: {system_context}\n\n"
            "Structure the runbook as:\n"
            "1. Detection: How to identify this incident type\n"
            "2. Immediate containment (first 15 minutes): Specific actions using AI SAFE2 controls\n"
            "3. HEAR notification protocol (if ACT-3/ACT-4 agent involved)\n"
            "4. Eradication: Root cause elimination steps\n"
            "5. Recovery: Restore from clean state using P3 recovery controls\n"
            "6. Post-incident: Update CP.6 AIID incident log, E5.4 red-team artifact, and CP.2 threat model\n"
            "7. Evidence preservation: What logs and artifacts to preserve for compliance reporting\n\n"
            "Reference specific AI SAFE2 v3.0 control IDs throughout."
        ),
    },

    "agent_deployment_checklist": {
        "name": "Agent Deployment Readiness Checklist",
        "description": "Generate a deployment readiness checklist for a specific agent ACT tier.",
        "arguments": [
            {"name": "agent_name", "description": "Name or description of the agent", "required": True},
            {"name": "act_tier", "description": "ACT tier: ACT-1, ACT-2, ACT-3, or ACT-4", "required": True},
            {"name": "deployment_date", "description": "Target deployment date", "required": False},
        ],
        "template": (
            "Generate a deployment readiness checklist for: {agent_name}\n"
            "ACT Tier: {act_tier}\n"
            "Target date: {deployment_date}\n\n"
            "Use classify_agent if you need to verify the ACT tier first.\n"
            "Use control_lookup with act_tier='{act_tier}' to retrieve all mandatory controls.\n\n"
            "Structure the checklist as:\n"
            "- Pre-deployment security controls (P1-P5 mandatory for this tier)\n"
            "- Governance artifacts required (A2.4 entry, CP.3 classification, etc.)\n"
            "- HEAR designation status (if ACT-3/ACT-4)\n"
            "- CP.9 replication governance (if spawning sub-agents)\n"
            "- Compliance evidence package (what auditor artifacts must exist)\n"
            "- Go/No-Go criteria: minimum gates that must pass before production\n\n"
            "Mark each item as [Required] [Recommended] or [ACT-4 Only]."
        ),
    },
}


def get_prompt(prompt_name: str, arguments: dict[str, str] | None = None) -> dict:
    """
    Retrieve and optionally render a prompt template.

    Args:
        prompt_name: Prompt identifier (see PROMPTS keys).
        arguments: Values to substitute into the template.

    Returns:
        dict with prompt content and metadata.
    """
    if prompt_name not in PROMPTS:
        return {
            "error": f"Prompt '{prompt_name}' not found",
            "available": list(PROMPTS.keys()),
        }

    p = PROMPTS[prompt_name]
    template = p["template"]

    if arguments:
        for k, v in arguments.items():
            template = template.replace(f"{{{k}}}", v or "not provided")

    return {
        "prompt_name": prompt_name,
        "name": p["name"],
        "description": p["description"],
        "arguments": p["arguments"],
        "rendered_prompt": template,
    }


def list_prompts() -> dict:
    """List all available prompt templates."""
    return {
        "prompts": {
            name: {
                "name": p["name"],
                "description": p["description"],
                "arguments": p["arguments"],
            }
            for name, p in PROMPTS.items()
        }
    }
