"""Policy-driven development plans and evidence-bounded completion receipts.

This module turns development-process guidance into deterministic, replayable
artifacts. It never executes target code, approves a change, or grants merge,
release, deployment, exception, or policy-change authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from safe2.challenge.io import read_bytes, safe_path
from safe2.contracts import validate_artifact

INTEGRITY_CANONICALIZATION = "json-sort-keys-compact-utf8-v1"
REVIEW_CADENCE = ("completion", "subsystem", "task", "task-and-specialist")
RISK_TIERS = ("low", "medium", "high", "critical")
RED_GREEN_MODES = {"tdd", "characterization-first", "contract-first"}
GREEN_ONLY_MODES = {"schema-validation", "render-validation"}
SUPPORTED_ARTIFACTS = {
    "safe2.development-plan.v1": "development-plan-v1",
    "safe2.development-receipt.v1": "development-receipt-v1",
}


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    unsigned = {key: item for key, item in value.items() if key != "integrity"}
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def artifact_digest(value: dict[str, Any]) -> str:
    """Hash all top-level content except the self-referential integrity block."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": INTEGRITY_CANONICALIZATION,
        "digest": artifact_digest(value),
        "verification_scope": "all top-level content except integrity",
        "authenticity": "unsigned",
    }
    return value


def _integrity_status(value: dict[str, Any]) -> str:
    integrity = value.get("integrity")
    if not isinstance(integrity, dict):
        return "not_present"
    if (
        integrity.get("algorithm") != "sha256"
        or integrity.get("canonicalization") != INTEGRITY_CANONICALIZATION
        or integrity.get("authenticity") != "unsigned"
    ):
        return "invalid"
    digest = integrity.get("digest")
    if not isinstance(digest, str) or len(digest) != 64:
        return "invalid"
    return "valid" if digest == artifact_digest(value) else "invalid"


def _require_valid(contract: str, value: dict[str, Any]) -> None:
    violations = validate_artifact(contract, value)
    if violations:
        raise ValueError(f"{contract} failed structural validation")


def _max_cadence(*values: str) -> str:
    try:
        return max(values, key=REVIEW_CADENCE.index)
    except ValueError as exc:
        raise ValueError("policy contains an unsupported review cadence") from exc


def _gap(code: str, severity: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "detail": detail}


def _literal_prefix(pattern: str) -> str:
    normalized = pattern.replace("\\", "/")
    positions = [normalized.find(token) for token in ("*", "?", "[")]
    boundaries = [position for position in positions if position >= 0]
    return normalized[: min(boundaries)] if boundaries else normalized


def _patterns_overlap(declared: str, policy_pattern: str) -> bool:
    declared = declared.replace("\\", "/")
    policy_pattern = policy_pattern.replace("\\", "/")
    if fnmatchcase(declared, policy_pattern) or fnmatchcase(policy_pattern, declared):
        return True
    declared_prefix = _literal_prefix(declared).rstrip("/")
    policy_prefix = _literal_prefix(policy_pattern).rstrip("/")
    return bool(
        declared_prefix
        and policy_prefix
        and (
            declared_prefix.startswith(policy_prefix + "/")
            or policy_prefix.startswith(declared_prefix + "/")
        )
    )


def _require_repository_patterns(paths: list[str]) -> None:
    for path in paths:
        normalized = path.replace("\\", "/")
        if (
            normalized.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized)
            or ".." in normalized.split("/")
        ):
            raise ValueError("scope and policy paths must be repository-relative")


def _classify_risk(
    source: dict[str, Any], risk_policy: dict[str, Any] | None
) -> dict[str, Any]:
    declared = source["risk_tier"]
    if risk_policy is None:
        return {
            "declared_tier": declared,
            "policy_floor": None,
            "effective_tier": declared,
            "matched_rules": [],
            "risk_raised": False,
        }
    _require_valid("review-policy-v1", risk_policy)
    _require_repository_patterns(source["scope"]["include"])
    for rule in risk_policy["rules"]:
        _require_repository_patterns(rule["patterns"])
    matched_rules = []
    included = source["scope"]["include"]
    for rule in risk_policy["rules"]:
        matched_paths = sorted(
            path
            for path in included
            if any(_patterns_overlap(path, pattern) for pattern in rule["patterns"])
        )
        if matched_paths:
            matched_rules.append(
                {
                    "id": rule["id"],
                    "tier": rule["tier"],
                    "reason": rule["reason"],
                    "matched_paths": matched_paths,
                    "required_evidence": list(rule["required_evidence"]),
                    "review_lenses": list(rule["review_lenses"]),
                }
            )
    floor_candidates = [risk_policy["default_tier"]]
    floor_candidates.extend(item["tier"] for item in matched_rules)
    policy_floor = max(floor_candidates, key=RISK_TIERS.index)
    effective = max((declared, policy_floor), key=RISK_TIERS.index)
    return {
        "declared_tier": declared,
        "policy_floor": policy_floor,
        "effective_tier": effective,
        "matched_rules": matched_rules,
        "risk_raised": RISK_TIERS.index(effective) > RISK_TIERS.index(declared),
    }


