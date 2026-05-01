"""
AI SAFE2 MCP Security Toolkit — mcp-score: Data Models
CheckResult and AttestationData dataclasses.
Separated to break circular imports between assessor.py and checker sub-modules.
"""
from __future__ import annotations
from dataclasses import dataclass, field


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
    findings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
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
    # MCP-8 through MCP-13 attestation fields (schema v1.1)
    session_economics: bool = False         # MCP-8: token budget + cost ceiling declared
    context_tool_isolation: str = ""        # MCP-9: isolation library/method reference
    multi_agent_provenance: bool = False    # MCP-10: CP.9 lineage tokens in use
    schema_temporal_profiling: bool = False # MCP-11: tools/list hash pinned
    swarm_c2_controls: bool = False         # MCP-12: topology monitoring deployed
    failure_taxonomy: bool = False          # MCP-13: CP.1 tags in audit events
    last_assessed: str = ""
    raw: dict = field(default_factory=dict)


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
