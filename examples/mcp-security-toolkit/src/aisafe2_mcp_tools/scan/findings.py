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
CONTROL_MAP: dict[str, str] = {
    "RCE": "MCP-1",   # No Dynamic Command Construction
    "INJ": "MCP-2",   # Output Sanitization Before LLM Return
    "SEC": "MCP-4",   # STDIO Transport Integrity / Auth
    "AUTH": "MCP-4",
    "RL": "MCP-6",    # Network Isolation / Rate Limiting (default; RL-002 overridden below)
    "LOG": "MCP-5",   # Tool Invocation Audit Log (LOG-002 also maps here)
    "MEM": "MCP-10",  # Multi-Agent Provenance and Delegation Edge Monitoring
    "DEP": "MCP-3",   # Registry Provenance Verification
    "CONF": "MCP-6",
    "CTI": "MCP-9",   # Context-Tool Isolation
    "STP": "MCP-11",  # Schema Temporal Profiling
    "SWM": "MCP-12",  # Swarm C2 Detection Controls
}

# Finding-ID-level overrides applied before class prefix lookup.
# Use when a single prefix class spans multiple CP.5.MCP controls.
FINDING_CONTROL_OVERRIDE: dict[str, str] = {
    "RL-002": "MCP-8",  # LLM API cost budget — Session Economics, not Network Isolation
}

# All valid finding IDs — used for ID format validation
VALID_FINDING_IDS: set[str] = {
    # Critical — RCE class
    "RCE-001", "RCE-002", "RCE-003", "RCE-004", "RCE-005", "RCE-006",
    # High — Injection and security
    "INJ-001", "INJ-002", "INJ-003", "INJ-004", "INJ-005",
    "SEC-001", "SEC-002", "SEC-003", "SEC-004", "SEC-005", "SEC-006",
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

    def to_dict(self) -> dict:
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
