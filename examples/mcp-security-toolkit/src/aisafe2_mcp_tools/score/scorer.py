"""
AI SAFE2 MCP Security Toolkit — mcp-score: Scoring Rubric
CP.5.MCP scoring constants, rating thresholds, and attestation bonus computation.
Separated so scoring logic can be adjusted without touching assessment logic.

Rubric (100 points max):
  Authentication        0–25
  TLS                   0–15 (12 for HTTPS; 15 reserved for TLS 1.3 verification)
  Tool injection scan   0–20
  FSP patterns          0–10
  Security headers      0–10
  Rate limiting         0–10
  Session ID in URL     0–5
  SSRF surface          0–5
  Builder attestation   0–25 bonus (capped at 100 total)

Badge threshold: 70+
"""
from __future__ import annotations

from aisafe2_mcp_tools.score.models import AttestationData

# Score thresholds
BADGE_THRESHOLD = 70

RATINGS = [
    (90, "Secure"),
    (70, "Acceptable"),
    (50, "Elevated Risk"),
    (30, "High Risk"),
    (0,  "Critical"),
]

# Attestation bonus points per control (max 25 total)
ATTESTATION_POINTS = {
    "no_dynamic_commands": 8,    # MCP-1 — biggest remote blind spot
    "output_sanitization": 5,    # MCP-2 — library reference verifiable
    "source_hash": 4,            # MCP-4 — tamper detection
    "audit_logging": 4,          # MCP-5 — log evidence
    "network_isolation": 4,      # MCP-6 — localhost-only binding
}

REMEDIATION_URLS = {
    "AUTH":    "https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar#mcp-7",
    "TLS":     "https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar#mcp-6",
    "INJECTION":"https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar#mcp-2",
    "RATE":    "https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/00-cross-pillar#mcp-6",
}


def get_rating(score: int) -> str:
    """Return text rating for a numeric score."""
    for threshold, label in RATINGS:
        if score >= threshold:
            return label
    return "Critical"


def compute_attestation_bonus(att: AttestationData) -> int:
    """
    Compute bonus points from builder attestation file.
    Controls not verifiable remotely are credited here (max 25, total capped at 100).
    """
    bonus = 0
    if att.no_dynamic_commands:
        bonus += ATTESTATION_POINTS["no_dynamic_commands"]
    if att.output_sanitization:
        bonus += ATTESTATION_POINTS["output_sanitization"]
    if att.source_hash:
        bonus += ATTESTATION_POINTS["source_hash"]
    if att.audit_logging:
        bonus += ATTESTATION_POINTS["audit_logging"]
    if att.network_isolation and (
        "localhost" in att.network_isolation.lower()
        or "127.0.0.1" in att.network_isolation
    ):
        bonus += ATTESTATION_POINTS["network_isolation"]
    return min(25, bonus)


def is_badge_eligible(score: int) -> bool:
    return score >= BADGE_THRESHOLD
