"""
AI SAFE2 Tool: review_code (Light Version)
Analyzes code against AI SAFE2 v3.0 controls using the control taxonomy as context.
No server-side code execution. The model reasons about the code using the controls.

Pro tier only.
"""
from __future__ import annotations

from mcp_server.controls_db import get_db
from mcp_server.tiers import gate_tool

# Controls most relevant to code review — pre-selected for context injection
CODE_REVIEW_CONTROL_IDS = [
    "P1.T1.1", "P1.T1.2", "P1.T1.5", "P1.T1.9",
    "P1.T1.2_ADV", "P1.T1.4_ADV", "P1.T1.5_ADV",
    "P1.T2.3", "P1.T2.5", "P1.T2.9",
    "P1.T2.2_ADV", "P1.T1.10", "S1.3", "S1.4", "S1.5", "S1.6", "S1.7",
    "P2.T3.1", "P2.T3.7", "P2.T1.1_ADV", "A2.5",
    "P3.T5.1", "P3.T5.2", "P3.T5.4", "P3.T5.7", "P3.T1.1_ADV", "F3.2", "F3.5",
    "P4.T8.2", "P4.T8.3", "M4.4", "M4.5", "M4.7", "M4.8",
    "CP.3", "CP.4", "CP.9", "CP.10",
]

# Severity classification guidance
SEVERITY_GUIDE = {
    "critical": "Immediate exploitation risk or data leakage. Fix before deployment.",
    "high":     "Significant security risk. Fix within current sprint.",
    "medium":   "Should be fixed. Schedule within 30 days.",
    "low":      "Best practice improvement. Address in next security review.",
    "info":     "Observation or improvement opportunity. No immediate risk.",
}


def review_code(
    code: str,
    language: str = "python",
    context: str = "",
    focus_pillar: str = "",
    tier: str = "free",
) -> dict:
    """
    Review code against AI SAFE2 v3.0 controls and return structured findings.

    This is a light-version review: the function provides the control context
    and review framework so the model can reason about the code.
    No code is executed on the server.

    Args:
        code: The code to review (paste the relevant snippet or file).
        language: Programming language ('python', 'javascript', 'typescript', etc.).
        context: Optional description of what this code does / its role in the system.
        focus_pillar: Optional pillar to focus the review ('P1', 'P2', 'P3', 'P4', 'P5').
        tier: Caller access tier. Pro required.

    Returns:
        dict with 'review_context' containing the controls framework for model-based analysis,
        'findings_template' for structured output, and 'instructions' for the reviewing model.
    """
    gate = gate_tool(tier, "code_review")
    if gate is not None:
        return gate

    db = get_db()

    # Load the most relevant controls for code review
    review_controls = []
    for ctrl_id in CODE_REVIEW_CONTROL_IDS:
        ctrl = db.get_by_id(ctrl_id)
        if ctrl:
            # Filter by pillar if requested
            if focus_pillar and ctrl.get("pillar_id") not in (focus_pillar.upper(), "CP"):
                continue
            review_controls.append({
                "id": ctrl["id"],
                "name": ctrl["name"],
                "pillar": ctrl["pillar_name"],
                "priority": ctrl["priority"],
                "description": ctrl["description"],
                "builder_problem": ctrl["builder_problem"],
                "tags": ctrl["tags"],
            })

    # If pillar focused, also fetch all controls for that pillar
    if focus_pillar:
        pillar_controls = db.get_by_pillar(focus_pillar)
        existing_ids = {c["id"] for c in review_controls}
        for ctrl in pillar_controls:
            if ctrl["id"] not in existing_ids:
                review_controls.append({
                    "id": ctrl["id"],
                    "name": ctrl["name"],
                    "pillar": ctrl["pillar_name"],
                    "priority": ctrl["priority"],
                    "description": ctrl["description"],
                    "builder_problem": ctrl["builder_problem"],
                    "tags": ctrl["tags"],
                })

    return {
        "tool": "review_code",
        "input": {
            "language": language,
            "context": context or "Not provided",
            "code_length_chars": len(code),
            "focus_pillar": focus_pillar or "all pillars",
        },
        "review_controls": review_controls,
        "severity_guide": SEVERITY_GUIDE,
        "findings_template": {
            "description": "Use this structure for each finding",
            "fields": {
                "id": "F001, F002, ...",
                "severity": "critical | high | medium | low | info",
                "category": "ai_specific | traditional_security | configuration | compliance",
                "pillar": "Pillar name",
                "safe2_control": "Control ID (e.g., S1.5, CP.10)",
                "control_name": "Human-readable control name",
                "title": "Short finding title",
                "description": "What the issue is and where it appears",
                "evidence": {
                    "location": "Line number, function name, or section",
                    "code_snippet": "The relevant code",
                },
                "impact": "What could happen if exploited",
                "remediation": {
                    "summary": "How to fix it",
                    "code_suggestion": "Corrected code pattern if applicable",
                },
                "compliance_impact": ["Framework references affected"],
            },
        },
        "instructions": (
            f"Review the following {language} code against AI SAFE2 v3.0 controls. "
            f"Context: {context or 'general AI system component'}. "
            "For each control in review_controls, assess whether the code satisfies, "
            "violates, or does not apply to that control. "
            "Return findings using the findings_template structure. "
            "Focus on: prompt injection surfaces, secret handling, memory governance, "
            "error handling, logging, rate limiting, and agentic trust boundaries. "
            "Prioritize critical and high severity findings first. "
            "Provide actionable code-level remediation for each finding. "
            f"\n\nCODE TO REVIEW:\n```{language}\n{code}\n```"
        ),
        "meta": {
            "controls_loaded": len(review_controls),
            "tier": tier,
            "note": (
                "This is a model-assisted review using the AI SAFE2 v3.0 control taxonomy. "
                "Complement with static analysis tools (bandit, semgrep) for production systems."
            ),
        },
    }
