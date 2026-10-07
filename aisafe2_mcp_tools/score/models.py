"""
AI SAFE2 MCP Security Toolkit — mcp-score: Data Models
CheckResult and AttestationData dataclasses.
Separated to break circular imports between assessor.py and checker sub-modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    check_id: str
    name: str
    cp5_control: str
    passed: bool
    score: int
    max_score: int
    severity: str
    detail: str
    remediation: str
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "cp5_control": self.cp5_control,
            "passed": self.passed,
            "score": self.score,
            "max_score": self.max_score,
            "severity": self.severity,
            "detail": self.detail,
            "remediation": self.remediation,
            "findings": self.findings,
        }


@dataclass
class AttestationData:
    present: bool = False
    server_name: str = ""
    framework: str = ""
    no_dynamic_commands: bool = False
    output_sanitization: str = ""
    source_hash: str = ""
    rate_limiting: bool = False
    audit_logging: bool = False
    network_isolation: str = ""
    # Attestation fields keyed MCP-8_* .. MCP-13_* in the file (schema v1.1).
    # Those key prefixes use the retired v3.0 numbering and are not v3.1 control IDs.
    session_economics: bool = False         # MCP-8: token budget + cost ceiling declared
    context_tool_isolation: str = ""        # MCP-9: isolation library/method reference
    multi_agent_provenance: bool = False    # MCP-10: CP.9 lineage tokens in use
    schema_temporal_profiling: bool = False # MCP-11: tools/list hash pinned
    swarm_c2_controls: bool = False         # MCP-12: topology monitoring deployed
    failure_taxonomy: bool = False          # MCP-13: CP.1 tags in audit events
    last_assessed: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreReport:
    server_url: str
    assessment_timestamp: str
    total_score: int
    max_possible: int
    base_score: int
    attestation_bonus: int
    rating: str
    badge_eligible: bool
    checks: list[CheckResult]
    attestation: AttestationData
    tool_count: int
    tools_scanned: list[str]
    errors: list[str]
    duration_seconds: float
    # Self-declared /.well-known/mcp-security.json claims. Reported, never scored:
    # an unauthenticated server-published file cannot raise its own grade.
    attestation_claimed_points: int = 0
    # Checks whose failure means hostile content was observed (tool-description
    # injection / schema poisoning). Any entry caps the score and blocks the badge
    # and the CI gate, regardless of the total.
    blocking_findings: list[str] = field(default_factory=list)
