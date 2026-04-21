"""
AI SAFE2 v3.0 Scanner — Cross-Pillar Governance Rules (CP.1-CP.10)
Structural analysis for ACT tier estimation, HEAR presence check (CP.10),
Agent Replication Governance (CP.9), and Catastrophic Risk Thresholds (CP.8).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from .base import Rule


# ── ACT Tier Estimation ────────────────────────────────────────────────────────

@dataclass
class ACTEstimate:
    """Result of ACT tier estimation from code analysis."""
    tier: str                       # ACT-1, ACT-2, ACT-3, ACT-4
    confidence: str                 # high, medium, low
    signals: list[str] = field(default_factory=list)
    mandatory_controls: list[str] = field(default_factory=list)
    hear_required: bool = False
    cp9_required: bool = False
    governance_gaps: list[str] = field(default_factory=list)


# Signals that indicate higher autonomy
ACT4_SIGNALS = [
    r"spawn_agent\s*\(", r"create_agent\s*\(", r"invoke_agent\s*\(",
    r"orchestrat", r"sub.?agent", r"worker.?agent", r"agent.?pool",
    r"multi.?agent", r"swarm", r"agent.?network", r"delegate.*agent",
    r"AutoGen|CrewAI|LangGraph.*multi", r"hierarchical.*agent",
]
ACT3_SIGNALS = [
    r"schedule\s*\(", r"cron\b", r"celery", r"background.*task",
    r"asyncio.*loop", r"daemon\b", r"unattended", r"overnight",
    r"persistent.*memory", r"cross.?session", r"memory\.save",
    r"vector.*store.*persist", r"\.save_context\(",
    r"send_email\s*\(", r"delete\s*\(", r"database.*write",
    r"payment\s*\.", r"financial.*transaction",
]
ACT2_SIGNALS = [
    r"human.*review\s*=\s*True", r"require.*approval", r"checkpoint\s*\(",
    r"await.*human", r"hitl\b", r"human.in.the.loop",
]


def estimate_act_tier(content: str) -> ACTEstimate:
    """
    Estimate ACT tier from file content based on detected signals.
    Returns an ACTEstimate with tier, confidence, and governance gaps.
    """
    signals = []

    # Check for spawning / orchestration (ACT-4)
    act4_hits = [p for p in ACT4_SIGNALS if re.search(p, content, re.IGNORECASE)]
    act3_hits = [p for p in ACT3_SIGNALS if re.search(p, content, re.IGNORECASE)]
    act2_hits = [p for p in ACT2_SIGNALS if re.search(p, content, re.IGNORECASE)]

    has_llm_call = bool(re.search(
        r"(openai\.|anthropic\.|\.invoke\(|agent\.run|llm\.predict|client\.messages\.create)",
        content, re.IGNORECASE
    ))

    if not has_llm_call:
        return ACTEstimate(tier="N/A", confidence="high",
                           signals=["No LLM API calls detected — not an agent file"])

    if act4_hits:
        tier = "ACT-4"
        confidence = "high"
        signals = [f"Spawning/orchestration signal: {h}" for h in act4_hits[:3]]
    elif len(act3_hits) >= 2:
        tier = "ACT-3"
        confidence = "medium"
        signals = [f"Autonomous operation signal: {h}" for h in act3_hits[:3]]
    elif len(act3_hits) == 1:
        tier = "ACT-3"
        confidence = "low"
        signals = [f"Autonomous operation signal: {h}" for h in act3_hits]
    elif act2_hits:
        tier = "ACT-2"
        confidence = "medium"
        signals = [f"Supervised operation signal: {h}" for h in act2_hits[:3]]
    else:
        tier = "ACT-1"
        confidence = "low"
        signals = ["No autonomous operation signals detected — defaulting to ACT-1"]

    # Determine governance gaps based on tier
    gaps = []
    hear_required = tier in ("ACT-3", "ACT-4")
    cp9_required = tier == "ACT-4"

    # Check for HEAR designation
    if hear_required:
        hear_fields = {"hear_agent_of_record", "hear_designation", "human_ethical_agent",
                       "hear_key", "hear_signing_key", "cp10", "cp.10"}
        has_hear = any(f in content.lower() for f in hear_fields)
        if not has_hear:
            gaps.append(
                f"CP.10 HEAR Doctrine: {tier} agent detected without hear_agent_of_record designation. "
                "A named individual with a cryptographic signing key must be registered before deployment."
            )

    # Check for CP.9 replication governance
    if cp9_required:
        lineage_fields = {"lineage_token", "replication_lineage", "delegation_hop",
                          "spawn_limit", "cp9", "cp.9", "agent_lineage"}
        has_cp9 = any(f in content.lower() for f in lineage_fields)
        if not has_cp9:
            gaps.append(
                "CP.9 Agent Replication Governance: orchestrator pattern detected without "
                "lineage token, delegation hop limits, or 500ms kill-switch tree implementation."
            )

    # Check for CP.8 catastrophic risk thresholds
    if tier in ("ACT-3", "ACT-4"):
        crt_fields = {"catastrophic_risk", "crt_", "emergency_threshold", "cp8",
                      "cp.8", "halt_threshold", "suspension_criteria"}
        has_crt = any(f in content.lower() for f in crt_fields)
        if not has_crt:
            gaps.append(
                "CP.8 Catastrophic Risk Thresholds: no CRT definition found. "
                "ACT-3/ACT-4 deployments require documented CRT before approval."
            )

    # Check for A2.5 execution trace
    trace_fields = {"execution_trace", "a2_5", "semantic_trace", "langsmith",
                    "langfuse", "opentelemetry", "tracing"}
    has_trace = any(f in content.lower() for f in trace_fields)
    if not has_trace and tier in ("ACT-2", "ACT-3", "ACT-4"):
        gaps.append(
            "A2.5 Semantic Execution Trace Logging: no trace logging detected. "
            "Required for ACT-2+ deployments."
        )

    mandatory = {
        "ACT-1": ["P1.T1.2", "P1.T1.5", "P2.T4.1", "P3.T5.1", "P4.T7.1"],
        "ACT-2": ["All ACT-1", "CP.2", "A2.5", "S1.5", "F3.2", "M4.4", "M4.5"],
        "ACT-3": ["All ACT-2", "CP.3", "CP.4", "CP.8", "CP.10 HEAR", "F3.4", "F3.5", "M4.6", "M4.8"],
        "ACT-4": ["All ACT-3", "CP.9 ARG", "F3.3", "P4.T1.1_ADV"],
    }.get(tier, [])

    return ACTEstimate(
        tier=tier,
        confidence=confidence,
        signals=signals,
        mandatory_controls=mandatory,
        hear_required=hear_required,
        cp9_required=cp9_required,
        governance_gaps=gaps,
    )


# ── Check Functions ────────────────────────────────────────────────────────────

def _check_cp9_replication(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    CP.9 — Agent Replication Governance
    Detect agent spawning without lineage tracking or delegation limits.
    """
    findings = []
    spawn_patterns = [
        r"spawn_agent\s*\(", r"create_agent\s*\(", r"invoke_agent\s*\(",
        r"Agent\s*\(.*\)\.run", r"new\s+Agent\s*\(",
        r"multiprocessing\.Process\s*\(.*agent",
        r"ThreadPoolExecutor.*agent", r"asyncio\.gather.*agent",
        r"CrewAI.*agent", r"AutoGen.*agent", r"langchain.*agent.*create",
    ]
    lineage_words = {
        "lineage_token", "parent_did", "delegation_depth", "chain_id",
        "cp9", "replication_lineage", "spawn_limit", "max_hops",
        "delegation_hop", "ephemeral_credential"
    }

    for i, line in enumerate(lines):
        for pat in spawn_patterns:
            if re.search(pat, line, re.IGNORECASE):
                if not any(w in content.lower() for w in lineage_words):
                    findings.append((
                        i + 1,
                        f"Agent spawning without CP.9 lineage governance: {line.strip()[:60]}"
                    ))
                break
    return findings


