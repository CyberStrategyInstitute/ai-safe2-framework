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
