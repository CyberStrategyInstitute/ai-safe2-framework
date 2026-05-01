"""
AI SAFE2 MCP Security Toolkit — Shared Injection Pattern Library
Single source of truth. Used by mcp-score, mcp-scan, and mcp-safe-wrap.

Pattern coverage aligns with AI SAFE2 v3.0 CP.5.MCP-2 (Output Sanitization)
and CP.5.MCP-9 (Context–Tool Isolation).

Sources:
  - OX Security April 2026 advisory
  - CyberArk Full Schema Poisoning (FSP) research
  - Invariant Labs Tool Poisoning Attack (TPA) taxonomy
  - OWASP LLM Top 10 2025 — LLM01 Prompt Injection
  - CSI Research Note 023 v2.0
"""
from __future__ import annotations

import re
from typing import NamedTuple

REDACTION_MARKER = "[SAFE2_REDACTED]"


class Pattern(NamedTuple):
    regex: re.Pattern[str]
    family: str
    severity: str        # "critical" | "high" | "medium"
    description: str
    cp5_control: str     # AI SAFE2 CP.5.MCP control ID


# ── Core injection pattern library ────────────────────────────────────────────

INJECTION_PATTERNS: list[Pattern] = [

    # ── Instruction override ──────────────────────────────────────────────────
    Pattern(re.compile(
        r"ignore\s+(\w+\s+)?(previous|all|prior|above|your)\s+(\w+\s+)?"
        r"(instructions?|rules?|prompts?|constraints?|guidelines?|directives?)",
        re.IGNORECASE,
    ), "instruction_override", "critical",
        "Classic instruction override — highest-frequency injection class",
        "MCP-2"),

    Pattern(re.compile(
        r"disregard\s+(all\s+)?(previous|prior|your)?\s*"
        r"(instructions?|rules?|prompts?|guidelines?|constraints?)",
        re.IGNORECASE,
    ), "instruction_override", "critical",
        "Disregard pattern — synonymous with ignore-previous class",
        "MCP-2"),

    Pattern(re.compile(
        r"forget\s+(all\s+)?(everything|previous|prior)?\s*"
        r"(instructions?|rules?|above|context)",
        re.IGNORECASE,
    ), "instruction_override", "critical",
        "Forget-instructions pattern",
        "MCP-2"),

    Pattern(re.compile(
        r"\b(new|updated|revised|actual|real|corrected)\s+"
        r"(instructions?|task|objective|goal|mission|directive)\s*:",
        re.IGNORECASE,
    ), "instruction_override", "high",
        "Inline instruction replacement pattern",
        "MCP-2"),

    Pattern(re.compile(
        r"do\s+not\s+follow\s+(previous|prior|above|earlier)\s+"
        r"(instructions?|rules?|prompts?|guidelines?)",
        re.IGNORECASE,
    ), "instruction_override", "high",
        "Explicit instruction negation",
        "MCP-2"),

    # ── Role confusion / persona hijacking ────────────────────────────────────
    Pattern(re.compile(
        r"you\s+are\s+now\s+(a|an|the)\s+",
        re.IGNORECASE,
    ), "role_confusion", "critical",
        "You-are-now persona reassignment",
        "MCP-2"),

    Pattern(re.compile(
        r"\bact\s+as\s+(?:(a|an|the|if\s+you\s+(are|were|have))\s+|\w+\s*)",
        re.IGNORECASE,
    ), "role_confusion", "high",
        "Act-as persona injection",
        "MCP-2"),

    Pattern(re.compile(
        r"\bpretend\s+(to\s+be|you\s+are|that\s+you)\s+",
        re.IGNORECASE,
    ), "role_confusion", "high",
        "Pretend-to-be persona injection",
        "MCP-2"),

    Pattern(re.compile(
        r"your\s+(true|real|actual|hidden|secret|underlying)\s+"
        r"(self|purpose|goal|task|mission|identity|persona|role|nature)",
        re.IGNORECASE,
    ), "role_confusion", "high",
        "Hidden-purpose disclosure attempt",
        "MCP-2"),

    Pattern(re.compile(
        r"\b(switch|enter|activate|enable)\s+(into\s+)?"
        r"(developer|admin|god|unrestricted|root|privileged|jailbreak)\s+mode",
        re.IGNORECASE,
    ), "role_confusion", "critical",
        "Mode-switch jailbreak pattern",
        "MCP-2"),

    # ── Permission escalation ─────────────────────────────────────────────────
    Pattern(re.compile(
        r"dangerously[-_\s]?skip[-_\s]?permissions?",
        re.IGNORECASE,
    ), "permission_escalation", "critical",
        "Claude Code --dangerously-skip-permissions injection (OX CVE class)",
        "MCP-2"),

    Pattern(re.compile(
        r"\bbypass\s+(safety|security|restrictions?|guidelines?|filters?|controls?|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation", "critical",
        "Safety bypass pattern",
        "MCP-2"),

    Pattern(re.compile(
        r"\boverride\s+(safety|security|restrictions?|mode|protocol|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation", "high",
        "Security override pattern",
        "MCP-2"),

    Pattern(re.compile(r"\bjailbreak\b", re.IGNORECASE),
        "permission_escalation", "critical",
        "Explicit jailbreak keyword",
        "MCP-2"),

    Pattern(re.compile(r"\bDAN\s+(mode|prompt|jailbreak|version)\b", re.IGNORECASE),
        "permission_escalation", "critical",
        "DAN jailbreak variant",
        "MCP-2"),

    Pattern(re.compile(
        r"\b(remove|disable|turn\s+off)\s+(\w+\s+)?"
        r"(safety|security|restrictions?|filters?|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation", "critical",
        "Explicit safety removal (with optional qualifier word)",
        "MCP-2"),

    # ── System prompt exfiltration ────────────────────────────────────────────
    Pattern(re.compile(
        r"\b(reveal|show|print|output|repeat|display|leak|expose|share|return)\s+"
        r"(your\s+)?(system\s+prompt|instructions?|rules?|guidelines?|configuration)",
        re.IGNORECASE,
    ), "exfiltration", "critical",
        "System prompt exfiltration attempt",
        "MCP-2"),

    Pattern(re.compile(
        r"\brepeat\s+(everything|all)\s+(above|before|prior|from\s+the\s+beginning)",
        re.IGNORECASE,
    ), "exfiltration", "high",
        "Repeat-all content extraction",
        "MCP-2"),

    # ── Full Schema Poisoning (FSP) patterns — CyberArk research ─────────────
    # These appear in parameter names, enum values, response schemas
    Pattern(re.compile(
        r"__inject__|__override__|__exec__|__cmd__|__eval__",
        re.IGNORECASE,
    ), "fsp_schema_poisoning", "critical",
        "FSP double-underscore injection marker in schema fields (CyberArk research)",
        "MCP-2"),

    Pattern(re.compile(
        r'"\w+"\s*:\s*"[^"]*\b(ignore|override|bypass|jailbreak|inject)\b[^"]*"',
        re.IGNORECASE,
    ), "fsp_schema_poisoning", "high",
        "Injection language embedded in JSON schema value",
        "MCP-2"),

    # ── LLM special tokens (family-agnostic) ─────────────────────────────────
    Pattern(re.compile(
        r"<\|?(im_start|im_end|endoftext|begin_of_text|end_of_text|"
        r"start_header_id|end_header_id|eot_id)\|?>",
        re.IGNORECASE,
    ), "special_token", "critical",
        "ChatML / Llama family special tokens",
        "MCP-2"),

    Pattern(re.compile(
        r"<\|?(system|user|assistant|human|model)\|?>",
        re.IGNORECASE,
    ), "special_token", "high",
        "Role demarcation special tokens",
        "MCP-2"),

    Pattern(re.compile(r"\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\]", re.IGNORECASE),
        "special_token", "high",
        "Llama/Alpaca instruction format tokens",
        "MCP-2"),

    Pattern(re.compile(
        r"^#{1,4}\s*(System|Human|Assistant|Instruction|User)\s*:",
        re.IGNORECASE | re.MULTILINE,
    ), "special_token", "high",
        "Markdown role separator (training format injection)",
        "MCP-2"),

    # ── Zero-width / direction-override Unicode ───────────────────────────────
    Pattern(re.compile(
        r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff\u00ad]"
    ), "zero_width", "critical",
        "Invisible zero-width / direction-override Unicode — used to hide injection from humans",
        "MCP-2"),

    # ── Role separator injection ──────────────────────────────────────────────
    Pattern(re.compile(
        r"[\r\n]{2,}\s*"
        r"(system|user|assistant|human|ai|<\|system\|>|<\|user\|>)\s*:",
        re.IGNORECASE,
    ), "role_separator", "high",
        "Newline-padded role separator injection",
        "MCP-2"),

    # ── ATPA — Advanced Tool Poisoning (tool response steering) ──────────────
    # Malicious instructions in tool response bodies that steer re-invocation
    Pattern(re.compile(
        r"\b(the\s+)?(answer\s+is\s+incomplete|verify\s+again|call\s+this\s+tool\s+again"
        r"|re[-_]?invoke|retry\s+this\s+tool|additional\s+verification\s+required)",
        re.IGNORECASE,
    ), "atpa_steering", "high",
        "ATPA response-body steering — instructs agent to re-invoke tool (billing amplification vector)",
        "MCP-2"),

    # ── MCP-UPD Parasitic Toolchain patterns ─────────────────────────────────
    Pattern(re.compile(
        r"\b(collect|gather|retrieve|read|access|obtain)\s+"
        r"(all\s+)?(credentials?|api\s+keys?|tokens?|passwords?|secrets?|ssh\s+keys?)",
        re.IGNORECASE,
    ), "mcp_upd", "critical",
        "MCP-UPD privacy collection phase — credential harvesting instruction",
        "MCP-2"),

    Pattern(re.compile(
        r"\b(send|transmit|post|upload|forward|exfiltrate|email)\s+"
        r"(this\s+)?(data|information|content|result|output|credentials?)\s+"
        r"(to|at)\s+",
        re.IGNORECASE,
    ), "mcp_upd", "critical",
        "MCP-UPD disclosure phase — data transmission instruction",
        "MCP-2"),
]

# ── SSRF-enabling URL parameter patterns ──────────────────────────────────────
# Used by mcp-score to detect SSRF surface in tool schemas

SSRF_URL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'"type"\s*:\s*"string".*?"format"\s*:\s*"uri"', re.DOTALL),
    re.compile(r'"(url|endpoint|webhook|callback|redirect|target|host|uri)"\s*:', re.IGNORECASE),
]

