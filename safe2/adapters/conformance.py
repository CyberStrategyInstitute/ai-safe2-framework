"""Strict conformance checks for attributed third-party evidence adapters."""

from __future__ import annotations

import hashlib
import json
import math
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2 import __version__
from safe2.contracts import validate_artifact

MAX_DOCUMENT_BYTES = 20_000_000
EVIDENCE_TYPES = {"harness", "scanner", "evaluator", "ledger", "usage", "cloud"}


class AdapterError(ValueError):
    """Raised for unreadable or structurally ambiguous adapter inputs."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError("duplicate JSON object key")
        result[key] = value
    return result


def load_json_regular(path: Path, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> dict[str, Any]:
    """Load one bounded, non-symlink JSON object with duplicate/non-finite rejection."""
    try:
        info = path.lstat()
    except OSError as exc:
        raise AdapterError(f"input is not readable: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AdapterError("adapter input must be a regular, non-symlink file")
    if info.st_size > max_bytes:
        raise AdapterError(f"adapter input exceeds {max_bytes} bytes")
    try:
        value = json.loads(
            path.read_bytes(),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                AdapterError(f"non-finite JSON number: {token}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("adapter input must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise AdapterError("adapter input root must be an object")
    return value


def _canonical_digest(value: dict[str, Any], excluded: str) -> str:
    body = {key: item for key, item in value.items() if key != excluded}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _semantic_violations(
    descriptor: dict[str, Any], evidence: dict[str, Any]
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []

    def fail(rule: str, path: str, message: str) -> None:
        failures.append({"rule": rule, "path": path, "message": message})

    if evidence.get("adapter_id") != descriptor.get("adapter_id"):
        fail("ADAPTER-ID", "$.adapter_id", "evidence adapter_id does not match descriptor")
    if evidence.get("adapter_version") != descriptor.get("version"):
        fail("ADAPTER-VERSION", "$.adapter_version", "evidence version does not match descriptor")
    if evidence.get("evidence_type") not in descriptor.get("evidence_types", []):
        fail("EVIDENCE-TYPE", "$.evidence_type", "evidence type is not declared by the adapter")
    if evidence.get("provider") != descriptor.get("provider"):
        fail("PROVIDER-ATTRIBUTION", "$.provider", "provider attribution differs from descriptor")
    if evidence.get("decision_scope") != "evidence_only":
        fail(
            "DECISION-SCOPE",
            "$.decision_scope",
            "external adapter output must remain evidence_only",
        )
    if evidence.get("conformance_claim") is not False:
        fail(
            "CONFORMANCE-CLAIM",
            "$.conformance_claim",
            "adapter evidence cannot claim AI SAFE2 conformance",
        )

    coverage = evidence.get("coverage", {})
    status = evidence.get("status")
    gaps = coverage.get("gaps", []) if isinstance(coverage, dict) else []
    if status == "complete" and gaps:
        fail(
            "COVERAGE-COMPLETE", "$.coverage.gaps", "complete evidence cannot retain coverage gaps"
        )
    if status == "partial" and not gaps:
        fail(
            "COVERAGE-PARTIAL", "$.coverage.gaps", "partial evidence must identify at least one gap"
        )
    if status == "unavailable" and evidence.get("payload") is not None:
        fail("UNAVAILABLE-PAYLOAD", "$.payload", "unavailable evidence must not contain a payload")
    if status != "unavailable" and evidence.get("payload") is None:
        fail("EVIDENCE-PAYLOAD", "$.payload", "completed or partial evidence requires a payload")

    claim_ids: set[str] = set()
    for index, claim in enumerate(evidence.get("claims", [])):
        claim_id = claim.get("id")
        if claim_id in claim_ids:
            fail("CLAIM-ID", f"$.claims[{index}].id", "claim identifiers must be unique")
        claim_ids.add(claim_id)
        if claim.get("basis") == "observed" and not claim.get("source_ref"):
            fail(
                "CLAIM-SOURCE",
                f"$.claims[{index}].source_ref",
                "observed claims require a source_ref",
            )
        value = claim.get("value")
        if isinstance(value, float) and not math.isfinite(value):
            fail("CLAIM-FINITE", f"$.claims[{index}].value", "claim numbers must be finite")
    return failures


def evaluate_conformance(
    descriptor: dict[str, Any], specimens: list[tuple[str, dict[str, Any]]]
) -> dict[str, Any]:
    """Evaluate structural and semantic adapter conformance without executing a provider."""
    descriptor_errors = validate_artifact("adapter-descriptor-v1", descriptor)
    cases = []
    for name, evidence in specimens:
        structural = validate_artifact("adapter-evidence-v1", evidence)
        semantic = (
            [] if structural or descriptor_errors else _semantic_violations(descriptor, evidence)
        )
        cases.append(
            {
                "name": name,
                "status": "passed" if not structural and not semantic else "failed",
                "structural_errors": structural,
                "semantic_errors": semantic,
            }
        )
    passed = (
        not descriptor_errors and bool(cases) and all(row["status"] == "passed" for row in cases)
    )
    report: dict[str, Any] = {
        "schema_version": "safe2.adapter-conformance.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "adapter_id": descriptor.get("adapter_id") if not descriptor_errors else None,
        "adapter_version": descriptor.get("version") if not descriptor_errors else None,
        "runner": {"name": "safe2", "version": __version__},
        "status": "passed" if passed else "failed",
        "descriptor_errors": descriptor_errors,
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "passed": sum(row["status"] == "passed" for row in cases),
            "failed": sum(row["status"] == "failed" for row in cases),
        },
        "limitations": [
            "Conformance validates artifact contracts and attribution semantics; it does not execute, trust, endorse, or certify the provider.",
            "A passing adapter can still supply inaccurate evidence; source authenticity and independent verification remain separate concerns.",
        ],
    }
    report["integrity_sha256"] = _canonical_digest(report, "integrity_sha256")
    violations = validate_artifact("adapter-conformance-v1", report)
    if violations:
        raise AdapterError("generated conformance report failed its packaged contract")
    return report
