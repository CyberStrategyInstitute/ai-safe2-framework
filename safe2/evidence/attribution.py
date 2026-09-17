"""Deterministic, evidence-bounded finding attribution across two revisions."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

MAX_BYTES = 5_000_000


def _load(payload: bytes, contract: str, label: str) -> dict[str, Any]:
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError(f"{label} must be nonempty and no larger than 5 MB")
    value = parse_json(payload)
    if validate_artifact(contract, value):
        raise ValueError(f"{label} violates its evidence contract")
    return value


def _index(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for finding in findings:
        key = finding["finding_key"]
        if key in result:
            raise ValueError(f"Duplicate finding_key: {key}")
        result[key] = {
            **finding,
            "component_ids": sorted(finding["component_ids"]),
            "control_ids": sorted(finding["control_ids"]),
        }
    return result


def build(source_payload: bytes, identity_payload: bytes, baseline_scope_payload: bytes, current_scope_payload: bytes) -> dict[str, Any]:
    source = _load(source_payload, "change-attribution-source-v1", "Change attribution source")
    identity = _load(identity_payload, "system-identity-manifest-v1", "System identity")
    baseline_scope = _load(baseline_scope_payload, "assessment-scope-manifest-v1", "Baseline scope")
    current_scope = _load(current_scope_payload, "assessment-scope-manifest-v1", "Current scope")
    subject = source["subject"]
    if identity["subject"]["subject_id"] != subject["subject_id"] or identity["system_fingerprint_sha256"] != subject["system_fingerprint_sha256"]:
        raise ValueError("Identity and comparison subjects must match")
    for item in (baseline_scope, current_scope):
        if item["subject"] != subject:
            raise ValueError("Scope and comparison subjects must match")
    for name, payload, revision in (("baseline", baseline_scope_payload, source["baseline"]), ("current", current_scope_payload, source["current"])):
        if hashlib.sha256(payload).hexdigest() != revision["scope_manifest_sha256"]:
            raise ValueError(f"{name.capitalize()} scope digest does not match")
    baseline, current = _index(source["baseline"]["findings"]), _index(source["current"]["findings"])
    complete = source["baseline"]["coverage_complete"] and source["current"]["coverage_complete"]
    changes = []
    counts = {key: 0 for key in ("inherited", "introduced", "changed", "resolved", "unknown")}
    for key in sorted(set(baseline) | set(current)):
        before, after = baseline.get(key), current.get(key)
        if not complete:
            status = "unknown"
        elif before is None:
            status = "introduced"
        elif after is None:
            status = "resolved"
        elif before == after:
            status = "inherited"
        else:
            status = "changed"
        counts[status] += 1
        rows = [row for row in (before, after) if row]
        changes.append({"finding_key": key, "status": status, "baseline": before, "current": after, "component_ids": sorted(set().union(*(row["component_ids"] for row in rows))), "control_ids": sorted(set().union(*(row["control_ids"] for row in rows)))})
    result = {
        "schema_version": "safe2.change-attribution-manifest.v1", "created_at": datetime.now(UTC).isoformat(),
        "source": {"comparison_id": source["comparison_id"], "sha256": hashlib.sha256(source_payload).hexdigest(), "authentication": "not_checked"},
        "subject": subject,
        "revisions": {name: {"revision_id": source[name]["revision_id"], "scope_manifest_sha256": source[name]["scope_manifest_sha256"], "coverage_complete": source[name]["coverage_complete"]} for name in ("baseline", "current")},
        "changes": changes, "summary": {**counts, "total": len(changes)},
        "decision_scope": "change_attribution_support_only", "change_verified": False, "conformance_claim": False,
        "limitations": ["Caller-declared finding keys determine correspondence.", "A trusted baseline declaration is not independently authenticated.", "Scope manifests describe declared metadata and do not prove deployment contents.", "Attribution does not prove causation, control effectiveness, or conformance."]}
    if validate_artifact("change-attribution-manifest-v1", result):
        raise ValueError("Change attribution builder produced an invalid manifest")
    return result
