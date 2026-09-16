"""Normalize an attributed agent-system identity without verifying deployment state."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

CATEGORIES = ("model", "harness", "tool", "skill", "memory", "environment", "policy", "evaluator")
VERSIONED_CATEGORIES = {"model", "harness", "tool", "skill", "policy", "evaluator"}


def _attribution(basis: str, source_ref: str | None, label: str) -> None:
    if basis == "unknown" and source_ref is not None:
        raise ValueError(f"Unknown {label} cannot cite a source")
    if basis != "unknown" and source_ref is None:
        raise ValueError(f"Observed or declared {label} requires a source reference")


def _fingerprint(source: dict[str, Any]) -> str:
    """Fingerprint system identity, excluding evidence provenance and JSON/list order."""
    components = []
    for item in source["components"]:
        components.append({key: item[key] for key in (
            "component_id", "category", "name", "provider", "version",
            "artifact_sha256", "role", "authority",
        )})
        components[-1]["authority"] = sorted(components[-1]["authority"])
    bindings = [{key: item[key] for key in (
        "from_component_id", "to_component_id", "relationship",
    )} for item in source["bindings"]]
    identity = {
        "subject": source["subject"],
        "components": sorted(components, key=lambda item: item["component_id"]),
        "bindings": sorted(bindings, key=lambda item: (
            item["from_component_id"], item["to_component_id"], item["relationship"],
        )),
    }
    canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def ingest(payload: bytes) -> dict[str, Any]:
    """Validate and summarize a bounded provider-neutral identity declaration."""
    if not payload or len(payload) > 1_000_000:
        raise ValueError("System identity source must be a nonempty file of at most 1 MB")
    source = parse_json(payload)
    if validate_artifact("system-identity-source-v1", source):
        raise ValueError("System identity source violates its evidence contract")

    component_ids: set[str] = set()
    counts = {category: 0 for category in CATEGORIES}
    for component in source["components"]:
        component_id = component["component_id"]
        if component_id in component_ids:
            raise ValueError("Component identifiers must be unique")
        component_ids.add(component_id)
        counts[component["category"]] += 1
        _attribution(component["basis"], component["source_ref"], "component identity")
        if "unknown" in component["authority"] and len(component["authority"]) != 1:
            raise ValueError("Unknown authority cannot be combined with asserted authority")
    binding_ids: set[str] = set()
    relationship_edges: set[tuple[str, str, str]] = set()
    bound_ids: set[str] = set()
    for binding in source["bindings"]:
        binding_id = binding["binding_id"]
        if binding_id in binding_ids:
            raise ValueError("Binding identifiers must be unique")
        binding_ids.add(binding_id)
        start, end = binding["from_component_id"], binding["to_component_id"]
        if start not in component_ids or end not in component_ids:
            raise ValueError("Every binding endpoint must reference a declared component")
        if start == end:
            raise ValueError("A component cannot bind to itself")
        edge = (start, end, binding["relationship"])
        if edge in relationship_edges:
            raise ValueError("Duplicate component relationships are not allowed")
        relationship_edges.add(edge)
        bound_ids.update((start, end))
        _attribution(binding["basis"], binding["source_ref"], "binding")

    coverage_statuses = []
    for category in CATEGORIES:
        coverage = source["coverage"][category]
        status = coverage["status"]
        coverage_statuses.append(status)
        _attribution(coverage["basis"], coverage["source_ref"], "coverage")
        if status == "missing":
            if coverage["basis"] != "unknown" or counts[category]:
                raise ValueError("Missing coverage must be unknown and contain no category components")
        elif status == "not_applicable":
            if coverage["basis"] == "unknown" or counts[category]:
                raise ValueError("Not-applicable coverage must be attributed and contain no category components")
        elif not counts[category]:
            raise ValueError("Complete or partial coverage requires a category component")
        elif status == "complete" and any(
            item["category"] == category and item["basis"] == "unknown"
            for item in source["components"]
        ):
            raise ValueError("Complete coverage cannot contain unknown component identity")

    evidence_ids: set[str] = set()
    for reference in source["evidence_refs"]:
        if reference["evidence_id"] in evidence_ids:
            raise ValueError("Evidence identifiers must be unique")
        evidence_ids.add(reference["evidence_id"])

    components = source["components"]
    unknown = sum(item["basis"] == "unknown" for item in components)
    unversioned = sum(
        item["category"] in VERSIONED_CATEGORIES and item["version"] is None
        for item in components
    )
    unbound = len(component_ids - bound_ids)
    recommendations = []
    for category in CATEGORIES:
        status = source["coverage"][category]["status"]
        if status in {"partial", "missing"}:
            recommendations.append(f"Complete attributed {category} identity coverage; current status is {status}.")
    if unknown:
        recommendations.append(f"Resolve the evidence basis for {unknown} component(s) marked unknown.")
    if unversioned:
        recommendations.append(f"Pin or record versions for {unversioned} versionable component(s).")
    if unbound:
        recommendations.append(f"Describe relationships for {unbound} currently unbound component(s).")
    if not source["evidence_refs"]:
        recommendations.append("Attach hashed evidence references supporting the system identity.")

    summary = {
        "components": len(components), "bindings": len(source["bindings"]),
        "evidence_refs": len(source["evidence_refs"]),
        "observed_components": sum(item["basis"] == "observed" for item in components),
        "declared_components": sum(item["basis"] == "declared" for item in components),
        "unknown_components": unknown, "unversioned_components": unversioned,
        "unbound_components": unbound,
        "coverage_complete": coverage_statuses.count("complete"),
        "coverage_partial": coverage_statuses.count("partial"),
        "coverage_missing": coverage_statuses.count("missing"),
        "coverage_not_applicable": coverage_statuses.count("not_applicable"),
        "categories": counts,
    }
    result = {
        "schema_version": "safe2.system-identity-manifest.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "source": {
            "manifest_id": source["manifest_id"], "declared_at": source["declared_at"],
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
            "authentication": "not_checked",
        },
        "subject": source["subject"], "components": components,
        "bindings": source["bindings"], "coverage": source["coverage"],
        "evidence_refs": source["evidence_refs"], "summary": summary,
        "system_fingerprint_sha256": _fingerprint(source),
        "recommendations": recommendations,
        "decision_scope": "system_identity_inventory_only",
        "identity_verified": False, "configuration_verified": False,
        "conformance_claim": False,
        "limitations": [
            "The source hash binds submitted bytes but does not authenticate the author or collector.",
            "The system fingerprint identifies normalized declared composition; it does not prove deployment state.",
            "Observed labels remain source-attributed unless supported by independent evidence.",
            "Inventory inclusion does not establish authorization, control effectiveness, safety, or AI SAFE2 conformance.",
            "Names, versions, authority, relationships, and evidence references are retained assertions, not discoveries.",
        ],
    }
    if validate_artifact("system-identity-manifest-v1", result):
        raise ValueError("System identity intake produced an invalid manifest")
    return result