def _check_cp10_hear(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    CP.10 — HEAR Doctrine (Human Ethical Agent of Record)
    Detect ACT-3/4 deployment configs missing HEAR designation.
    Only runs on config files.
    """
    findings = []
    if not any(filepath.endswith(ext) for ext in (".json", ".yaml", ".yml", ".toml", ".env")):
        return []

    # ACT-3/4 indicators in config
    act34_indicators = [
        r"act.?tier\s*[:=]\s*[\"']?(ACT-3|ACT-4|3|4)",
        r"autonomous\s*[:=]\s*true",
        r"unattended\s*[:=]\s*true",
        r"orchestrat.*[:=]\s*true",
        r"spawn.*agent.*[:=]\s*true",
    ]
    has_act34 = any(re.search(p, content, re.IGNORECASE) for p in act34_indicators)
    if not has_act34:
        return []

    # HEAR designation fields
    hear_fields = {
        "hear_agent_of_record", "hear_designation", "human_ethical_agent",
        "hear_signing_key", "cp10", "responsible_human"
    }
    has_hear = any(f in content.lower() for f in hear_fields)

    if not has_hear:
        findings.append((
            1,
            "ACT-3/4 deployment config missing CP.10 HEAR designation — "
            "hear_agent_of_record field required before production deployment"
        ))
    return findings


def _check_cp8_missing_crt(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    CP.8 — Catastrophic Risk Threshold Controls
    Detect ACT-3/4 code patterns without CRT definitions.
    """
    findings = []
    if not any(filepath.endswith(ext) for ext in (".py", ".js", ".ts", ".yaml", ".yml")):
        return []

    # Must have autonomous agent signals to trigger
    has_autonomous = any(re.search(p, content, re.IGNORECASE) for p in [
        r"agent\.run\s*\(", r"\.invoke\s*\(", r"autonomous", r"unattended"
    ])
    if not has_autonomous:
        return []

    crt_words = {
        "catastrophic_risk", "crt_threshold", "emergency_halt", "cp8",
        "suspension_criteria", "halt_condition", "kill_threshold",
        "behavioral_threshold", "weaponizable"
    }
    if not any(w in content.lower() for w in crt_words):
        findings.append((
            1,
            "Autonomous agent without CP.8 Catastrophic Risk Thresholds — "
            "CRT documentation required before ACT-3/4 deployment approval"
        ))
    return findings


# ── Rule Definitions ──────────────────────────────────────────────────────────

CP_RULES: list[Rule] = [

    # CP.9 — Agent Replication Governance (FIRST IN FIELD)
    Rule(
        control_id="CP.9",
        severity="CRITICAL",
        description="Agent spawning or orchestration pattern without CP.9 replication governance — "
                    "no lineage tokens, delegation hop limits, or kill-switch tree architecture.",
        remediation="Apply CP.9: add lineage_token (parent_did, chain_id, delegation_depth, TTL) "
                    "to every spawned sub-agent. Enforce max 2 delegation hops (ACT-3) or 3 (ACT-4). "
                    "Implement gateway-layer kill switch that severs the full tree within 500ms. "
                    "No other governance framework has this standard.",
        check_fn=_check_cp9_replication,
        file_exts=(".py", ".js", ".ts"),
    ),

    # CP.10 — HEAR Doctrine (FIRST IN FIELD)
    Rule(
        control_id="CP.10",
        severity="CRITICAL",
        description="ACT-3/4 deployment configuration without CP.10 HEAR designation — "
                    "no named Human Ethical Agent of Record with cryptographic signing authority.",
        remediation="Apply CP.10: designate a named HEAR with a registered cryptographic signing key. "
                    "Add hear_agent_of_record to agent state inventory (A2.4). "
                    "Implement Class-H action protocol: agent pauses, HEAR signs, agent verifies before "
                    "any irreversible action. Fail-closed: no automatic approval path. "
                    "Satisfies: EU AI Act Art. 14, SOC 2 CC.7.4, GDPR Art. 22.",
        check_fn=_check_cp10_hear,
        file_exts=(".json", ".yaml", ".yml", ".toml", ".env"),
    ),

    # CP.8 — Catastrophic Risk Thresholds
    Rule(
        control_id="CP.8",
        severity="CRITICAL",
        description="Autonomous agent code without Catastrophic Risk Threshold definitions — "
                    "no behavioral indicators that trigger emergency suspension.",
        remediation="Apply CP.8: define CRTs for this agent: behaviors that trigger emergency "
                    "suspension regardless of business continuity impact. Required examples: "
                    "acquiring unauthorized compute, communicating outside approved list, "
                    "exhibiting weaponizable capability. Document before ACT-3/4 approval.",
        check_fn=_check_cp8_missing_crt,
        file_exts=(".py", ".js", ".ts", ".yaml", ".yml"),
    ),

    # CP.4 — Control Plane awareness
    Rule(
        control_id="CP.4",
        severity="MEDIUM",
        description="MCP server or agent protocol mesh in use without CP.4 control plane "
                    "governance artifacts — protocol-level supply chain not assessed.",
        remediation="Apply CP.4: treat every MCP server, A2A endpoint, and protocol mesh "
                    "as an Agentic Control Plane component. Assess against CP.3-CP.7 requirements. "
                    "Document in board-visible governance artifacts.",
        pattern=r"(mcp_server|ModelContextProtocol|StdioServerParameters|sse_server|a2a_endpoint)",
        file_exts=(".py", ".js", ".ts"),
    ),
]
