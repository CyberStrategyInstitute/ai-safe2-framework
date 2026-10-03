"""One-command, evidence-bounded project assessment orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2 import __version__
from safe2.configuration import ConfigurationError, resolve_configuration
from safe2.contracts import validate_artifact
from safe2.discovery import assess_posture, discover_local, inventory_assets, seal_inventory
from safe2.discovery.config import inspect_inventory
from safe2.engines.project import run_scan
from safe2.evidence.manifest import create_manifest
from safe2.secure_io import reject_symlink_ancestry


class AssessmentError(ValueError):
    """Raised when an assessment cannot preserve its declared boundaries."""


def _canonical_digest(value: dict[str, Any], excluded: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != excluded}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _project_scan(root: Path, *, enabled: bool, max_files: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "safe2.project-scan-evidence.v1",
        "collected_at": datetime.now(UTC).isoformat(),
        "scope": {"root": str(root)},
        "collector": {"name": "safe2", "version": __version__, "engine": "static-project-scan"},
        "status": "not_requested",
        "content_read_locally": False,
        "result": None,
        "limitations": [
            "Static analysis does not prove deployed configuration, runtime behavior, control effectiveness, or framework conformance."
        ],
    }
    if enabled:
        traversed = 0
        pending = [root]
        while pending:
            current = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    traversed += 1
                    if traversed > max_files:
                        break
                    if entry.is_symlink():
                        raise AssessmentError("static scan refuses symbolic links")
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
        scan = run_scan(str(root), max_files=max_files)
        serialized = scan.model_dump(mode="json")
        for violation in serialized.get("violations", []):
            violation["evidence"] = "[redacted: inspect the source locally]"
        result.update(
            {
                "status": "incomplete" if scan.meta.get("scan_truncated") else "completed",
                "content_read_locally": True,
                "result": serialized,
            }
        )
    result["integrity_sha256"] = _canonical_digest(result, "integrity_sha256")
    violations = validate_artifact("project-scan-evidence-v1", result)
    if violations:
        raise AssessmentError("project scan evidence failed its packaged contract")
    return result


def _render_card(assessment: dict[str, Any]) -> str:
    summary = assessment["summary"]
    coverage = assessment["coverage"]
    actions = assessment["next_actions"]
    lines = [
        "# AI SAFE² Project Assessment Card",
        "",
        f"**Disposition:** {summary['disposition']}",
        f"**Subject:** `{assessment['subject']['id']}`",
        f"**Evidence confidence:** {summary['evidence_confidence']}",
        "",
        "## What was observed",
        "",
        f"- Agent harnesses detected: {summary['harnesses_detected']}",
        f"- Security-relevant assets inventoried: {summary['assets_inventoried']}",
        f"- Environment posture findings: {summary['environment_findings']}",
        f"- Static scan violations: {summary['static_violations'] if summary['static_violations'] is not None else 'NOT ASSESSED'}",
        "",
        "## Coverage",
        "",
        "| Surface | Status | Meaning |",
        "|---|---|---|",
    ]
    for row in coverage:
        lines.append(f"| {row['surface']} | {row['status']} | {row['meaning']} |")
    lines.extend(["", "## Next actions", ""])
    lines.extend(f"{index}. {action}" for index, action in enumerate(actions, 1))
    lines.extend(
        [
            "",
            "## Decision boundary",
            "",
            (
                "This card is a projection of `assessment.json`. It does not authorize deployment, "
                "establish certification, prove completion, or replace accountable human review."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def run_assessment(
    root: Path,
    *,
    output_dir: Path | None,
    config_path: Path | None,
    scan_content: bool,
    inspect_config: bool,
    include_wsl: bool,
) -> dict[str, Any]:
    """Run the bounded golden path and atomically publish a reviewable evidence bundle."""
    root = root.absolute()
    try:
        root_info = root.lstat()
    except OSError as exc:
        raise AssessmentError("assessment root is not readable") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise AssessmentError("assessment root must be a regular directory, not a symbolic link")
    try:
        config, config_source = resolve_configuration(explicit=config_path, start=root)
    except ConfigurationError as exc:
        raise AssessmentError(str(exc)) from exc
    content_enabled = scan_content or config["privacy"]["collect_content"]
    config_enabled = inspect_config
    if inspect_config and not config["privacy"]["collect_content"] and not scan_content:
        raise AssessmentError(
            "--inspect-config requires explicit --scan-content consent or collect_content=true"
        )

    selected_output = output_dir or (root / config["output"]["directory"])
    if not selected_output.is_absolute():
        selected_output = root / selected_output
    selected_output = selected_output.absolute()
    if selected_output.exists() or selected_output.is_symlink():
        raise AssessmentError(f"output directory already exists: {selected_output}")
    try:
        reject_symlink_ancestry(selected_output.parent)
    except ValueError as exc:
        raise AssessmentError("symbolic-link output ancestors are not allowed") from exc
    selected_output.parent.mkdir(parents=True, exist_ok=True)

    staging = Path(tempfile.mkdtemp(prefix=".safe2-assess-", dir=selected_output.parent))
    try:
        discovery = discover_local(root, include_wsl=include_wsl)
        discovery["targets"] = []
        discovery["summary"].update(
            {"explicit_targets": 0, "targets_completed": 0, "targets_failed": 0}
        )
        discovery["asset_inventory"] = inventory_assets(
            root,
            max_files=config["limits"]["max_files"],
            hash_contents=False,
            max_hash_bytes=config["limits"]["max_file_bytes"],
        )
        discovery["privacy"]["security_asset_contents_read_locally"] = False
        if config_enabled:
            discovery["configuration_inspection"] = inspect_inventory(
                root,
                discovery["asset_inventory"],
                max_bytes=config["limits"]["max_file_bytes"],
            )
            discovery["privacy"]["mode"] = "metadata_plus_redacted_structure"
            discovery["privacy"]["configuration_contents_read_locally"] = True
        discovery["posture"] = assess_posture(discovery)
        seal_inventory(discovery)

        scan = _project_scan(root, enabled=content_enabled, max_files=config["limits"]["max_files"])
        _write_json(staging / "environment.json", discovery)
        _write_json(staging / "project-scan.json", scan)
        manifest = create_manifest(
            (staging / "environment.json", staging / "project-scan.json"),
            subject_id=config["project"].get("name", root.name),
        )
        for record in manifest["artifacts"]:
            record["path"] = Path(record["path"]).name
        manifest["integrity_sha256"] = _canonical_digest(manifest, "integrity_sha256")
        if validate_artifact("run-manifest-v1", manifest):
            raise AssessmentError("evidence manifest failed its packaged contract")
        _write_json(staging / "manifest.json", manifest)

        posture_findings = discovery["posture"]["findings"]
        scan_result = scan["result"]
        scan_violations = None if scan_result is None else len(scan_result["violations"])
        config_incomplete = (
            discovery.get("configuration_inspection", {}).get("summary", {}).get("incomplete", 0)
        )
        incomplete = (
            scan["status"] != "completed"
            or discovery["asset_inventory"].get("truncated", False)
            or bool(config_incomplete)
        )
        has_findings = bool(posture_findings) or bool(scan_violations)
        disposition = "INCOMPLETE" if incomplete else ("REVIEW" if has_findings else "BASELINE")
        confidence = "LOW" if incomplete else ("MODERATE" if config_enabled else "LIMITED")
        next_actions = []
        if scan_result is None:
            next_actions.append(
                "Rerun with --scan-content to include consented static content analysis."
            )
        if not config_enabled:
            next_actions.append(
                "Rerun with --scan-content --inspect-config for redacted configuration structure coverage."
            )
        if posture_findings:
            next_actions.append(
                "Assign owners and review the environment posture findings in environment.json."
            )
        if scan_violations:
            next_actions.append(
                "Triage the static findings in project-scan.json before deployment."
            )
        next_actions.append(
            "Add harness runtime, task receipt, AISM, and Challenge evidence when applicable."
        )

        assessment: dict[str, Any] = {
            "schema_version": "safe2.project-assessment.v1",
            "assessment_id": f"safe2-assessment-{uuid.uuid4()}",
            "created_at": datetime.now(UTC).isoformat(),
            "subject": {"id": config["project"].get("name", root.name), "root": str(root)},
            "configuration": {
                "schema_version": config["schema_version"],
                "source": config_source,
                "profile": config["project"]["profile"],
            },
            "summary": {
                "disposition": disposition,
                "evidence_confidence": confidence,
                "harnesses_detected": discovery["summary"]["harnesses_detected"],
                "assets_inventoried": len(discovery["asset_inventory"]["assets"]),
                "environment_findings": len(posture_findings),
                "static_violations": scan_violations,
            },
            "coverage": [
                {
                    "surface": "environment_metadata",
                    "status": "incomplete"
                    if discovery["asset_inventory"].get("truncated", False)
                    else "complete",
                    "meaning": "Local metadata and recognized assets were inventoried within declared limits.",
                },
                {
                    "surface": "configuration_structure",
                    "status": "incomplete"
                    if config_incomplete
                    else "complete"
                    if config_enabled
                    else "not_requested",
                    "meaning": "Raw values are never emitted.",
                },
                {
                    "surface": "static_project_content",
                    "status": "complete" if scan["status"] == "completed" else scan["status"],
                    "meaning": "Content analysis requires explicit consent and remains incomplete when its traversal limit is reached.",
                },
                {
                    "surface": "runtime_and_cloud",
                    "status": "not_assessed",
                    "meaning": "No active harness, network, container, or cloud behavior was observed.",
                },
            ],
            "artifacts": {
                "environment": "environment.json",
                "project_scan": "project-scan.json",
                "manifest": "manifest.json",
                "card": "decision-card.md",
            },
            "next_actions": next_actions,
            "decision_scope": "human_review_support_only",
            "limitations": [
                "The workflow does not establish organizational maturity, framework conformance, certification, or deployment authorization.",
                "Unrequested and unavailable evidence remains explicit and cannot improve the disposition.",
            ],
        }
        assessment["integrity_sha256"] = _canonical_digest(assessment, "integrity_sha256")
        violations = validate_artifact("project-assessment-v1", assessment)
        if violations:
            raise AssessmentError("project assessment failed its packaged contract")
        _write_json(staging / "assessment.json", assessment)
        with (staging / "decision-card.md").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(_render_card(assessment))
        try:
            os.replace(staging, selected_output)
        except FileExistsError as exc:
            raise AssessmentError(f"output directory already exists: {selected_output}") from exc
        return {"assessment": assessment, "output_dir": str(selected_output)}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
