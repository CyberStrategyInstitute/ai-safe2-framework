"""
AI SAFE2 MCP Security Toolkit — mcp-scan: Finding Data Model
Stable finding IDs, severity constants, and the Finding dataclass.

Finding IDs are permanent identifiers. They appear in:
  - CLI output
  - JSON reports
  - Fix templates (fixes/RCE-001.template etc.)
  - CP.5.MCP compliance mapping
  - Remediation documentation

Do NOT change finding IDs after publication — downstream tooling and
audit records reference them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


# Stable severity order for sorting (critical first)
SEVERITY_ORDER: dict[str, int] = {
    "critical": 4, "high": 3, "medium": 2, "low": 1,
}

# CP.5.MCP control mapping for each finding prefix
# Mapped to the CP.5.MCP v3.1 profile (MCP-1..MCP-19, 00-cross-pillar/
# cp5_mcp_server_security.md). The previous map used the retired 13-control
# numbering, so every finding cited the wrong control.
CONTROL_MAP: dict[str, str] = {
    "RCE": "MCP-1",   # Command Construction Safety
    "INJ": "MCP-2",   # Return-Path Content Sanitization
    "SEC": "MCP-7",   # Trust Establishment (overrides below)
    "AUTH": "MCP-4",  # Server/Binary Integrity (stdio verification)
    "RL": "MCP-8",    # Economic Ceiling
    "LOG": "MCP-5",   # Tool Invocation Audit
    "MEM": "MCP-12",  # Principal-Scoped State
    "DEP": "MCP-4",   # Server/Binary Integrity (supply chain)
    "CONF": "MCP-9",  # Secret Boundary
    "CTI": "MCP-9",   # Secret Boundary (retrieval-to-disclosure chain)
    "STP": "MCP-11",  # Catalog Provenance
    "SWM": "MCP-10",  # Delegation Edge Monitoring
}

# Finding-ID-level overrides applied before class prefix lookup.
FINDING_CONTROL_OVERRIDE: dict[str, str] = {
    "RCE-005": "MCP-6",   # path traversal: input validation against authorized schema
    "INJ-003": "MCP-19",  # SSRF boundaries are part of authorization-chain integrity
    "INJ-103": "MCP-19",
    "INJ-005": "MCP-11",  # dynamic registration / rug pull: catalog provenance
    "SEC-001": "MCP-3",   # 0.0.0.0 bind: least-privilege exposure
    "SEC-003": "MCP-19",  # token forwarding: intended resource / audience
    "SEC-004": "MCP-19",  # redirect_uri: redirect/resource binding
    "SEC-005": "MCP-12",  # shared session/tenant state
    "SEC-006": "MCP-6",   # path containment
    "SEC-106": "MCP-6",
    "SEC-007": "MCP-9",   # hardcoded credential
}

# All valid finding IDs — used for ID format validation
VALID_FINDING_IDS: set[str] = {
    # Critical — RCE class
    "RCE-001", "RCE-002", "RCE-003", "RCE-004", "RCE-005", "RCE-006",
    "RCE-007", "RCE-008", "RCE-009", "RCE-101", "RCE-102", "RCE-103",
    # High — Injection and security
    "INJ-001", "INJ-002", "INJ-003", "INJ-004", "INJ-005",
    "SEC-001", "SEC-002", "SEC-003", "SEC-004", "SEC-005", "SEC-006",
    "SEC-007", "SEC-106", "INJ-103",
    # Medium — Operational
    "RL-001", "RL-002", "LOG-001", "LOG-002", "MEM-001",
    "CTI-001", "STP-001", "SWM-001",
    # Low — Hygiene
    "AUTH-001", "DEP-001", "DEP-002", "CONF-001",
}


@dataclass
class Finding:
    """
    A single security finding from mcp-scan static analysis.

    finding_id: Stable ID (e.g., "RCE-001"). Never changes after publication.
    severity: critical / high / medium / low
    cp5_control: AI SAFE2 v3.0 CP.5.MCP control reference (e.g., "MCP-1")
    title: Short title for display
    description: Detailed description of the vulnerability and why it matters
    file: Relative path to the file containing the finding
    line: Line number (1-indexed)
    code_snippet: The relevant code line (truncated to 120 chars)
    remediation: Specific, actionable fix guidance
    cve_refs: CVE identifiers this finding relates to
    auto_fixable: True if mcp-scan fix --auto can safely apply a template fix
    manual_required: True for CRITICAL findings — always requires human review
    """
    finding_id: str
    severity: str          # Use Severity enum values
    cp5_control: str
    title: str
    description: str
    file: str
    line: int
    code_snippet: str
    remediation: str
    cve_refs: list[str] = field(default_factory=list)
    auto_fixable: bool = False
    manual_required: bool = False  # Always True for critical

    def __post_init__(self) -> None:
        # Invariant: critical findings are never auto-fixable
        if self.severity == Severity.CRITICAL:
            self.auto_fixable = False
            self.manual_required = True

    @property
    def severity_rank(self) -> int:
        return SEVERITY_ORDER.get(self.severity, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "cp5_control": self.cp5_control,
            "title": self.title,
            "description": self.description,
            "file": self.file,
            "line": self.line,
            "code_snippet": self.code_snippet,
            "remediation": self.remediation,
            "cve_refs": self.cve_refs,
            "auto_fixable": self.auto_fixable,
            "manual_required": self.manual_required,
        }

    @staticmethod
    def control_for(finding_id: str) -> str:
        """Return the CP.5.MCP control for a finding ID.

        Checks FINDING_CONTROL_OVERRIDE first (finding-ID-level precision),
        then falls back to the class prefix in CONTROL_MAP.
        """
        if finding_id in FINDING_CONTROL_OVERRIDE:
            return FINDING_CONTROL_OVERRIDE[finding_id]
        prefix = finding_id.split("-")[0]
        return CONTROL_MAP.get(prefix, "MCP-2")
