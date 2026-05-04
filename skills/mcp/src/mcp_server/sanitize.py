"""
AI SAFE2 MCP Server — Output Sanitization (RISK-1 FIX)

Scans every tool return value for prompt injection patterns before the
result is returned to LLM clients (Claude Code, Codex, Cursor, etc.).

Threat addressed:
  Supply-chain attack against ai-safe2-controls-v3.0.json. If an attacker
  compromises the controls data file (malicious PR merge, poisoned CI/CD,
  typosquat distribution), they could embed instruction-override payloads
  in control descriptions or builder_problem fields. Without this layer,
  those payloads would reach the LLM as trusted tool-response context.

Architecture:
  - This is DEFENSE-IN-DEPTH over an already-hardened read-only surface.
  - Primary protection: no dynamic command construction + static read-only data.
  - This layer: catches content-level injection if the data file is tampered.
  - Limitation: regex is not exhaustive. Sufficiently obfuscated payloads may
    bypass detection. Complementary control: source integrity hash (RISK-2).

All matches are logged with pattern family, field path, and truncated preview
for forensic audit, then redacted with [SAFE2_REDACTED].
"""
from __future__ import annotations

import re
from typing import Any

import structlog

log = structlog.get_logger()

# ── Redaction marker ──────────────────────────────────────────────────────────
_REDACTION_MARKER = "[SAFE2_REDACTED]"

