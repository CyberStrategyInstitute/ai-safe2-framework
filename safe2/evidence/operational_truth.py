"""Loss-aware task evidence synthesis across harness boundaries."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

DOMAINS = ("task_lifecycle", "tool_calls", "artifacts", "tests", "usage", "environment_state", "completion_claim")
SUPPORTED = {"safe2.harness-evidence.v1", "safe2.task-receipt.v1"}


def build(policy_payload: bytes, artifacts: list[bytes]) -> dict[str, Any]:
    policy = parse_json(policy_payload)
    if validate_artifact("operational-truth-source-v1", policy):
        raise ValueError("Operational truth policy violates its contract")
    if not 1 <= len(artifacts) <= 100:
        raise ValueError("Provide 1..100 evidence artifacts")

    rows: list[dict[str, Any]] = []
    seen_digests: set[str] = set()
    harnesses: set[str] = set()
    coverage: dict[str, list[str]] = {domain: [] for domain in DOMAINS}
    event_counts = {"total": 0, "observed": 0, "declared": 0, "missing": 0}
    usage_events: dict[str, tuple[Any, Any, Any, Any]] = {}
    duplicate_usage = 0
    claims: list[str] = []
    receipt_states: list[str] = []
    conflicts: list[str] = []

    for raw in artifacts:
        if not raw or len(raw) > 5_000_000:
            raise ValueError("Evidence artifacts must be nonempty and at most 5 MB")
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen_digests:
            raise ValueError("Duplicate evidence artifact bytes are ambiguous")
        seen_digests.add(digest)
        artifact = parse_json(raw)
        version = artifact.get("schema_version")
        if version not in SUPPORTED:
            raise ValueError("Unsupported operational evidence contract")
        contract = "harness-evidence-v1" if version == "safe2.harness-evidence.v1" else "task-receipt-v1"
        if validate_artifact(contract, artifact):
            raise ValueError("Operational evidence violates its contract")
        rows.append({"schema_version": version, "sha256": digest, "bytes": len(raw)})

        if version == "safe2.harness-evidence.v1":
            task = artifact["task"]
            if task["task_id"] != policy["task_id"]: conflicts.append("task_id_mismatch")
            if task["revision"] != policy["revision"]: conflicts.append("revision_mismatch")
            harnesses.add(artifact["harness"]["name"])
            for domain in DOMAINS: coverage[domain].append(artifact["coverage"][domain]["status"])
            summary = artifact["summary"]
            for key in event_counts: event_counts[key] += summary.get(f"{key}_events", 0) if key != "total" else summary["total_events"]
            claims.append(artifact["completion_claim"]["status"])
            for item in artifact["usage"]:
                fingerprint = (item.get("metric"), item.get("value"), item.get("basis"), item.get("source_ref"))
                if item["event_id"] in usage_events and usage_events[item["event_id"]] != fingerprint:
                    duplicate_usage += 1
                usage_events.setdefault(item["event_id"], fingerprint)
        else:
            if artifact["task_id"] != policy["task_id"]: conflicts.append("receipt_task_id_mismatch")
            harnesses.add(artifact["harness"])
            counts = artifact["counts"]
            if counts["contradicted"]: receipt_states.append("contradicted")
            elif counts["unverifiable"]: receipt_states.append("unverifiable")
            else: receipt_states.append("supported")
            for item in artifact["usage"]:
                fingerprint = (item.get("metric"), item.get("value"), item.get("basis"), item.get("source_ref"))
                if item["event_id"] in usage_events and usage_events[item["event_id"]] != fingerprint:
                    duplicate_usage += 1
                usage_events.setdefault(item["event_id"], fingerprint)

    aggregate = {}
    gaps = []
    rank = {"missing": 0, "partial": 1, "complete": 2}
    for domain in DOMAINS:
        statuses = coverage[domain]
        aggregate[domain] = min(statuses, key=rank.get) if statuses else "missing"
        if domain in policy["required_domains"] and aggregate[domain] != "complete":
            gaps.append(f"required_domain_{domain}_{aggregate[domain]}")
    if duplicate_usage:
        conflicts.append("duplicate_usage_ownership")
    complete_claimed = "claimed_complete" in claims
    if not complete_claimed:
        completion = "not_claimed"
    elif "contradicted" in receipt_states:
        completion = "contradicted"
    elif receipt_states and all(state == "supported" for state in receipt_states):
        completion = "supported_by_supplied_evidence"
    else:
        completion = "insufficient_evidence"
        gaps.append("completion_claim_lacks_supported_receipt")
    conflicts = sorted(set(conflicts))
    gaps = sorted(set(gaps))
    gate = "hold" if conflicts or completion == "contradicted" else ("review" if gaps or completion in {"not_claimed", "insufficient_evidence"} else "ready_for_human_decision")
    result = {
        "schema_version": "safe2.operational-truth-manifest.v1", "created_at": datetime.now(UTC).isoformat(),
        "task": {"task_id": policy["task_id"], "revision": policy["revision"], "harnesses": sorted(harnesses)},
        "inputs": rows, "coverage": aggregate, "events": event_counts,
        "usage": {"events": len(usage_events), "duplicate_ownership": duplicate_usage, "billing_verified": False},
        "completion": {"claims": sorted(set(claims)), "assessment": completion},
        "gaps": gaps, "conflicts": conflicts, "gate": gate, "decision_owner": policy["decision_owner"],
        "assumptions": policy["assumptions"], "exclusions": policy["exclusions"],
        "completion_verified": False, "billing_verified": False, "conformance_claim": False,
        "limitations": [
            "Synthesis checks supplied evidence consistency; it does not observe execution or authenticate provider truth.",
            "Complete coverage is provider-attributed and does not prove that omitted events do not exist.",
            "Supported completion means supplied receipt criteria agree; task acceptance remains human-owned.",
            "Usage is deduplicated by event identifier only and is not billing reconciliation.",
            "Event summary counts are provider totals and may overlap because normalized harness evidence does not expose raw event identifiers.",
        ],
    }
    if validate_artifact("operational-truth-manifest-v1", result):
        raise ValueError("Operational truth synthesis produced an invalid artifact")
    return result
