"""Conservative technical release-readiness synthesis."""
from __future__ import annotations

import hashlib
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

LIMIT = 5_000_000


def _load(payload: bytes, contract: str, label: str) -> dict[str, Any]:
    if not payload or len(payload) > LIMIT:
        raise ValueError(f"{label} is empty or exceeds 5 MB")
    value = parse_json(payload)
    if validate_artifact(contract, value):
        raise ValueError(f"{label} violates its evidence contract")
    return value


def _unique(rows: list[dict[str, Any]], key: str) -> None:
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key}")


def build(source_payload: bytes, identity_payload: bytes, scope_payload: bytes, attribution_payload: bytes) -> dict[str, Any]:
    source = _load(source_payload, "release-readiness-source-v1", "Readiness source")
    identity = _load(identity_payload, "system-identity-manifest-v1", "System identity")
    scope = _load(scope_payload, "assessment-scope-manifest-v1", "Assessment scope")
    attribution = _load(attribution_payload, "change-attribution-manifest-v1", "Change attribution")
    _unique(source["checks"], "check_id"); _unique(source["residual_risks"], "risk_id"); _unique(source["actions"], "action_id")
    subject = {"subject_id": identity["subject"]["subject_id"], "system_fingerprint_sha256": identity["system_fingerprint_sha256"]}
    if scope["subject"] != subject or attribution["subject"] != subject:
        raise ValueError("Readiness evidence subjects do not match")
    checks = {row["check_id"]: row for row in source["checks"]}
    missing = sorted(set(source["required_checks"]) - set(checks))
    failed = sorted(key for key in source["required_checks"] if key in checks and checks[key]["status"] in {"failed", "cancelled"})
    incomplete = sorted(key for key in source["required_checks"] if key in checks and checks[key]["status"] in {"pending", "unavailable"})
    blocking_changes = [row["finding_key"] for row in attribution["changes"] if row["status"] in {"introduced", "changed"} and row["current"] and row["current"]["severity"] in {"critical", "high"}]
    open_high = [row["risk_id"] for row in source["residual_risks"] if row["disposition"] == "open" and row["severity"] in {"critical", "high"}]
    unsafe_scope = bool(scope["summary"]["unsafe_links"] or scope["summary"]["conflicts"] or scope["summary"]["truncated"])
    scope_gaps = bool(scope["summary"]["partial"] or scope["summary"]["unclassified"])
    unknown_change = bool(attribution["summary"]["unknown"])
    open_other = [row["risk_id"] for row in source["residual_risks"] if row["disposition"] == "open" and row["risk_id"] not in open_high]
    reasons: list[str] = []; gaps: list[str] = []
    if failed: reasons.append("Required checks failed or were cancelled: " + ", ".join(failed))
    if blocking_changes: reasons.append("High-impact introduced or changed findings remain: " + ", ".join(blocking_changes))
    if open_high: reasons.append("Open critical or high residual risks remain: " + ", ".join(open_high))
    if unsafe_scope: reasons.append("Assessment scope contains unsafe links, conflicts, or truncation.")
    if missing: gaps.append("Required checks are missing: " + ", ".join(missing))
    if incomplete: gaps.append("Required checks are incomplete: " + ", ".join(incomplete))
    if scope_gaps: gaps.append("Assessment scope remains partial or unclassified.")
    if unknown_change: gaps.append("Change attribution contains unknown results.")
    if open_other: gaps.append("Open residual risks require review: " + ", ".join(open_other))
    if reasons: status = "hold"
    elif gaps: status = "review"
    else: status = "ready_for_human_decision"
    check_counts = Counter(row["status"] for row in source["checks"])
    result = {
        "schema_version": "safe2.release-readiness-manifest.v1", "created_at": datetime.now(UTC).isoformat(),
        "source": {"assessment_id": source["assessment_id"], "sha256": hashlib.sha256(source_payload).hexdigest(), "authentication": "not_checked"}, "target": source["target"], "subject": subject,
        "evidence": {"system_identity_sha256": hashlib.sha256(identity_payload).hexdigest(), "assessment_scope_sha256": hashlib.sha256(scope_payload).hexdigest(), "change_attribution_sha256": hashlib.sha256(attribution_payload).hexdigest()},
        "gate": {"status": status, "reasons": reasons, "facts": [f"{len(source['required_checks']) - len(missing)} of {len(source['required_checks'])} required checks supplied.", f"{attribution['summary']['total']} findings compared across revisions."], "gaps": gaps},
        "checks": {"required": len(source["required_checks"]), "missing": missing, "failed": failed, "incomplete": incomplete, "status_counts": dict(sorted(check_counts.items()))},
        "change_summary": attribution["summary"], "scope_summary": scope["summary"], "residual_risks": source["residual_risks"], "actions": source["actions"], "assumptions": source["assumptions"], "rollback": source["rollback"], "decision_owner": source["decision_owner"],
        "recommendation": {"hold": "Do not release until blocking evidence is resolved and reassessed.", "review": "Resolve evidence gaps or obtain an explicit, documented human risk decision.", "ready_for_human_decision": "Technical evidence supports proceeding to the named human release decision."}[status],
        "decision_scope": "technical_release_readiness_support_only", "release_authorized": False, "conformance_claim": False,
        "limitations": ["The named human retains release authority.", "Supplied check status and risk disposition are not independently authenticated.", "Artifact hashes prove byte binding, not truth or execution.", "Technical readiness does not establish AI SAFE² conformance or production safety."]}
    if validate_artifact("release-readiness-manifest-v1", result): raise ValueError("Readiness builder produced an invalid manifest")
    return result