# ── Injection pattern library ─────────────────────────────────────────────────
# Each entry: (compiled_pattern, family_label)
# family_label is used in structured log output for alerting / SIEM correlation.
#
# Patterns cover:
#   1. Instruction override (most common injection class)
#   2. Role confusion / persona hijacking
#   3. Permission escalation (jailbreak, mode switches)
#   4. System prompt exfiltration
#   5. LLM-family special tokens (ChatML, Llama, Gemma, Mistral, Claude)
#   6. Zero-width / direction-override Unicode (invisible injection hiding)
#   7. Newline-based role separator injection
# ─────────────────────────────────────────────────────────────────────────────
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [

    # ── 1. Instruction override ───────────────────────────────────────────────
    (re.compile(
        r"ignore\s+(previous|all|prior|above|your)\s+"
        r"(instructions?|rules?|prompts?|constraints?|guidelines?|directives?)",
        re.IGNORECASE,
    ), "instruction_override"),

    (re.compile(
        r"disregard\s+(all\s+)?(previous|prior|your)?\s*"
        r"(instructions?|rules?|prompts?|guidelines?|constraints?)",
        re.IGNORECASE,
    ), "instruction_override"),

    (re.compile(
        r"forget\s+(all\s+)?(everything|previous|prior)?\s*"
        r"(instructions?|rules?|above|context)",
        re.IGNORECASE,
    ), "instruction_override"),

    (re.compile(
        r"\b(new|updated|revised|actual|real|corrected)\s+"
        r"(instructions?|task|objective|goal|mission|directive)\s*:",
        re.IGNORECASE,
    ), "instruction_override"),

    (re.compile(
        r"do\s+not\s+follow\s+(previous|prior|above|earlier)\s+"
        r"(instructions?|rules?|prompts?|guidelines?)",
        re.IGNORECASE,
    ), "instruction_override"),

    # ── 2. Role confusion / persona hijacking ─────────────────────────────────
    (re.compile(
        r"you\s+are\s+now\s+(a|an|the)\s+",
        re.IGNORECASE,
    ), "role_confusion"),

    (re.compile(
        r"\bact\s+as\s+(a|an|the|if\s+you\s+are)\s+",
        re.IGNORECASE,
    ), "role_confusion"),

    (re.compile(
        r"\bpretend\s+(to\s+be|you\s+are|that\s+you)\s+",
        re.IGNORECASE,
    ), "role_confusion"),

    (re.compile(
        r"your\s+(true|real|actual|hidden|secret|underlying)\s+"
        r"(self|purpose|goal|task|mission|identity|persona|role|nature)",
        re.IGNORECASE,
    ), "role_confusion"),

    (re.compile(
        r"switch\s+(to|into)\s+(developer|admin|god|unrestricted|root|privileged)\s+mode",
        re.IGNORECASE,
    ), "role_confusion"),

    (re.compile(
        r"\benable\s+(developer|debug|admin|unrestricted|god|root)\s+mode",
        re.IGNORECASE,
    ), "role_confusion"),

    # ── 3. Permission escalation / jailbreak ──────────────────────────────────
    (re.compile(
        r"dangerously[-_\s]?skip[-_\s]?permissions?",
        re.IGNORECASE,
    ), "permission_escalation"),

    (re.compile(
        r"\bbypass\s+(safety|security|restrictions?|guidelines?|filters?|controls?|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation"),

    (re.compile(
        r"\boverride\s+(safety|security|restrictions?|mode|protocol|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation"),

    (re.compile(r"\bjailbreak\b", re.IGNORECASE), "permission_escalation"),

    (re.compile(r"\bDAN\s+(mode|prompt|jailbreak|version)\b", re.IGNORECASE), "permission_escalation"),

    (re.compile(
        r"\b(remove|disable|turn\s+off)\s+(safety|security|restrictions?|filters?|guardrails?)",
        re.IGNORECASE,
    ), "permission_escalation"),

    # ── 4. System prompt exfiltration ─────────────────────────────────────────
    (re.compile(
        r"\b(reveal|show|print|output|repeat|display|leak|expose|share|return)\s+"
        r"(your\s+)?(system\s+prompt|instructions?|rules?|guidelines?|configuration)",
        re.IGNORECASE,
    ), "exfiltration"),

    (re.compile(
        r"what\s+(are\s+)?your\s+(instructions?|rules?|guidelines?|system\s+prompt|configuration)",
        re.IGNORECASE,
    ), "exfiltration"),

    (re.compile(
        r"\brepeat\s+(everything|all)\s+(above|before|prior|from\s+the\s+beginning)",
        re.IGNORECASE,
    ), "exfiltration"),

    # ── 5. LLM special tokens (family-agnostic) ───────────────────────────────
    # ChatML (OpenAI GPT, Mistral, many others)
    (re.compile(
        r"<\|?(im_start|im_end|endoftext|begin_of_text|end_of_text|"
        r"start_header_id|end_header_id|eot_id)\|?>",
        re.IGNORECASE,
    ), "special_token"),

    # Generic role markers (used in many fine-tuned models)
    (re.compile(
        r"<\|?(system|user|assistant|human|model)\|?>",
        re.IGNORECASE,
    ), "special_token"),

    # Llama / Alpaca instruction format
    (re.compile(r"\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\]", re.IGNORECASE), "special_token"),

    # Markdown role separators used in some training formats
    (re.compile(r"^#{1,4}\s*(System|Human|Assistant|Instruction|User)\s*:", re.IGNORECASE | re.MULTILINE), "special_token"),

    # ── 6. Zero-width / direction-override Unicode ────────────────────────────
    # These are invisible in most renderers. Used to hide injection text from humans.
    # Ranges: zero-width space/joiners, direction overrides, BOM, soft hyphen.
    (re.compile(
        r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff\u00ad]"
    ), "zero_width_char"),

    # ── 7. Newline-based role separator injection ──────────────────────────────
    # Attacker pads with newlines then inserts a fake role marker.
    (re.compile(
        r"[\r\n]{2,}\s*"
        r"(system|user|assistant|human|ai|<\|system\|>|<\|user\|>|<\|assistant\|>)\s*:",
        re.IGNORECASE,
    ), "role_separator_injection"),
]


def sanitize_output(value: Any, _field_path: str = "root") -> Any:
    """
    Recursively scan and sanitize a tool output value for injection patterns.

    Behavior by type:
      str  — scan all patterns; replace each match with [SAFE2_REDACTED]; log warnings
      dict — recurse over values (keys are not scanned — they are internal constants)
      list — recurse over items
      other (int, float, bool, None) — returned unchanged

    Args:
        value: The tool return value to sanitize.
        _field_path: Dotted path for structured log context (e.g., "root.controls[0].description").

    Returns:
        Sanitized value of the same type.
    """
    if isinstance(value, str):
        for pattern, family in _INJECTION_PATTERNS:
            if pattern.search(value):
                log.warning(
                    "sanitize.injection_detected",
                    pattern_family=family,
                    field_path=_field_path,
                    preview=value[:140].replace("\n", "\\n").replace("\r", "\\r"),
                )
                value = pattern.sub(_REDACTION_MARKER, value)
        return value

    if isinstance(value, dict):
        return {
            k: sanitize_output(v, f"{_field_path}.{k}")
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            sanitize_output(item, f"{_field_path}[{i}]")
            for i, item in enumerate(value)
        ]

    # int, float, bool, None — no injection possible
    return value


def contains_injection(text: str) -> bool:
    """
    Return True if text contains any known injection pattern.
    Utility for testing and external validation.
    """
    return any(pat.search(text) for pat, _ in _INJECTION_PATTERNS)


def get_pattern_families() -> list[str]:
    """Return deduplicated list of pattern family names. For test inspection."""
    seen: set[str] = set()
    return [f for _, f in _INJECTION_PATTERNS if not (f in seen or seen.add(f))]  # type: ignore[func-returns-value]