# Blocked URL patterns for SSRF prevention in mcp-safe-wrap proxy
SSRF_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"https?://169\.254\.169\.254"),           # AWS IMDSv1
    re.compile(r"https?://169\.254\.170\.2"),             # ECS credential endpoint
    re.compile(r"https?://fd00:ec2::254"),                # IPv6 IMDS
    re.compile(r"https?://(localhost|127\.\d+\.\d+\.\d+|::1)(:\d+)?"),  # Loopback
    re.compile(r"https?://10\.\d+\.\d+\.\d+"),           # RFC 1918
    re.compile(r"https?://172\.(1[6-9]|2\d|3[01])\.\d+\.\d+"),  # RFC 1918
    re.compile(r"https?://192\.168\.\d+\.\d+"),           # RFC 1918
    re.compile(r"https?://0\.0\.0\.0"),                  # All-interfaces
    re.compile(r"file://"),                               # File scheme
    re.compile(r"https?://metadata\.google\.internal"),   # GCP IMDS
]


def scan_text(text: str) -> list[tuple[Pattern, str]]:
    """
    Scan text for all injection patterns.
    Returns list of (Pattern, matched_text) tuples.
    """
    findings: list[tuple[Pattern, str]] = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.regex.search(text)
        if match:
            findings.append((pattern, match.group(0)[:100]))
    return findings


