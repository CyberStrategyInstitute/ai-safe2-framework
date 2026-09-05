"""Privacy-conscious user and agent friction evidence."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.contracts import validate_artifact

OUTCOMES = {"verified_done", "unverified_done", "failed", "blocked", "stuck"}
CATEGORIES = {
    "false_completion",
    "missing_evidence",
    "silent_tool_failure",
    "incorrect_from_missing_data",
    "stuck_loop",
    "sycophancy",
    "context_loss",
    "permission_friction",
    "integration_failure",
    "other",
}
EVIDENCE_REF_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]{1,30}:[^\s]{1,470}$")


def _event_digest(event: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in event.items() if key != "integrity_sha256"}
    canonical = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_event(event: dict[str, Any]) -> str:
    """Return valid, invalid, or not_present for a friction-event seal."""
    digest = event.get("integrity_sha256")
    if digest is None:
        return "not_present"
    if not isinstance(digest, str) or len(digest) != 64:
        return "invalid"
    return "valid" if hmac.compare_digest(digest, _event_digest(event)) else "invalid"


def _validate_event_contract(event: dict[str, Any], line: int) -> None:
    candidate = dict(event)
    candidate.setdefault("integrity_sha256", _event_digest(event))
    violations = validate_artifact("friction-event-v1", candidate)
    if violations:
        first = violations[0]
        raise ValueError(
            f"friction event contract violation on line {line} at "
            f"{first['instance_path']} ({first['validator']})"
        )
    references = event.get("evidence_refs", [])
    if event.get("evidence_count") != len(references):
        raise ValueError(f"friction event evidence_count mismatch on line {line}")
    expected_verification = (
        "external_reference_supplied" if references else "self_reported"
    )
    if event.get("verification") != expected_verification:
        raise ValueError(f"friction event verification mismatch on line {line}")
    if event.get("outcome") == "verified_done" and not references:
        raise ValueError(f"verified_done lacks evidence on line {line}")


def record_event(
    *,
    category: str,
    outcome: str,
    severity: str,
    summary: str,
    harness: str | None = None,
    environment: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    resolved: bool = False,
) -> dict[str, Any]:
    if category not in CATEGORIES:
        raise ValueError(f"unsupported category: {category}")
    if outcome not in OUTCOMES:
        raise ValueError(f"unsupported outcome: {outcome}")
    if outcome == "verified_done" and not evidence_refs:
        raise ValueError("verified_done requires at least one external evidence reference")
    if any(not EVIDENCE_REF_PATTERN.fullmatch(reference) for reference in evidence_refs):
        raise ValueError(
            "evidence references must be bounded scheme:value identifiers without whitespace"
        )
    if not summary.strip():
        raise ValueError("summary must not be empty")
    if len(summary) > 1000:
        raise ValueError("summary must be 1000 characters or fewer")
    event_id = f"friction-{uuid.uuid4()}"
    event = {
        "schema_version": "safe2.friction.v1",
        "id": event_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "category": category,
        "outcome": outcome,
        "severity": severity,
        "summary": summary,
        "harness": harness,
        "environment": environment,
        "evidence_refs": list(evidence_refs),
        "evidence_count": len(evidence_refs),
        "resolved": resolved,
        "verification": "external_reference_supplied" if evidence_refs else "self_reported",
        "privacy": {
            "prompt_content_collected": False,
            "tool_output_collected": False,
            "secret_values_collected": False,
        },
    }
    event["integrity_sha256"] = _event_digest(event)
    return event


def append_event(path: Path, event: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ValueError("friction log must not be a symbolic link")
    if verify_event(event) != "valid":
        raise ValueError("friction event integrity verification failed before append")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


def summarize_events(path: Path, *, max_bytes: int = 20_000_000) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("friction log must not be a symbolic link")
    if path.stat().st_size > max_bytes:
        raise ValueError("friction log exceeds the maximum supported size")
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {number}") from exc
        if not isinstance(event, dict):
            raise TypeError(f"friction event on line {number} must be a JSON object")
        integrity_status = verify_event(event)
        if integrity_status == "invalid":
            raise ValueError(f"friction event integrity verification failed on line {number}")
        _validate_event_contract(event, number)
        events.append(event)
    by_category: dict[str, int] = {}
    by_outcome: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_harness: dict[str, int] = {}
    by_environment: dict[str, int] = {}
    for event in events:
        category = str(event.get("category", "unknown"))
        outcome = str(event.get("outcome", "unknown"))
        by_category[category] = by_category.get(category, 0) + 1
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        severity = str(event.get("severity", "unknown"))
        harness = str(event.get("harness") or "unspecified")
        environment = str(event.get("environment") or "unspecified")
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_harness[harness] = by_harness.get(harness, 0) + 1
        by_environment[environment] = by_environment.get(environment, 0) + 1
    evidenced = sum(bool(event.get("evidence_refs")) for event in events)
    reference_attested = sum(event.get("outcome") == "verified_done" for event in events)
    claimed_done = sum(event.get("outcome") in {"verified_done", "unverified_done"} for event in events)
    sealed = sum(verify_event(event) == "valid" for event in events)
    unsigned = len(events) - sealed
    resolved = sum(bool(event.get("resolved")) for event in events)
    recorded_at = sorted(str(event["recorded_at"]) for event in events)
    top_categories = sorted(by_category, key=lambda key: (-by_category[key], key))[:5]
    return {
        "schema_version": "safe2.friction-summary.v1",
        "events": len(events),
        "by_category": by_category,
        "by_outcome": by_outcome,
        "by_severity": by_severity,
        "by_harness": by_harness,
        "by_environment": by_environment,
        "top_categories": [
            {"category": category, "events": by_category[category]}
            for category in top_categories
        ],
        "resolution": {
            "resolved": resolved,
            "unresolved": len(events) - resolved,
            "resolved_rate": resolved / len(events) if events else 0.0,
        },
        "time_window": {
            "first_recorded_at": recorded_at[0] if recorded_at else None,
            "last_recorded_at": recorded_at[-1] if recorded_at else None,
        },
        "evidence_attachment_rate": evidenced / len(events) if events else 0.0,
        "claimed_completion": claimed_done,
        # Compatibility fields intentionally count reference-supplied attestations;
        # they do not claim that SAFE2 resolved or cryptographically bound the refs.
        "reference_attested_completion": reference_attested,
        "completion_evidence_gap": claimed_done - reference_attested,
        "integrity": {
            "sealed_events": sealed,
            "unsigned_events": unsigned,
            "invalid_events": 0,
            "coverage": sealed / len(events) if events else 0.0,
            "authenticity": "unsigned_sha256",
        },
        "limitations": [
            "Event integrity detects modification but does not prove authorship or approval.",
            "Unsigned legacy events contribute to summary metrics and are counted explicitly.",
            "Reference-attested completion means an external reference was supplied; SAFE2 does not resolve or independently verify it.",
        ],
    }
