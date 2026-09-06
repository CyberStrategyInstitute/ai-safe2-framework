"""Evidence-bounded environment policy evaluation for agents and CI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from safe2.contracts import validate_artifact

SEVERITIES = ("critical", "high", "medium", "low", "info")


def load_policy(path: Path, *, max_bytes: int = 1_000_000) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("policy must not be a symbolic link")
    try:
        if path.stat().st_size > max_bytes:
            raise ValueError("policy exceeds the maximum supported size")
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"policy could not be parsed: {type(exc).__name__}") from exc
    violations = validate_artifact("environment-policy-v1", policy)
    if violations:
        first = violations[0]
        raise ValueError(
            f"policy contract violation at {first['instance_path']} "
            f"({first['validator']})"
        )
    return policy


def evaluate_policy(discovery: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Separate missing decision evidence (HOLD) from observed rule breaches (DENY)."""
    posture = discovery["posture"]
    coverage = posture["coverage"]
    drift = discovery.get("drift")
    prerequisites: list[dict[str, str]] = []
    violations: list[dict[str, str]] = []

    if posture["disposition"] == "INCOMPLETE":
        prerequisites.append(
            {"rule": "posture_complete", "reason": "Environment posture is incomplete."}
        )
    high_coverage_gaps = [
        row
        for row in posture.get("findings", [])
        if row.get("category") in {"coverage_gap", "coverage_drift"}
        and row.get("severity") in {"critical", "high"}
    ]
    if high_coverage_gaps and posture["disposition"] != "INCOMPLETE":
        prerequisites.append(
            {
                "rule": "decision_coverage_complete",
                "reason": (
                    f"{len(high_coverage_gaps)} high-severity coverage findings prevent "
                    "an evidence-sufficient decision."
                ),
            }
        )
    allowed = policy.get("allowed_dispositions", ["BASELINE", "REVIEW"])
    if posture["disposition"] not in allowed and posture["disposition"] != "INCOMPLETE":
        violations.append(
            {
                "rule": "allowed_dispositions",
                "reason": f"Observed disposition {posture['disposition']} is not allowed.",
            }
        )
    if policy.get("require_baseline") and drift is None:
        prerequisites.append(
            {"rule": "require_baseline", "reason": "No baseline comparison was supplied."}
        )
    if policy.get("require_baseline_integrity") and (
        drift is None or drift.get("baseline_integrity") != "valid"
    ):
        prerequisites.append(
            {
                "rule": "require_baseline_integrity",
                "reason": "A baseline with valid integrity evidence was not supplied.",
            }
        )
    if drift is not None and drift.get("baseline_integrity") != "valid" and not any(
        row["rule"] == "require_baseline_integrity" for row in prerequisites
    ):
        prerequisites.append(
            {
                "rule": "baseline_integrity_valid",
                "reason": "Unsigned baseline evidence cannot support an automated ALLOW decision.",
            }
        )
    if policy.get("require_config_inspection") and not coverage.get(
        "configuration_inspection_requested"
    ):
        prerequisites.append(
            {
                "rule": "require_config_inspection",
                "reason": "Opt-in structural configuration inspection was not requested.",
            }
        )
    if policy.get("require_all_targets_completed") and coverage.get(
        "explicit_targets_incomplete", 0
    ):
        prerequisites.append(
            {
                "rule": "require_all_targets_completed",
                "reason": "One or more explicitly requested targets were not completed.",
            }
        )
    max_drift = policy.get("max_drift_changes")
    if max_drift is not None:
        if drift is None:
            prerequisites.append(
                {
                    "rule": "max_drift_changes",
                    "reason": "Drift threshold cannot be evaluated without a baseline.",
                }
            )
        elif drift["changes"] > max_drift:
            violations.append(
                {
                    "rule": "max_drift_changes",
                    "reason": f"Observed {drift['changes']} changes; maximum is {max_drift}.",
                }
            )
    for severity, maximum in policy.get("max_findings", {}).items():
        observed = posture["finding_counts"].get(severity, 0)
        if observed > maximum:
            violations.append(
                {
                    "rule": f"max_findings.{severity}",
                    "reason": f"Observed {observed} {severity} findings; maximum is {maximum}.",
                }
            )

    disposition = "DENY" if violations else "HOLD" if prerequisites else "ALLOW"
    return {
        "schema_version": "safe2.environment-policy-decision.v1",
        "policy_id": policy["id"],
        "disposition": disposition,
        "exit_code": {"ALLOW": 0, "DENY": 1, "HOLD": 2}[disposition],
        "violations": violations,
        "unmet_prerequisites": prerequisites,
        "facts": {
            "posture_disposition": posture["disposition"],
            "finding_counts": posture["finding_counts"],
            "drift_changes": drift.get("changes") if drift else None,
            "baseline_integrity": drift.get("baseline_integrity") if drift else None,
        },
        "interpretation": (
            "ALLOW means supplied evidence met this policy; it is not a conformance, "
            "certification, or universal safety claim."
        ),
    }
