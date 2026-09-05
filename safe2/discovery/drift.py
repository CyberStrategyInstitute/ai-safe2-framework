"""Compare discovery evidence against a prior trusted baseline."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from safe2.contracts import validate_artifact
from safe2.discovery.integrity import verify_inventory


def load_baseline(path: Path, *, max_bytes: int = 20_000_000) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("baseline must not be a symbolic link")
    if path.stat().st_size > max_bytes:
        raise ValueError("baseline exceeds the maximum supported size")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"baseline could not be parsed: {type(exc).__name__}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "safe2.discovery.v1":
        raise ValueError("baseline is not a safe2.discovery.v1 inventory")
    if verify_inventory(data) == "invalid":
        raise ValueError("baseline integrity verification failed")
    validation_candidate = dict(data)
    if verify_inventory(data) == "not_present":
        from safe2.discovery.integrity import seal_inventory

        seal_inventory(validation_candidate)
    violations = validate_artifact("discovery-v1", validation_candidate)
    if violations:
        first = violations[0]
        raise ValueError(
            f"baseline contract violation at {first['instance_path']} "
            f"({first['validator']})"
        )
    return data


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")[:80]


def _finding(
    finding_id: str,
    severity: str,
    category: str,
    title: str,
    fact: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "category": category,
        "title": title,
        "facts": [fact],
        "assumptions": ["The change may be authorized; baseline comparison does not establish intent."],
        "recommendation": recommendation,
        "candidate_controls": ["P2", "CP.1"],
        "verification": "derived_from_baseline_comparison",
    }


def _asset_map(inventory: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("type")), str(row.get("path"))): row
        for row in inventory.get("asset_inventory", {}).get("assets", [])
    }


def _config_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("path")): row
        for row in inventory.get("configuration_inspection", {}).get("files", [])
        if row.get("status") == "completed" and row.get("content_sha256")
    }


def compare_discovery(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Return security-relevant changes without interpreting them as unauthorized."""
    findings: list[dict[str, Any]] = []
    scope_changed = baseline.get("scope") != current.get("scope")
    if scope_changed:
        findings.append(
            _finding(
                "DRIFT-SCOPE-CHANGED",
                "high",
                "coverage_drift",
                "Current and baseline assessment scopes differ",
                "The current inventory scope does not match the trusted baseline scope.",
                "Use a baseline captured for the same target and root, or document and approve the scope transition before interpreting other changes.",
            )
        )
    current_harnesses = {str(row.get("id")) for row in current.get("harnesses", [])}
    baseline_harnesses = {str(row.get("id")) for row in baseline.get("harnesses", [])}
    for harness in sorted(current_harnesses - baseline_harnesses):
        findings.append(
            _finding(
                f"DRIFT-HARNESS-ADDED-{_slug(harness)}",
                "medium",
                "harness_drift",
                f"Harness indicator added: {harness}",
                f"{harness} appears in the current inventory but not the baseline.",
                "Confirm installation owner, purpose, version, permissions, policy, and evidence requirements.",
            )
        )
    for harness in sorted(baseline_harnesses - current_harnesses):
        findings.append(
            _finding(
                f"DRIFT-HARNESS-REMOVED-{_slug(harness)}",
                "low",
                "harness_drift",
                f"Harness indicator removed: {harness}",
                f"{harness} appears in the baseline but not the current inventory.",
                "Confirm whether the harness was intentionally removed, moved, or became undiscoverable.",
            )
        )

    current_assets = _asset_map(current)
    baseline_assets = _asset_map(baseline)
    current_configs = _config_map(current)
    baseline_configs = _config_map(baseline)
    review_types = {
        "agent_skill",
        "mcp_configuration",
        "persistent_agent_state",
        "scheduled_agent_operation",
        "harness_configuration",
        "infrastructure_as_code",
        "ci_pipeline",
    }
    for asset_type, path in sorted(current_assets.keys() - baseline_assets.keys()):
        severity = "medium" if asset_type in review_types else "low"
        findings.append(
            _finding(
                f"DRIFT-ASSET-ADDED-{_slug(asset_type + '-' + path)}",
                severity,
                "asset_drift",
                f"Security-relevant asset added: {path}",
                f"A new {asset_type} asset appears in the current inventory.",
                "Confirm source, owner, purpose, approval, and applicable validation before relying on the asset.",
            )
        )
    for asset_type, path in sorted(baseline_assets.keys() - current_assets.keys()):
        findings.append(
            _finding(
                f"DRIFT-ASSET-REMOVED-{_slug(asset_type + '-' + path)}",
                "low",
                "asset_drift",
                f"Security-relevant asset removed: {path}",
                f"A baseline {asset_type} asset is absent from the current inventory.",
                "Confirm whether removal was intended and whether its governance function was replaced.",
            )
        )

    for asset_type, path in sorted(current_assets.keys() & baseline_assets.keys()):
        if path in current_configs and path in baseline_configs:
            continue
        current_asset = current_assets[(asset_type, path)]
        baseline_asset = baseline_assets[(asset_type, path)]
        current_hash = current_asset.get("content_sha256")
        baseline_hash = baseline_asset.get("content_sha256")
        content_changed = bool(
            current_hash and baseline_hash and current_hash != baseline_hash
        )
        metadata_changed = any(
            current_asset.get(field) != baseline_asset.get(field)
            for field in ("size_bytes", "modified_at")
        )
        if content_changed or (not (current_hash and baseline_hash) and metadata_changed):
            basis = "content hash" if content_changed else "size or modification time"
            findings.append(
                _finding(
                    f"DRIFT-ASSET-CHANGED-{_slug(asset_type + '-' + path)}",
                    "medium",
                    "asset_drift",
                    f"Security-relevant asset changed: {path}",
                    f"The asset's {basis} differs from the trusted baseline.",
                    "Review and authorize the asset change, then validate affected agent behavior before accepting a new baseline.",
                )
            )

    for path in sorted(current_configs.keys() & baseline_configs.keys()):
        if current_configs[path]["content_sha256"] != baseline_configs[path]["content_sha256"]:
            findings.append(
                _finding(
                    f"DRIFT-CONFIG-CHANGED-{_slug(path)}",
                    "medium",
                    "configuration_drift",
                    f"Inspected configuration changed: {path}",
                    "The current content hash differs from the trusted baseline hash; no raw values were compared in output.",
                    "Review the configuration diff through an authorized local workflow and reapprove the baseline if expected.",
                )
            )

    current_targets = {str(row.get("id")): row.get("status") for row in current.get("targets", [])}
    baseline_targets = {str(row.get("id")): row.get("status") for row in baseline.get("targets", [])}
    for target in sorted(baseline_targets.keys() - current_targets.keys()):
        findings.append(
            _finding(
                f"DRIFT-TARGET-NOT-ASSESSED-{_slug(target)}",
                "high",
                "coverage_drift",
                f"Baseline target was not requested in the current run: {target}",
                "A target present in the baseline has no current observation.",
                "Reassess the target or record a time-bounded scope exception; do not treat missing coverage as no change.",
            )
        )
    for target in sorted(current_targets.keys() & baseline_targets.keys()):
        if baseline_targets[target] == "completed" and current_targets[target] != "completed":
            findings.append(
                _finding(
                    f"DRIFT-TARGET-LOST-{_slug(target)}",
                    "high",
                    "coverage_drift",
                    f"Previously completed target is now incomplete: {target}",
                    f"Baseline status was completed; current status is {current_targets[target]}.",
                    "Restore read access and rerun before accepting the current environment posture.",
                )
            )

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding["category"]] = counts.get(finding["category"], 0) + 1
    return {
        "schema_version": "safe2.discovery-drift.v1",
        "baseline_collected_at": baseline.get("collected_at"),
        "baseline_integrity": verify_inventory(baseline),
        "current_collected_at": current.get("collected_at"),
        "scope_changed": scope_changed,
        "changes": len(findings),
        "counts": counts,
        "findings": findings,
        "interpretation": "Changes require review; baseline comparison does not establish authorization or risk by itself.",
    }
