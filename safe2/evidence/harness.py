"""Loss-aware intake for provider-neutral harness evidence exports."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

DOMAINS = (
    "task_lifecycle", "tool_calls", "artifacts", "tests", "usage",
    "environment_state", "completion_claim",
)


def ingest(payload: bytes) -> dict[str, Any]:
    """Validate and summarize an attributed export without trusting its claims."""
    if not payload or len(payload) > 1_000_000:
        raise ValueError("Harness source must be a nonempty file of at most 1 MB")
    source = parse_json(payload)
    if validate_artifact("harness-source-v1", source):
        raise ValueError("Harness source violates its evidence contract")

    event_ids: set[str] = set()
    for event in (*source["events"], *source["usage"]):
        event_id = event["event_id"]
        if event_id in event_ids:
            raise ValueError("Event identifiers must be unique across evidence and usage")
        event_ids.add(event_id)
        if event["source_ref"] is None and event.get("status") != "missing" and event.get("basis") != "unknown":
            raise ValueError("Observed, declared, reported, or estimated events require a source reference")
        if event.get("status") == "missing" and event["source_ref"] is not None:
            raise ValueError("Missing events cannot cite evidence that was not collected")
        if event.get("basis") == "unknown" and (event["value"] is not None or event["source_ref"] is not None):
            raise ValueError("Unknown usage must preserve a null value and source reference")

    coverage = source["coverage"]
    for domain in DOMAINS:
        item = coverage[domain]
        if item["status"] == "missing":
            if item["basis"] != "unknown" or item["source_ref"] is not None:
                raise ValueError("Missing coverage must remain unknown and unreferenced")
        elif item["basis"] == "unknown" or item["source_ref"] is None:
            raise ValueError("Complete or partial coverage requires an attributed basis")

    claim = source["completion_claim"]
    if claim["status"] == "not_claimed" and claim["source_ref"] is not None:
        raise ValueError("An absent completion claim cannot have a source reference")
    if claim["status"] != "not_claimed" and claim["source_ref"] is None:
        raise ValueError("A completion claim requires a source reference")

    statuses = [coverage[domain]["status"] for domain in DOMAINS]
    event_statuses = [event["status"] for event in source["events"]]
    recommendations = []
    for domain in DOMAINS:
        status = coverage[domain]["status"]
        if status != "complete":
            recommendations.append(
                f"Collect an attributed {domain.replace('_', ' ')} source; current coverage is {status}."
            )
    if source["producer"]["kind"] == "operator_declaration":
        recommendations.append("Add a supported native, hook, or wrapper export independent of operator declaration.")

    result = {
        "schema_version": "safe2.harness-evidence.v1",
        "collected_at": datetime.now(UTC).isoformat(),
        "provider": {"name": "SAFE2 harness evidence intake", "mode": "offline-import"},
        "source": {
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
            "producer_id": source["producer"]["producer_id"],
            "export_id": source["producer"]["export_id"], "kind": source["producer"]["kind"],
            "authentication": "not_checked",
        },
        "harness": source["harness"], "task": source["task"], "coverage": coverage,
        "summary": {
            "coverage_complete": statuses.count("complete"),
            "coverage_partial": statuses.count("partial"),
            "coverage_missing": statuses.count("missing"),
            "observed_events": event_statuses.count("observed"),
            "declared_events": event_statuses.count("declared"),
            "missing_events": event_statuses.count("missing"),
            "total_events": len(event_statuses),
        },
        "completion_claim": claim, "usage": source["usage"],
        "recommendations": recommendations,
        "decision_scope": "evidence_inventory_only", "completion_verified": False,
        "billing_verified": False, "conformance_claim": False,
        "limitations": [
            "Intake validates structure and source binding; it does not authenticate the producer or execution.",
            "Observed and complete are source-attributed labels, not independent proof of coverage or truth.",
            "No prompt, tool arguments, output content, secret values, or filesystem contents are retained here.",
            "A completion claim is preserved but never promoted to verified completion by intake alone.",
            "Usage values remain provider-reported, estimated, or unknown and are not billing reconciliation.",
        ],
    }
    if validate_artifact("harness-evidence-v1", result):
        raise ValueError("Harness intake produced an invalid evidence artifact")
    return result
