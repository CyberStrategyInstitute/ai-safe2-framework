"""Create a provenance-preserving manifest across heterogeneous evidence."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2 import __version__
from safe2.contracts import validate_artifact
from safe2.discovery.integrity import verify_inventory
from safe2.evidence.friction import verify_event

SCHEMA_CONTRACTS = {
    "safe2.discovery.v1": "discovery-v1",
    "safe2.discovery-drift.v1": "discovery-drift-v1",
    "safe2.environment-posture.v1": "environment-posture-v1",
    "safe2.environment-policy-decision.v1": "environment-policy-decision-v1",
    "safe2.friction.v1": "friction-event-v1",
    "safe2.friction-summary.v1": "friction-summary-v1",
    "safe2.run-manifest.v1": "run-manifest-v1",
    "safe2.nexus-evidence.v1": "nexus-evidence-v1",
    "safe2.skillspector-evidence.v1": "skillspector-evidence-v1",
}


def _canonical_digest(value: dict[str, Any], excluded: str) -> str:
    body = {key: item for key, item in value.items() if key != excluded}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_manifest(manifest: dict[str, Any]) -> str:
    digest = manifest.get("integrity_sha256")
    if digest is None:
        return "not_present"
    if not isinstance(digest, str) or len(digest) != 64:
        return "invalid"
    return (
        "valid"
        if digest == _canonical_digest(manifest, "integrity_sha256")
        else "invalid"
    )


def _artifact_record(path: Path, *, max_bytes: int) -> dict[str, Any]:
    record: dict[str, Any] = {"path": str(path), "status": "invalid"}
    if path.is_symlink():
        return {**record, "error": "symbolic_link_rejected"}
    try:
        size = path.stat().st_size
        record["bytes"] = size
        if size > max_bytes:
            return {**record, "error": "input_size_limit_exceeded"}
        raw = path.read_bytes()
    except OSError as exc:
        return {**record, "error": type(exc).__name__}
    record["sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        artifact = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {**record, "error": type(exc).__name__}
    if not isinstance(artifact, dict):
        return {**record, "error": "top_level_not_object"}

    declared_version = artifact.get("schema_version")
    contract = SCHEMA_CONTRACTS.get(str(declared_version))
    if declared_version == "1.0" and "subject" in artifact and "cells" in artifact:
        contract = "aism-assessment-v1"
    schema_version = (
        declared_version
        if isinstance(declared_version, str)
        and re.fullmatch(r"[A-Za-z0-9._-]{1,100}", declared_version)
        else None
    )
    record.update({"schema_version": schema_version, "contract": contract})
    if contract is None:
        return {**record, "error": "unknown_schema_version", "structural_validation": "not_available"}
    violations = validate_artifact(contract, artifact)
    record["structural_validation"] = "valid" if not violations else "invalid"
    record["validation_error_count"] = len(violations)
    if declared_version == "safe2.discovery.v1":
        record["integrity_verification"] = verify_inventory(artifact)
    elif declared_version == "safe2.friction.v1":
        record["integrity_verification"] = verify_event(artifact)
    elif declared_version == "safe2.run-manifest.v1":
        record["integrity_verification"] = verify_manifest(artifact)
    else:
        record["integrity_verification"] = "not_applicable"
    record["status"] = (
        "valid"
        if not violations and record["integrity_verification"] != "invalid"
        else "invalid"
    )
    return record


def create_manifest(
    paths: tuple[Path, ...], *, subject_id: str, max_bytes: int = 20_000_000
) -> dict[str, Any]:
    if not subject_id.strip():
        raise ValueError("subject_id must not be empty")
    artifacts = [_artifact_record(path, max_bytes=max_bytes) for path in paths]
    valid = sum(row["status"] == "valid" for row in artifacts)
    manifest: dict[str, Any] = {
        "schema_version": "safe2.run-manifest.v1",
        "run_id": f"safe2-run-{uuid.uuid4()}",
        "created_at": datetime.now(UTC).isoformat(),
        "subject_id": subject_id,
        "collector": {"name": "safe2", "version": __version__},
        "artifacts": artifacts,
        "summary": {"artifacts": len(artifacts), "valid": valid, "invalid": len(artifacts) - valid},
        "decision_scope": "evidence_inventory_only",
        "limitations": [
            "Manifest inclusion does not establish factual accuracy, authorization, control effectiveness, or conformance.",
            "SHA-256 binds artifact bytes but does not authenticate their author or approver.",
        ],
    }
    manifest["integrity_sha256"] = _canonical_digest(manifest, "integrity_sha256")
    return manifest
