"""
AI SAFE2 Tool: classify_agent
Classify an AI agent by ACT Capability Tier (1-4) and return the
mandatory controls, governance requirements, and HEAR designation status.

Free tier:  returns ACT-1/ACT-2 classification only.
Pro tier:   full ACT-1 through ACT-4 classification with CP.9/CP.10 requirements.
"""
from __future__ import annotations

from mcp_server.controls_db import get_db
from mcp_server.tiers import gate_tool

# Signals that indicate higher autonomy tier
ACT_SIGNALS = {
    "ACT-4": [
        "orchestrates other agents", "spawns sub-agents", "controls multiple agents",
        "delegates to agents", "swarm", "agent network", "multi-agent orchestrator",
        "recursive agents", "agent tree", "agent hierarchy",
    ],
    "ACT-3": [
        "no human review", "autonomous", "post-hoc", "runs overnight", "scheduled",
        "unattended", "persistent state", "long-running", "cron", "background task",
        "cross-session memory", "broad tool access", "write access", "delete", "modify",
        "financial transactions", "send email", "send message",
    ],
    "ACT-2": [
        "human checkpoints", "approval", "human review for critical", "supervised",
        "limited tools", "read-only", "fetch", "search", "query",
    ],
}


def _detect_tier(
    description: str,
    human_review_required: bool,
    spawns_sub_agents: bool,
    has_persistent_memory: bool,
    tool_access: list[str],
    operates_unattended: bool,
) -> str:
    """Infer ACT tier from signals."""
    desc_lower = description.lower()
    tool_str = " ".join(tool_access).lower()
    combined = desc_lower + " " + tool_str

    # ACT-4: spawns agents (highest priority check)
    if spawns_sub_agents:
        return "ACT-4"
    if any(s in combined for s in ACT_SIGNALS["ACT-4"]):
        return "ACT-4"

    # ACT-3: autonomous operation (no human review + persistent state or unattended)
    if not human_review_required and operates_unattended:
        return "ACT-3"
    if not human_review_required and has_persistent_memory:
        return "ACT-3"
    if not human_review_required and any(s in combined for s in ACT_SIGNALS["ACT-3"]):
        return "ACT-3"

    # ACT-1: human reviews ALL outputs, no tool access, not unattended
    # Must be checked before ACT-2 to prevent description signal misclassification
    if human_review_required and not tool_access and not operates_unattended:
        return "ACT-1"

    # ACT-2: supervised with some tool access or human checkpoints (not all outputs reviewed)
    if tool_access and human_review_required:
        return "ACT-2"
    if any(s in combined for s in ACT_SIGNALS["ACT-2"]):
        if not operates_unattended:
            return "ACT-2"

    # Default: ACT-1
    return "ACT-1"