def create_plan(
    source: dict[str, Any],
    policy: dict[str, Any],
    risk_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a deterministic, risk-adjusted implementation plan."""
    _require_valid("development-plan-source-v1", source)
    _require_valid("development-policy-v1", policy)
    _require_repository_patterns(source["scope"]["include"])
    _require_repository_patterns(source["scope"]["exclude"])

    shape_name = source["delivery_shape"]
    risk_classification = _classify_risk(source, risk_policy)
    tier_name = risk_classification["effective_tier"]
    change_kind = source["change_kind"]
    shape = policy["delivery_shapes"][shape_name]
    tier = policy["risk_tiers"][tier_name]
    allowed_test_modes = policy["test_modes_by_change_kind"][change_kind]

    approval_required = bool(shape["human_design_approval"] or tier["human_design_approval"])
    threat_model_required = bool(tier["threat_model_required"])
    before_after_required = bool(
        shape_name == "architectural" or tier_name in {"high", "critical"}
    )
    independent_review_required = bool(
        shape_name == "architectural" or tier_name in {"high", "critical"}
    )
    specialist_review_required = tier_name == "critical"
    rollback_required = bool(shape_name == "architectural" or tier_name in {"high", "critical"})
    isolation_required = change_kind != "research"
    required_evidence = sorted(
        set(shape["required_evidence"])
        | set(tier["required_evidence"])
        | set(policy["evidence_by_change_kind"][change_kind])
        | {
            evidence_id
            for rule in risk_classification["matched_rules"]
            for evidence_id in rule["required_evidence"]
        }
    )
    if independent_review_required and "human-review" not in required_evidence:
        required_evidence.append("human-review")
        required_evidence.sort()
    if specialist_review_required and "security-review" not in required_evidence:
        required_evidence.append("security-review")
        required_evidence.sort()
    review_lenses = sorted(
        {
            lens
            for rule in risk_classification["matched_rules"]
            for lens in rule["review_lenses"]
        }
    )

    requirements = {
        "design_artifact": shape["design_artifact"],
        "human_design_approval": approval_required,
        "threat_model": threat_model_required,
        "reusable_output_allowed": shape["reusable_output_allowed"],
        "isolation_required": isolation_required,
        "allowed_test_modes": list(allowed_test_modes),
        "review_cadence": _max_cadence(
            shape["review_cadence"], tier["review_cadence"]
        ),
        "before_after": before_after_required,
        "independent_review": independent_review_required,
        "specialist_review": specialist_review_required,
        "rollback": rollback_required,
        "greptile_recommended": tier_name in policy["greptile_recommended_for"],
        "verification_before_completion": True,
        "required_evidence": required_evidence,
        "review_lenses": review_lenses,
    }

    gaps: list[dict[str, str]] = []
    if approval_required and not source["design"]["approved"]:
        gaps.append(
            _gap(
                "design_approval_missing",
                "review",
                "This delivery shape or risk tier requires explicit human design approval.",
            )
        )
    if approval_required and not source["design"].get("approval_reference"):
        gaps.append(
            _gap(
                "design_approval_reference_missing",
                "review",
                "Required human approval needs a durable reference.",
            )
        )
    if shape_name == "architectural" and not source["design"].get("artifact"):
        gaps.append(
            _gap(
                "design_artifact_missing",
                "review",
                "Architectural work requires a written specification and implementation plan.",
            )
        )
    if threat_model_required and not source.get("threat_model_reference"):
        gaps.append(
            _gap(
                "threat_model_missing",
                "review",
                "Critical-risk work requires a threat-model reference.",
            )
        )
    if isolation_required and source["isolation"]["strategy"] == "none":
        gaps.append(
            _gap(
                "isolation_missing",
                "contradiction",
                "Repository-changing work must use an isolated branch or worktree.",
            )
        )
    if isolation_required and not source["isolation"].get("reference"):
        gaps.append(
            _gap(
                "isolation_reference_missing",
                "review",
                "The isolated branch or worktree needs a durable reference.",
            )
        )
    if source["testing"]["mode"] not in allowed_test_modes:
        gaps.append(
            _gap(
                "test_mode_not_allowed",
                "contradiction",
                "The selected test mode is incompatible with this change kind.",
            )
        )
    if shape_name == "spike" and source["work_product"] == "reusable":
        gaps.append(
            _gap(
                "spike_reusable_conflict",
                "contradiction",
                "A disposable spike cannot be represented as reusable implementation output.",
            )
        )
    if source["testing"]["mode"] == "approved-spike" and shape_name != "spike":
        gaps.append(
            _gap(
                "spike_mode_without_spike",
                "contradiction",
                "The approved-spike evidence mode is valid only for a spike.",
            )
        )

    if any(item["severity"] == "contradiction" for item in gaps):
        disposition = "invalid"
    elif gaps:
        disposition = "review_required"
    else:
        disposition = "ready"

    plan = {
        "schema_version": "safe2.development-plan.v1",
        "plan_id": source["task_id"],
        "policy": {
            "id": policy["policy_id"],
            "sha256": artifact_digest(policy),
            "risk_policy_id": risk_policy["policy_id"] if risk_policy else None,
            "risk_policy_sha256": artifact_digest(risk_policy) if risk_policy else None,
        },
        "source_sha256": artifact_digest(source),
        "task": {
            "title": source["title"],
            "outcome": source["outcome"],
            "delivery_shape": shape_name,
            "declared_risk_tier": source["risk_tier"],
            "risk_tier": tier_name,
            "change_kind": change_kind,
            "work_product": source["work_product"],
            "acceptance_conditions": list(source["acceptance_conditions"]),
            "scope": source["scope"],
            "trust_boundaries": list(source["trust_boundaries"]),
            "assumptions": list(source["assumptions"]),
            "unknowns": list(source["unknowns"]),
        },
        "risk_classification": risk_classification,
        "requirements": requirements,
        "observations": {
            "design_summary_present": bool(source["design"]["summary"].strip()),
            "design_artifact": source["design"].get("artifact"),
            "design_approved": source["design"]["approved"],
            "approval_reference": source["design"].get("approval_reference"),
            "threat_model_reference": source.get("threat_model_reference"),
            "isolation_strategy": source["isolation"]["strategy"],
            "isolation_reference": source["isolation"].get("reference"),
            "test_mode": source["testing"]["mode"],
            "test_rationale": source["testing"].get("rationale"),
        },
        "gaps": gaps,
        "disposition": disposition,
        "authorization": {
            "merge": False,
            "release": False,
            "deploy": False,
            "exception": False,
            "policy_change": False,
        },
        "limitations": [
            "The plan is derived from operator-supplied declarations and repository policy.",
            "Ready means planning prerequisites are represented; it does not prove implementation quality.",
            "Provider reviews are attributed evidence and cannot grant authority.",
        ],
    }
    _seal(plan)
    _require_valid("development-plan-v1", plan)
    return plan


def _artifact_target(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or candidate.drive or ".." in candidate.parts:
        raise ValueError("evidence paths must be relative and remain below artifact root")
    checked_root = safe_path(root)
    checked_target = safe_path(checked_root / candidate)
    if os.path.commonpath([str(checked_root), str(checked_target)]) != str(checked_root):
        raise ValueError("evidence path escapes artifact root")
    return checked_target


def _evaluate_evidence(
    observations: list[dict[str, Any]], artifact_root: Path
) -> dict[str, dict[str, Any]]:
    evaluated: dict[str, dict[str, Any]] = {}
    for observation in observations:
        evidence_id = observation["evidence_id"]
        if evidence_id in evaluated:
            raise ValueError("duplicate evidence identifiers are not allowed")
        declared_status = observation["status"]
        result: dict[str, Any] = {
            "evidence_id": evidence_id,
            "declared_status": declared_status,
            "status": "unverifiable",
            "reason": "operator_declared_unavailable",
            "artifact_path": observation.get("artifact_path"),
            "expected_sha256": observation.get("expected_sha256"),
            "observed_sha256": None,
        }
        if declared_status == "failed":
            result.update(status="contradicted", reason="operator_declared_failure")
        elif declared_status == "passed":
            try:
                payload = read_bytes(
                    _artifact_target(artifact_root, observation["artifact_path"]),
                    limit=20_000_000,
                )
                observed = hashlib.sha256(payload).hexdigest()
                result["observed_sha256"] = observed
                if observed == observation["expected_sha256"]:
                    result.update(status="supported", reason="artifact_hash_matched")
                else:
                    result.update(status="contradicted", reason="artifact_hash_mismatch")
            except (OSError, ValueError):
                result.update(status="unverifiable", reason="artifact_unavailable_or_unsafe")
        evaluated[evidence_id] = result
    return evaluated


def _cycle_check(
    source: dict[str, Any], evidence: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    mode = source["test_cycle"]["mode"]
    red = source["test_cycle"]["red"]
    green = source["test_cycle"]["green"]

    def phase_supported(phase: dict[str, Any], expected: str) -> bool:
        if phase["status"] != expected:
            return False
        reference = phase.get("evidence_id")
        return bool(reference and evidence.get(reference, {}).get("status") == "supported")

    if mode in RED_GREEN_MODES:
        supported = phase_supported(red, "observed") and phase_supported(green, "observed")
        reason = "red_and_green_evidence_supported" if supported else "red_or_green_evidence_missing"
    elif mode in GREEN_ONLY_MODES:
        supported = phase_supported(green, "observed")
        reason = "verification_evidence_supported" if supported else "verification_evidence_missing"
    else:
        supported = red["status"] == "not_applicable" and green["status"] == "not_applicable"
        reason = "cycle_not_applicable" if supported else "cycle_state_inconsistent"
    return {"mode": mode, "status": "supported" if supported else "unverifiable", "reason": reason}


def create_receipt(
    plan: dict[str, Any], source: dict[str, Any], artifact_root: Path
) -> dict[str, Any]:
    """Evaluate declared completion evidence without executing target code."""
    _require_valid("development-plan-v1", plan)
    _require_valid("development-receipt-source-v1", source)
    if _integrity_status(plan) != "valid":
        raise ValueError("development plan integrity is invalid")
    if plan["plan_id"] != source["task_id"]:
        raise ValueError("receipt task_id does not match the development plan")
    if source["test_cycle"]["mode"] != plan["observations"]["test_mode"]:
        raise ValueError("receipt test mode does not match the development plan")

    evidence = _evaluate_evidence(source["evidence"], artifact_root)
    required_evidence = []
    for evidence_id in plan["requirements"]["required_evidence"]:
        item = evidence.get(evidence_id)
        required_evidence.append(
            item
            or {
                "evidence_id": evidence_id,
                "declared_status": "missing",
                "status": "unverifiable",
                "reason": "required_evidence_missing",
                "artifact_path": None,
                "expected_sha256": None,
                "observed_sha256": None,
            }
        )

    process_checks: list[dict[str, str]] = []
    process_checks.append(
        {
            "id": "plan-disposition",
            "status": (
                "supported"
                if plan["disposition"] == "ready"
                else "contradicted"
                if plan["disposition"] == "invalid"
                else "unverifiable"
            ),
            "reason": f"plan_{plan['disposition']}",
        }
    )
    cycle = _cycle_check(source, evidence)
    process_checks.append({"id": "test-cycle", **cycle})

    before_after = source["before_after"]
    if plan["requirements"]["before_after"]:
        refs = before_after.get("evidence_ids", [])
        comparison_supported = (
            before_after["status"] == "compared"
            and len(refs) >= 2
            and all(evidence.get(item, {}).get("status") == "supported" for item in refs)
        )
        process_checks.append(
            {
                "id": "before-after",
                "status": "supported" if comparison_supported else "unverifiable",
                "reason": (
                    "comparable_evidence_supported"
                    if comparison_supported
                    else "comparable_evidence_missing"
                ),
            }
        )
    else:
        process_checks.append(
            {"id": "before-after", "status": "supported", "reason": "not_required_by_plan"}
        )

    reviews = source["reviews"]
    human_reviewed = any(
        item["kind"] == "human"
        and item["status"] == "completed"
        and evidence.get(item.get("evidence_id", ""), {}).get("status") == "supported"
        for item in reviews
    )
    if plan["requirements"]["independent_review"]:
        process_checks.append(
            {
                "id": "independent-review",
                "status": "supported" if human_reviewed else "unverifiable",
                "reason": "human_review_recorded" if human_reviewed else "human_review_missing",
            }
        )
    else:
        process_checks.append(
            {
                "id": "independent-review",
                "status": "supported",
                "reason": "not_required_by_plan",
            }
        )

    security_reviewed = any(
        item["kind"] == "security"
        and item["status"] == "completed"
        and evidence.get(item.get("evidence_id", ""), {}).get("status") == "supported"
        for item in reviews
    )
    if plan["requirements"]["specialist_review"]:
        process_checks.append(
            {
                "id": "specialist-review",
                "status": "supported" if security_reviewed else "unverifiable",
                "reason": (
                    "security_review_evidence_supported"
                    if security_reviewed
                    else "security_review_evidence_missing"
                ),
            }
        )
    else:
        process_checks.append(
            {
                "id": "specialist-review",
                "status": "supported",
                "reason": "not_required_by_plan",
            }
        )

    rollback_present = bool(source.get("rollback", "").strip())
    if plan["requirements"]["rollback"]:
        process_checks.append(
            {
                "id": "rollback",
                "status": "supported" if rollback_present else "unverifiable",
                "reason": "rollback_recorded" if rollback_present else "rollback_missing",
            }
        )
    else:
        process_checks.append(
            {"id": "rollback", "status": "supported", "reason": "not_required_by_plan"}
        )

    severe_findings = [
        item for item in source["open_findings"] if item["severity"] in {"high", "critical"}
    ]
    any_findings = bool(source["open_findings"])
    process_checks.append(
        {
            "id": "open-findings",
            "status": (
                "contradicted" if severe_findings else "unverifiable" if any_findings else "supported"
            ),
            "reason": (
                "high_or_critical_findings_open"
                if severe_findings
                else "lower_severity_findings_open"
                if any_findings
                else "no_open_findings_declared"
            ),
        }
    )

    statuses = [item["status"] for item in required_evidence]
    statuses.extend(item["status"] for item in process_checks)
    if "contradicted" in statuses:
        claim_status = "contradicted"
    elif "unverifiable" in statuses:
        claim_status = "review_required"
    else:
        claim_status = "supported"

    receipt = {
        "schema_version": "safe2.development-receipt.v1",
        "receipt_id": source["receipt_id"],
        "task_id": source["task_id"],
        "revision": source["revision"],
        "plan_sha256": artifact_digest(plan),
        "source_sha256": artifact_digest(source),
        "claim_status": claim_status,
        "required_evidence": required_evidence,
        "additional_evidence": [
            item
            for evidence_id, item in sorted(evidence.items())
            if evidence_id not in plan["requirements"]["required_evidence"]
        ],
        "process_checks": process_checks,
        "reviews": reviews,
        "open_findings": source["open_findings"],
        "residual_risks": source["residual_risks"],
        "rollback": source.get("rollback"),
        "completion_claim": source["completion_claim"],
        "authorization": {
            "completion": False,
            "merge": False,
            "release": False,
            "deploy": False,
            "risk_acceptance": False,
        },
        "limitations": [
            "Artifact hashes prove byte equality, not correctness or execution authenticity.",
            "Review and finding states are operator-supplied declarations.",
            "Supported means the declared evidence is internally consistent with this plan.",
            "A named human decision owner retains merge, release, deployment, and risk authority.",
        ],
    }
    _seal(receipt)
    _require_valid("development-receipt-v1", receipt)
    return receipt


def verify_development_artifact(value: dict[str, Any]) -> dict[str, Any]:
    """Verify structure and integrity without treating disposition as approval."""
    schema_version = value.get("schema_version")
    contract = SUPPORTED_ARTIFACTS.get(schema_version)
    if contract is None:
        return {
            "schema_version": schema_version,
            "recognized": False,
            "valid_contract": False,
            "integrity": "not_checked",
            "valid": False,
            "authorization_granted": False,
        }
    violations = validate_artifact(contract, value)
    integrity = _integrity_status(value)
    return {
        "schema_version": schema_version,
        "recognized": True,
        "valid_contract": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "integrity": integrity,
        "valid": not violations and integrity == "valid",
        "workflow_state": value.get("disposition", value.get("claim_status")),
        "authorization_granted": False,
    }
