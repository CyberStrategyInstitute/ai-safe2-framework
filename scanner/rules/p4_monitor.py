"""
AI SAFE2 v3.0 Scanner — Pillar 4: Engage & Monitor Rules
Covers: P4.T7.x (Engage/HITL), P4.T8.x (Monitor), M4.4-M4.8 (v3.0 new controls)
"""
from __future__ import annotations

import re
from .base import Rule


def _check_bedrock_unmonitored(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    M4.8 — Cloud AI Platform-Specific Monitoring
    Detect AWS Bedrock API calls that update guardrails or data sources
    without monitoring wrappers — the confirmed Bedrock Guardrail poisoning attack path.
    """
    findings = []
    # High-risk Bedrock API calls that standard CloudTrail does not flag
    high_risk_bedrock = [
        r"UpdateGuardrail", r"update_guardrail",
        r"UpdateDataSource", r"update_data_source",
        r"UpdateKnowledgeBase", r"update_knowledge_base",
        r"DeleteGuardrail", r"delete_guardrail",
        r"bedrock_agent\.update", r"bedrock-agent.*update",
    ]
    monitoring_words = {
        "monitor", "alert", "log", "audit", "cloudwatch", "siem",
        "notify", "alarm", "m4_8", "platform_monitor", "security_log"
    }

    for i, line in enumerate(lines):
        for pat in high_risk_bedrock:
            if re.search(pat, line, re.IGNORECASE):
                context = " ".join(lines[max(0, i - 5):i + 5]).lower()
                if not any(w in context for w in monitoring_words):
                    findings.append((
                        i + 1,
                        f"High-risk Bedrock API call without monitoring: {line.strip()[:60]}"
                    ))
    return findings


def _check_tool_invocation_without_baseline(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    M4.5 — Tool-Misuse Detection Controls
    Detect tool/function invocation patterns without baseline monitoring
    or invocation anomaly detection.
    """
    findings = []
    # Tool registration patterns (agent tool definitions)
    tool_def_patterns = [
        r"@tool\b", r"Tool\s*\(", r"StructuredTool\s*\(",
        r"tool_schemas\s*=", r"tools\s*=\s*\[",
        r'"function":\s*\{', r'"tools":\s*\[',
        r"function_definitions\s*=",
    ]
    monitoring_words = {
        "baseline", "monitor", "track", "invocation_log", "tool_audit",
        "anomaly", "m4_5", "tool_monitor", "alert"
    }

    # Find tool definitions
    for i, line in enumerate(lines):
        for pat in tool_def_patterns:
            if re.search(pat, line, re.IGNORECASE):
                # Look in the broader file for monitoring patterns
                if not any(w in content.lower() for w in monitoring_words):
                    findings.append((
                        i + 1,
                        f"Tool definition without invocation monitoring: {line.strip()[:60]}"
                    ))
                break  # one finding per tool block
    return findings


def _check_missing_hitl(content: str, lines: list[str], filepath: str) -> list[tuple[int, str]]:
    """
    P4.T7.1 — Human Approval Workflows
    Detect irreversible or high-impact tool calls without human-in-the-loop checkpoints.
    """
    findings = []
    # High-impact tool patterns that should have HITL gates
    high_impact_patterns = [
        r"send_email\s*\(", r"email\.send\s*\(", r"smtp\.",
        r"delete\s*\(", r"DROP\s+TABLE", r"\.delete\s*\(",
        r"payment\s*\.", r"charge\s*\(", r"transfer\s*\(",
        r"subprocess\.", r"os\.remove\s*\(", r"shutil\.rmtree",
        r"requests\.(post|put|delete|patch)\s*\(",
        r"httpx\.(post|put|delete|patch)\s*\(",
    ]
    hitl_words = {
        "human_approval", "require_approval", "confirm", "checkpoint",
        "hitl", "human_in_the_loop", "await_approval", "manual_review",
        "p4_t7", "approval_gate", "human_review"
    }

    for i, line in enumerate(lines):
        for pat in high_impact_patterns:
            if re.search(pat, line, re.IGNORECASE):
                context = " ".join(lines[max(0, i - 10):i + 5]).lower()
                if not any(w in context for w in hitl_words):
                    findings.append((
                        i + 1,
                        f"High-impact action without HITL checkpoint: {line.strip()[:60]}"
                    ))
                break
    return findings


P4_RULES: list[Rule] = [

    # ── P4.T7.x Engage / HITL ─────────────────────────────────────────────────

    Rule(
        control_id="P4.T7.1",
        severity="HIGH",
        description="High-impact agent action (email send, delete, payment, HTTP write) "
                    "without Human-in-the-Loop checkpoint.",
        remediation="Apply P4.T7.1: require human approval before irreversible or financially "
                    "material actions. For ACT-3/4 agents, this maps to the CP.10 HEAR Doctrine "
                    "Class-H action protocol.",
        check_fn=_check_missing_hitl,
        file_exts=(".py", ".js", ".ts"),
    ),

    # ── P4.T8.x Monitor ───────────────────────────────────────────────────────

    Rule(
        control_id="P4.T8.3",
        severity="HIGH",
        description="No SIEM integration or security event forwarding found in agent code.",
        remediation="Apply P4.T8.3: forward security events to a SIEM. "
                    "At minimum, log authentication events, tool invocations, "
                    "and anomaly detections to a centralized, tamper-evident store.",
        pattern=r"(?i)(siem|splunk|elastic|datadog|cloudwatch|security_log|audit_log)",
        file_exts=(".py", ".js", ".ts", ".yaml"),
    ),
    Rule(
        control_id="P4.T8.5",
        severity="MEDIUM",
        description="No token cost tracking found — no protection against runaway API spend.",
        remediation="Apply P4.T8.5: instrument token usage per agent call. "
                    "Set budget quotas and alert on threshold breach. "
                    "Combine with F3.2 recursion limit for full cost protection.",
        pattern=r"(?i)(token_count|usage\.total_tokens|prompt_tokens|completion_tokens)",
        file_exts=(".py", ".js", ".ts"),
    ),

    # ── M4.4-M4.8 New v3.0 Controls ──────────────────────────────────────────

    # M4.5 — Tool-Misuse Detection
    Rule(
        control_id="M4.5",
        severity="HIGH",
        description="Agent tool definitions present without invocation baseline monitoring "
                    "or anomaly detection — tool squatting and misuse undetectable.",
        remediation="Apply M4.5: establish tool invocation baselines. Monitor for unexpected "
                    "tools, out-of-scope parameters, and anomalous call frequency. "
                    "Treat tool changes as supply chain events requiring review.",
        check_fn=_check_tool_invocation_without_baseline,
        file_exts=(".py", ".js", ".ts", ".json"),
    ),

    # M4.7 — Jailbreak & Injection Telemetry
    Rule(
        control_id="M4.7",
        severity="HIGH",
        description="No jailbreak or injection attempt telemetry found — "
                    "attack patterns are invisible in production.",
        remediation="Apply M4.7: implement a unified telemetry layer that classifies "
                    "and logs all injection and jailbreak attempts by technique "
                    "(direct, indirect, cognitive, encoding). Feed findings to E5.4.",
        pattern=r"(?i)(jailbreak|injection_detect|prompt_guard|rebuff|llm_guard|prompt_firewall)",
        file_exts=(".py", ".js", ".ts"),
    ),

    # M4.8 — Cloud AI Platform-Specific Monitoring
    Rule(
        control_id="M4.8",
        severity="CRITICAL",
        description="High-risk Bedrock or Azure AI Foundry API call (UpdateGuardrail, "
                    "UpdateDataSource, UpdateKnowledgeBase) without monitoring wrapper — "
                    "confirmed Guardrail poisoning attack path not covered by standard CloudTrail.",
        remediation="Apply M4.8: add dedicated CloudWatch alerts for UpdateGuardrail and "
                    "UpdateDataSource API calls. These are not flagged by standard monitoring. "
                    "Treat any unauthorized call as a security incident.",
        check_fn=_check_bedrock_unmonitored,
        file_exts=(".py", ".js", ".ts"),
    ),
    Rule(
        control_id="M4.8",
        severity="HIGH",
        description="Azure AI Foundry configuration update without monitoring — "
                    "platform-specific attack path not covered by generic monitoring.",
        remediation="Apply M4.8: implement Azure Monitor alerts for AI Foundry configuration "
                    "changes. Treat config updates as security events requiring audit trails.",
        pattern=r"(?i)(azure.*ai.*foundry.*update|azure.*openai.*deploy|az_ml.*update)",
        file_exts=(".py", ".js", ".ts"),
    ),
]