def classify_agent(
    description: str,
    human_review_required: bool = True,
    spawns_sub_agents: bool = False,
    has_persistent_memory: bool = False,
    tool_access: list[str] | None = None,
    operates_unattended: bool = False,
    deployment_environment: str = "",
    tier: str = "free",
) -> dict:
    """
    Classify an AI agent by ACT Capability Tier and return governance requirements.

    Args:
        description: What the agent does (be specific — include tools it calls,
                     what data it accesses, what actions it can take).
        human_review_required: Is a human required to review ALL outputs before action?
        spawns_sub_agents: Can this agent spawn or orchestrate other agents?
        has_persistent_memory: Does this agent retain state across sessions?
        tool_access: List of tools/actions the agent can call (e.g., ['email_send',
                     'database_write', 'web_search', 'file_delete']).
        operates_unattended: Does this agent run without human presence (scheduled,
                             overnight, background)?
        deployment_environment: Deployment context (e.g., 'production', 'enterprise',
                                'customer-facing', 'internal').
        tier: Caller access tier. Pro required for ACT-3/ACT-4 details.

    Returns:
        dict with ACT tier, mandatory controls, governance requirements, and HEAR status.
    """
    db = get_db()
    tool_access = tool_access or []

    # Pro gate for ACT-3/ACT-4 full details
    pro_gate = gate_tool(tier, "classify_agent")

    detected_tier = _detect_tier(
        description, human_review_required, spawns_sub_agents,
        has_persistent_memory, tool_access, operates_unattended,
    )

    # For free tier, cap at ACT-2 with upgrade note
    if pro_gate is not None and detected_tier in ("ACT-3", "ACT-4"):
        return {
            "detected_tier": detected_tier,
            "tier_limited": True,
            "message": (
                f"This agent appears to be {detected_tier}. Full classification, "
                "mandatory controls, HEAR designation requirements, and CP.9 "
                "replication governance specs require a Pro token. "
                "cyberstrategyinstitute.com/ai-safe2/"
            ),
            **pro_gate,
        }

    # Load tier requirements from controls JSON
    tier_req = db.get_act_requirements(detected_tier) or {}
    mandatory_control_ids: list[str] = tier_req.get("mandatory_controls", [])

    # Resolve controls
    mandatory_controls = []
    for ctrl_id in mandatory_control_ids:
        if ctrl_id.startswith("All "):
            continue  # reference to another tier; handled in description
        ctrl = db.get_by_id(ctrl_id)
        if ctrl:
            mandatory_controls.append({
                "id": ctrl["id"],
                "name": ctrl["name"],
                "pillar": ctrl["pillar_name"],
                "priority": ctrl["priority"],
                "description": ctrl["description"],
            })

    # HEAR requirement
    hear_required = detected_tier in ("ACT-3", "ACT-4")
    cp9_required = detected_tier in ("ACT-3", "ACT-4") and spawns_sub_agents

    # Governance evidence requirements
    governance_evidence = []
    if detected_tier in ("ACT-1", "ACT-2", "ACT-3", "ACT-4"):
        governance_evidence.append("A2.4: Dynamic Agent State Inventory entry with owner_of_record")
    if detected_tier in ("ACT-2", "ACT-3", "ACT-4"):
        governance_evidence.append("CP.2: Adversarial ML Threat Model document")
        governance_evidence.append("CP.3: ACT tier classification documented in deployment manifest")
    if detected_tier in ("ACT-3", "ACT-4"):
        governance_evidence.append("CP.4: Agentic Control Plane governance artifact for board reporting")
        governance_evidence.append("CP.8: Catastrophic Risk Threshold (CRT) document — required before deployment approval")
        governance_evidence.append("CP.10: HEAR designation: named individual with signing key registered in A2.4")
        governance_evidence.append("A2.5: Semantic Execution Trace Logging configured and verified")
        governance_evidence.append("F3.2: Recursion Limit Governor active at API gateway layer")
        governance_evidence.append("M4.4: Adversarial Behavior Detection Pipeline active")
    if detected_tier == "ACT-4":
        governance_evidence.append("CP.9: Agent Replication Governance: lineage tokens, delegation limits, 500ms kill-switch tree")
        governance_evidence.append("F3.3: Swarm Quorum Abort Mechanism configured")

    # Risk flags from inputs
    risk_flags = []
    dangerous_tools = {"email_send", "sms_send", "file_delete", "database_write",
                       "database_delete", "api_post", "api_put", "api_delete",
                       "payment", "transfer", "deploy", "execute", "shell"}
    flagged = [t for t in tool_access if any(d in t.lower() for d in dangerous_tools)]
    if flagged:
        risk_flags.append(
            f"High-impact tools detected: {', '.join(flagged)}. "
            "These tools require Class-H action protocol under CP.10 HEAR Doctrine."
        )
    if has_persistent_memory and not any("S1.5" in c["id"] for c in mandatory_controls):
        risk_flags.append(
            "Persistent memory requires S1.5 Memory Governance Boundary Controls. "
            "Every memory write must be authorized, sanitized, and logged."
        )
    if spawns_sub_agents and not cp9_required:
        risk_flags.append("Sub-agent spawning detected — CP.9 Agent Replication Governance applies.")

    return {
        "detected_tier": detected_tier,
        "tier_definition": {
            "ACT-1": "Assisted — human reviews all outputs before any action",
            "ACT-2": "Supervised — agent acts with human checkpoints for critical decisions",
            "ACT-3": "Autonomous — agent operates; human review is post-hoc",
            "ACT-4": "Orchestrator — agent controls other agents; enterprise-scale authority",
        }[detected_tier],
        "classification_signals": {
            "human_review_required": human_review_required,
            "spawns_sub_agents": spawns_sub_agents,
            "has_persistent_memory": has_persistent_memory,
            "operates_unattended": operates_unattended,
            "tool_count": len(tool_access),
            "deployment_environment": deployment_environment or "not specified",
        },
        "hear_designation_required": hear_required,
        "cp9_replication_governance_required": cp9_required,
        "mandatory_controls": mandatory_controls,
        "governance_evidence_required": governance_evidence,
        "risk_flags": risk_flags,
        "next_steps": _next_steps(detected_tier, hear_required, cp9_required),
        "meta": {"tier": tier, "framework_version": "v3.0"},
    }


def _next_steps(act: str, hear: bool, cp9: bool) -> list[str]:
    steps = []
    if act in ("ACT-3", "ACT-4"):
        steps.append("1. Create A2.4 agent state inventory entry with owner_of_record field")
        if hear:
            steps.append("2. Designate a HEAR (Human Ethical Agent of Record): named individual with cryptographic signing key")
        steps.append("3. Document CP.8 Catastrophic Risk Thresholds before deployment approval")
        if cp9:
            steps.append("4. Implement CP.9 Agent Replication Governance: lineage tokens, delegation hop limits, 500ms kill-switch")
        steps.append(f"5. Activate F3.2 Recursion Limit Governor at API gateway (not system prompt)")
        steps.append("6. Configure A2.5 Semantic Execution Trace Logging with append-only store")
    elif act == "ACT-2":
        steps.append("1. Define human checkpoint triggers for high-risk actions")
        steps.append("2. Implement CP.2 Adversarial ML Threat Model document")
        steps.append("3. Configure AAF scoring for the risk formula")
    else:
        steps.append("1. Implement standard P1-P5 pillar controls")
        steps.append("2. Register agent in A2.4 inventory with owner_of_record")
        steps.append("3. Configure CP.6 AIID incident review process")
    return steps