def sanitize_text(text: str) -> tuple[str, list[tuple[Pattern, str]]]:
    """
    Sanitize text by redacting all injection patterns.
    Returns (sanitized_text, list_of_findings).
    """
    findings = scan_text(text)
    sanitized = text
    for pattern, _ in findings:
        sanitized = pattern.regex.sub(REDACTION_MARKER, sanitized)
    return sanitized, findings


def sanitize_value(value: object, field_path: str = "root") -> tuple[object, list[dict]]:
    """
    Recursively sanitize a JSON-compatible value.
    Returns (sanitized_value, list_of_finding_dicts).
    """
    all_findings: list[dict] = []

    if isinstance(value, str):
        sanitized, findings = sanitize_text(value)
        for pattern, match in findings:
            all_findings.append({
                "field_path": field_path,
                "family": pattern.family,
                "severity": pattern.severity,
                "control": pattern.cp5_control,
                "description": pattern.description,
                "match_preview": match,
            })
        return sanitized, all_findings

    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            sanitized_v, findings = sanitize_value(v, f"{field_path}.{k}")
            result[k] = sanitized_v
            all_findings.extend(findings)
        return result, all_findings

    if isinstance(value, list):
        result_list = []
        for i, item in enumerate(value):
            sanitized_item, findings = sanitize_value(item, f"{field_path}[{i}]")
            result_list.append(sanitized_item)
            all_findings.extend(findings)
        return result_list, all_findings

    return value, []
