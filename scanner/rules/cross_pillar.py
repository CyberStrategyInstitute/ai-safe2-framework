"""
AI SAFE2 v3.1 Scanner - Cross-Pillar Governance Rules (CP.1-CP.10).
Structural analysis for ACT tier estimation, HEAR presence, replication
governance, catastrophic-risk thresholds, and control-plane awareness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .base import Rule


@dataclass
class ACTEstimate:
    """Result of ACT tier estimation from code analysis."""

    tier: str
    confidence: str
    signals: list[str] = field(default_factory=list)
    mandatory_controls: list[str] = field(default_factory=list)
    hear_required: bool = False
    cp9_required: bool = False
    governance_gaps: list[str] = field(default_factory=list)


ACT4_SIGNALS = [
    r"spawn_agent\s*\(",
    r"create_agent\s*\(",
    r"invoke_agent\s*\(",
    r"orchestrat",
    r"sub.?agent",
    r"worker.?agent",
    r"agent.?pool",
    r"multi.?agent",
    r"swarm",
    r"agent.?network",
    r"delegate.*agent",
    r"AutoGen|CrewAI|LangGraph.*multi",
    r"hierarchical.*agent",
]

ACT3_SIGNALS = [
    r"schedule\s*\(",
    r"cron\b",
    r"celery",
    r"background.*task",
    r"asyncio.*loop",
    r"daemon\b",
    r"unattended",
    r"persistent.*memory",
    r"durable.*memory",
    r"handle[_-]?scoped",
    r"cross.?session",  # legacy compatibility signal
    r"memory\.save",
    r"vector.*store.*persist",
    r"\.save_context\(",
    r"send_email\s*\(",
    r"database.*write",
    r"payment\s*\.",
    r"financial.*transaction",
]

ACT2_SIGNALS = [
    r"human.*review\s*=\s*True",
    r"require.*approval",
    r"checkpoint\s*\(",
    r"await.*human",
    r"hitl\b",
    r"human.in.the.loop",
]


def estimate_act_tier(content: str) -> ACTEstimate:
    """Estimate ACT tier from static signals and return governance gaps."""
    act4_hits = [pattern for pattern in ACT4_SIGNALS if re.search(pattern, content, re.IGNORECASE)]
    act3_hits = [pattern for pattern in ACT3_SIGNALS if re.search(pattern, content, re.IGNORECASE)]
    act2_hits = [pattern for pattern in ACT2_SIGNALS if re.search(pattern, content, re.IGNORECASE)]

    has_llm_call = bool(re.search(
        r"(openai\.|anthropic\.|\.invoke\(|agent\.run|llm\.predict|client\.messages\.create)",
        content,
        re.IGNORECASE,
    ))

    if not has_llm_call:
        return ACTEstimate(
            tier="N/A",
            confidence="high",
            signals=["No LLM API calls detected; not classified as an agent file"],
        )

    if act4_hits:
        tier = "ACT-4"
        confidence = "high"
        signals = [f"Spawning/orchestration signal: {hit}" for hit in act4_hits[:3]]
    elif len(act3_hits) >= 2:
        tier = "ACT-3"
        confidence = "medium"
        signals = [f"Autonomous operation signal: {hit}" for hit in act3_hits[:3]]
    elif len(act3_hits) == 1:
        tier = "ACT-3"
        confidence = "low"
        signals = [f"Autonomous operation signal: {hit}" for hit in act3_hits]
    elif act2_hits:
        tier = "ACT-2"
        confidence = "medium"
        signals = [f"Supervised operation signal: {hit}" for hit in act2_hits[:3]]
    else:
        tier = "ACT-1"
        confidence = "low"
        signals = ["No autonomous operation signals detected; defaulting to ACT-1"]

    gaps: list[str] = []
    hear_required = tier in ("ACT-3", "ACT-4")
    cp9_required = tier == "ACT-4"
    lower = content.lower()

    if hear_required:
        hear_fields = {
            "hear_agent_of_record",
            "hear_designation",
            "human_ethical_agent",
            "hear_key",
            "hear_signing_key",
            "cp10",
            "cp.10",
        }
        if not any(field_name in lower for field_name in hear_fields):
            gaps.append(
                f"CP.10 HEAR Doctrine: {tier} agent detected without a HEAR designation. "
                "A named accountable human with effective stop authority is required before deployment."
            )

    if cp9_required:
        lineage_fields = {
            "lineage_token",
            "replication_lineage",
            "delegation_hop",
            "spawn_limit",
            "cp9",
            "cp.9",
            "agent_lineage",
            "capability_grant_id",
        }
        if not any(field_name in lower for field_name in lineage_fields):
            gaps.append(
                "CP.9 Agent Replication Governance: orchestrator pattern detected without "
                "lineage, delegation limits, or descendant-revocation evidence."
            )

    if tier in ("ACT-3", "ACT-4"):
        crt_fields = {
            "catastrophic_risk",
            "crt_",
            "emergency_threshold",
            "cp8",
            "cp.8",
            "halt_threshold",
            "suspension_criteria",
        }
        if not any(field_name in lower for field_name in crt_fields):
            gaps.append(
                "CP.8 Catastrophic Risk Thresholds: no CRT definition found. "
                "ACT-3 and ACT-4 deployments require documented emergency stop conditions."
            )

    trace_fields = {
        "execution_trace",
        "a2_5",
        "semantic_trace",
        "langsmith",
        "langfuse",
        "opentelemetry",
        "tracing",
    }
    if not any(field_name in lower for field_name in trace_fields) and tier in ("ACT-2", "ACT-3", "ACT-4"):
        gaps.append(
            "A2.5 Semantic Execution Trace Logging: no trace logging detected for an ACT-2+ deployment."
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


def _check_cp9_replication(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    spawn_patterns = [
        r"spawn_agent\s*\(",
        r"create_agent\s*\(",
        r"invoke_agent\s*\(",
        r"Agent\s*\(.*\)\.run",
        r"new\s+Agent\s*\(",
        r"multiprocessing\.Process\s*\(.*agent",
        r"ThreadPoolExecutor.*agent",
        r"asyncio\.gather.*agent",
        r"CrewAI.*agent",
        r"AutoGen.*agent",
        r"langchain.*agent.*create",
    ]
    lineage_words = {
        "lineage_token",
        "parent_did",
        "delegation_depth",
        "chain_id",
        "cp9",
        "replication_lineage",
        "spawn_limit",
        "max_hops",
        "delegation_hop",
        "ephemeral_credential",
        "capability_grant_id",
    }

    lower = content.lower()
    for index, line in enumerate(lines, start=1):
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in spawn_patterns):
            if not any(word in lower for word in lineage_words):
                findings.append((
                    index,
                    f"Agent spawning without CP.9 lineage governance: {line.strip()[:80]}",
                ))
    return findings


def _check_cp10_hear(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not any(filepath.endswith(ext) for ext in (".json", ".yaml", ".yml", ".toml", ".env")):
        return []

    act34_indicators = [
        r"act.?tier\s*[:=]\s*[\"']?(ACT-3|ACT-4|3|4)",
        r"autonomous\s*[:=]\s*true",
        r"unattended\s*[:=]\s*true",
        r"orchestrat.*[:=]\s*true",
        r"spawn.*agent.*[:=]\s*true",
    ]
    if not any(re.search(pattern, content, re.IGNORECASE) for pattern in act34_indicators):
        return []

    hear_fields = {
        "hear_agent_of_record",
        "hear_designation",
        "human_ethical_agent",
        "hear_signing_key",
        "cp10",
        "responsible_human",
    }
    if any(field_name in content.lower() for field_name in hear_fields):
        return []

    return [(
        1,
        "ACT-3/4 deployment config missing CP.10 HEAR designation",
    )]


def _check_cp8_missing_crt(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    if not any(filepath.endswith(ext) for ext in (".py", ".js", ".ts", ".yaml", ".yml")):
        return []

    has_autonomous = any(re.search(pattern, content, re.IGNORECASE) for pattern in (
        r"agent\.run\s*\(",
        r"\.invoke\s*\(",
        r"autonomous",
        r"unattended",
    ))
    if not has_autonomous:
        return []

    crt_words = {
        "catastrophic_risk",
        "crt_threshold",
        "emergency_halt",
        "cp8",
        "suspension_criteria",
        "halt_condition",
        "kill_threshold",
        "behavioral_threshold",
    }
    if any(word in content.lower() for word in crt_words):
        return []

    return [(
        1,
        "Autonomous agent without CP.8 Catastrophic Risk Threshold definitions",
    )]


CP_RULES: list[Rule] = [
    Rule(
        control_id="CP.9",
        severity="CRITICAL",
        description="Agent spawning or orchestration pattern without visible CP.9 replication governance.",
        remediation="Add descendant lineage, narrowed capability grants, delegation limits, inventory, and full-tree revocation behavior.",
        check_fn=_check_cp9_replication,
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="CP.10",
        severity="CRITICAL",
        description="ACT-3/4 deployment configuration without a CP.10 HEAR designation.",
        remediation="Designate a named Human Ethical Agent of Record with effective stop authority and fail-closed authorization for Class-H actions.",
        check_fn=_check_cp10_hear,
        file_exts=(".json", ".yaml", ".yml", ".toml", ".env"),
    ),
    Rule(
        control_id="CP.8",
        severity="CRITICAL",
        description="Autonomous agent code without Catastrophic Risk Threshold definitions.",
        remediation="Define deployment-specific emergency suspension criteria before ACT-3 or ACT-4 approval.",
        check_fn=_check_cp8_missing_crt,
        file_exts=(".py", ".js", ".ts", ".yaml", ".yml"),
    ),
    Rule(
        control_id="CP.4",
        severity="MEDIUM",
        description="Agent protocol or MCP surface detected; verify that it is governed as part of the Agentic Control Plane.",
        remediation="Document verified principals, authorization, delegation, policy context, evidence, revocation, and applicable CP.5 profiles for the protocol surface.",
        pattern=r"(mcp_server|ModelContextProtocol|StdioServerParameters|streamable.?http|sse_server|a2a_endpoint)",
        file_exts=(".py", ".js", ".ts"),
    ),
]
