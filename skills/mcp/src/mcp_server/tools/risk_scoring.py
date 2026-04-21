"""
AI SAFE2 Tool: calculate_risk_score
Computes the AI SAFE2 v3.0 Combined Risk Score:

  Combined Risk Score = CVSS_Base + ((100 - Pillar_Score) / 10) + (AAF / 10)

Free tier: basic formula (CVSS + Pillar), no AAF.
Pro tier:  full formula with OWASP AIVSS v0.8 Agentic Amplification Factor.
"""
from __future__ import annotations

from mcp_server.controls_db import get_db
from mcp_server.tiers import gate_tool

# AAF factor descriptions for reporting
AAF_FACTOR_LABELS = {
    "autonomy_level":          "Agent autonomy level (0=human-reviewed, 10=fully autonomous)",
    "tool_access_breadth":     "Number and sensitivity of tools the agent can call",
    "natural_language_reliance": "Degree to which decisions rely on LLM natural language output",
    "context_persistence":     "Amount of context retained across sessions",
    "behavioral_determinism":  "Predictability of agent behavior (0=deterministic, 10=stochastic)",
    "decision_opacity":        "Opacity of decision rationale to operators",
    "state_retention":         "Whether agent retains state across sessions",
    "dynamic_identity":        "Whether agent can adopt different identities or personas",
    "multi_agent_interactions": "Degree of interaction with other agents",
    "self_modification":       "Whether agent can modify its own configuration or prompts",
}

# Interpretation thresholds
def _interpret(score: float) -> str:
    if score >= 15:
        return "CRITICAL — immediate governance action required"
    if score >= 12:
        return "HIGH — significant agentic risk amplification"
    if score >= 9:
        return "MEDIUM-HIGH — standard SAFE2 controls required"
    if score >= 6:
        return "MEDIUM — baseline controls sufficient"
    return "LOW — routine monitoring"


def calculate_risk_score(
    cvss_base: float,
    pillar_score: float,
    aaf_factors: dict[str, float] | None = None,
    tier: str = "free",
) -> dict:
    """
    Calculate the AI SAFE2 v3.0 Combined Risk Score.

    Args:
        cvss_base: CVSS base score (0-10). Use the official CVSS calculator for your CVE.
        pillar_score: Organization's AI SAFE2 pillar compliance score (0-100).
                      100 = fully compliant, 0 = no controls in place.
                      Use the 151-Point Audit Scorecard from the Toolkit if available.
        aaf_factors: Dict of OWASP AIVSS v0.8 Agentic Amplification Factor values.
                     Each factor: 0 (control prevents it) / 5 (governed) / 10 (uncontrolled).
                     Required for Pro tier. Free tier uses estimated AAF = 0.
        tier: Caller access tier ('free' or 'pro').

    Returns:
        dict with combined score, components, interpretation, and recommendations.
    """
    db = get_db()

    # Validate inputs
    if not (0 <= cvss_base <= 10):
        return {"error": "cvss_base must be between 0 and 10"}
    if not (0 <= pillar_score <= 100):
        return {"error": "pillar_score must be between 0 and 100"}

    # Pillar component
    pillar_component = (100 - pillar_score) / 10

    # AAF component
    aaf_gate = gate_tool(tier, "full_aaf")
    if aaf_gate is not None:
        # Free tier: no AAF, inform user
        aaf_total = 0.0
        aaf_component = 0.0
        aaf_note = (
            "AAF scoring requires Pro tier. Score shown uses AAF=0 (baseline). "
            "Actual risk may be significantly higher for autonomous agents. "
            "Upgrade: cyberstrategyinstitute.com/ai-safe2/"
        )
        aaf_breakdown = {}
    else:
        # Pro tier: compute AAF
        if aaf_factors is None:
            aaf_factors = {}

        known_factors = list(AAF_FACTOR_LABELS.keys())
        aaf_breakdown = {}
        aaf_total = 0.0

        for factor in known_factors:
            val = float(aaf_factors.get(factor, 0))
            val = max(0.0, min(10.0, val))  # clamp
            aaf_breakdown[factor] = {
                "value": val,
                "description": AAF_FACTOR_LABELS[factor],
                "governance": (
                    "architecturally prevented" if val == 0
                    else "governed by SAFE2 controls" if val <= 5
                    else "UNCONTROLLED — governance failure"
                ),
            }
            aaf_total += val

        aaf_component = aaf_total / 10
        aaf_note = None

    combined = cvss_base + pillar_component + aaf_component
    combined = round(combined, 2)

    result: dict = {
        "combined_risk_score": combined,
        "interpretation": _interpret(combined),
        "components": {
            "cvss_base": cvss_base,
            "pillar_component": round(pillar_component, 2),
            "pillar_score_input": pillar_score,
            "aaf_component": round(aaf_component, 2),
            "aaf_total_raw": round(aaf_total, 1),
        },
        "formula": db.risk_formula["formula"],
        "tier": tier,
    }

    if aaf_breakdown:
        result["aaf_breakdown"] = aaf_breakdown
        uncontrolled = [f for f, v in aaf_breakdown.items() if v["value"] >= 8]
        if uncontrolled:
            result["governance_failures"] = {
                "factors": uncontrolled,
                "action": "These AAF factors are uncontrolled. Address immediately via CP.3 and CP.4.",
            }

    if aaf_note:
        result["aaf_note"] = aaf_note

    # Recommendations based on score
    recommendations = []
    if pillar_score < 50:
        recommendations.append("Pillar score below 50 — run the 151-Point Audit Scorecard (Toolkit) to identify control gaps.")
    if cvss_base >= 8:
        recommendations.append("High CVSS — prioritize P1 sanitization controls and P3 fail-safe controls immediately.")
    if combined >= 15:
        recommendations.append("Combined score CRITICAL — escalate to CISO and initiate emergency control review.")
    result["recommendations"] = recommendations

    return result
