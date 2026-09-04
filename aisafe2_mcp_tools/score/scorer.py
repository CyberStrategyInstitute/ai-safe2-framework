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

# Attestation bonus points — risk-weighted across all 13 CP.5.MCP controls.
# Higher likelihood / confirmed impact of the threat the control addresses,
# the more points attesting to it earns. Cap is 25; all 11 attested fields
# sum to 25 so full implementation earns full bonus.
#
# Risk tier 1 — RCE / confirmed high-impact incidents:
#   MCP-1 (5): OX Security RCE, biggest remote blind spot
#   MCP-9 (4): MCP-UPD 92.9% attack surface, zero interaction required
# Risk tier 2 — Confirmed financial / behavioral impact:
#   MCP-2 (3): Core injection defense
#   MCP-8 (3): $47K confirmed incident, 658x Phantom amplification
# Risk tier 3 — Stealth / delayed-profile threats:
#   MCP-11 (2): Rug pull, delayed_weeks temporal profile
#   MCP-4 (2): Source tamper detection
#   MCP-5 (2): Forensic foundation — audit trail
# Risk tier 4 — Architectural / emerging threats:
#   MCP-10 (1): Multi-agent lateral movement
#   MCP-6 (1): Egress control
#   MCP-12 (1): Swarm C2, semantically indistinguishable traffic
#   MCP-13 (1): Failure taxonomy correctness
ATTESTATION_POINTS = {
    "no_dynamic_commands": 5,       # MCP-1 — RCE tier, OX confirmed
    "context_tool_isolation": 4,    # MCP-9 — 92.9% attack surface (new)
    "output_sanitization": 3,       # MCP-2 — core injection defense
    "session_economics": 3,         # MCP-8 — $47K confirmed (new)
    "schema_temporal_profiling": 2, # MCP-11 — rug pull stealth (new)
    "source_hash": 2,               # MCP-4 — tamper detection
    "audit_logging": 2,             # MCP-5 — forensic foundation
    "multi_agent_provenance": 1,    # MCP-10 — lateral movement (new)
    "network_isolation": 1,         # MCP-6 — egress control
    "swarm_c2_controls": 1,         # MCP-12 — Swarm C2 (new)
    "failure_taxonomy": 1,          # MCP-13 — taxonomy correctness (new)
}
# Sum: 5+4+3+3+2+2+2+1+1+1+1 = 25

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
