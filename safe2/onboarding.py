"""Consent-first orchestration for a first useful AI SAFE2 assessment."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.assessment import AssessmentError, run_assessment
from safe2.configuration import (
    CONFIG_RELATIVE_PATH,
    MAX_CONFIG_BYTES,
    PROFILES,
    ConfigurationError,
    initialize_project,
    validate_configuration,
)
from safe2.contracts import validate_artifact
from safe2.secure_io import read_regular_bounded, reject_symlink_ancestry


class OnboardingError(ValueError):
    """Raised when guided onboarding cannot preserve its declared boundaries."""


def _digest(value: dict[str, Any], excluded: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != excluded}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _validate_root(root: Path) -> Path:
    target = root.absolute()
    try:
        reject_symlink_ancestry(target)
        info = target.lstat()
    except (OSError, ValueError) as exc:
        raise OnboardingError("target must be an inspectable regular directory") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise OnboardingError("target must be a regular directory, not a symbolic link")
    return target


def create_onboarding_plan(
    root: Path,
    *,
    profile: str,
    output_dir: Path | None,
    scan_content: bool,
    inspect_config: bool,
    include_wsl: bool,
) -> dict[str, Any]:
    """Build a deterministic, read-only execution preview."""
    target = _validate_root(root)
    if profile not in PROFILES:
        raise OnboardingError(f"unsupported profile: {profile}")
    config_path = target / CONFIG_RELATIVE_PATH
    if config_path.exists() or config_path.is_symlink():
        try:
            config_bytes = read_regular_bounded(config_path, limit=MAX_CONFIG_BYTES)
            configuration = validate_configuration(tomllib.loads(config_bytes.decode("utf-8")))
        except (ConfigurationError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise OnboardingError(str(exc)) from exc
        except ValueError as exc:
            raise OnboardingError("configuration is not a bounded regular file") from exc
        config_action = "reuse"
        effective_profile = configuration["project"]["profile"]
        config_sha256: str | None = hashlib.sha256(config_bytes).hexdigest()
        effective_content_read = scan_content or configuration["privacy"]["collect_content"]
        content_consent_source = "command" if scan_content else (
            "configuration" if effective_content_read else "none"
        )
    else:
        config_action = "create"
        effective_profile = profile
        config_sha256 = None
        effective_content_read = scan_content
        content_consent_source = "command" if scan_content else "none"
    if inspect_config and not effective_content_read:
        raise OnboardingError(
            "--inspect-config requires explicit --scan-content consent or collect_content=true"
        )
    selected_output = output_dir or (target / ".safe2" / "onboarding")
    if not selected_output.is_absolute():
        selected_output = target / selected_output
    selected_output = selected_output.absolute()
    plan: dict[str, Any] = {
        "schema_version": "safe2.onboarding-plan.v1",
        "plan_id": "",
        "target": str(target),
        "configuration": {
            "path": str(config_path),
            "action": config_action,
            "profile": effective_profile,
            "sha256": config_sha256,
        },
        "consent": {
            "read_project_content": effective_content_read,
            "read_project_content_source": content_consent_source,
            "inspect_redacted_configuration_structure": inspect_config,
            "inventory_wsl_names": include_wsl,
            "network_access": False,
        },
        "output_dir": str(selected_output),
        "steps": [
            "Create or reuse a secure local AI SAFE2 configuration.",
            "Inventory recognized local harness and security metadata.",
            "Run only the inspections explicitly consented above.",
            "Write a schema-valid evidence bundle and human next-step card.",
        ],
        "stops_before": [
            "remote or cloud access",
            "remediation or source modification",
            "deployment, publication, or release",
            "certification or framework-conformance claims",
        ],
        "authority": "Execution requires explicit operator confirmation; all decisions remain human-owned.",
    }
    plan["plan_id"] = "safe2-start-" + _digest(plan, "plan_id")[:16]
    violations = validate_artifact("onboarding-plan-v1", plan)
    if violations:
        raise OnboardingError("onboarding plan failed its packaged contract")
    return plan


def _render_next_step_card(result: dict[str, Any]) -> str:
    summary = result["assessment_summary"]
    return "\n".join(
        [
            "# AI SAFE² Guided Start Card",
            "",
            f"**Status:** {result['status']}",
            f"**Assessment disposition:** {summary['disposition']}",
            f"**Evidence confidence:** {summary['evidence_confidence']}",
            f"**Harnesses detected:** {summary['harnesses_detected']}",
            "",
            "## What to do next",
            "",
            "1. Open `assessment/decision-card.md` for the human-readable findings.",
            "2. Review `assessment/assessment.json` for canonical coverage and limitations.",
            "3. Add runtime, cloud, task-receipt, AISM, or Challenge evidence only when applicable.",
            "4. Have an accountable human decide whether to investigate, remediate, or proceed.",
            "",
            "## Boundary",
            "",
            "This guided run made no remote connection, changed no project source, authorized no deployment, and made no conformance claim.",
            "",
        ]
    )


def execute_onboarding(plan: dict[str, Any], *, project_name: str | None) -> dict[str, Any]:
    """Execute an approved plan and exclusively publish its evidence bundle."""
    if validate_artifact("onboarding-plan-v1", plan):
        raise OnboardingError("onboarding plan is not contract-valid")
    root = _validate_root(Path(plan["target"]))
    output = Path(plan["output_dir"])
    if output.exists() or output.is_symlink():
        raise OnboardingError(f"output directory already exists: {output}")
    try:
        reject_symlink_ancestry(output.parent)
        output.parent.mkdir(parents=True, exist_ok=True)
        reject_symlink_ancestry(output.parent)
    except (OSError, ValueError) as exc:
        raise OnboardingError("output ancestry is not safe or writable") from exc

    config = plan["configuration"]
    config_created = False
    if config["action"] == "create":
        try:
            initialize_project(root, profile=config["profile"], project_name=project_name)
            config_created = True
        except ConfigurationError as exc:
            raise OnboardingError(str(exc)) from exc

    staging = Path(tempfile.mkdtemp(prefix=".safe2-start-", dir=output.parent))
    try:
        try:
            config_bytes = read_regular_bounded(root / CONFIG_RELATIVE_PATH, limit=MAX_CONFIG_BYTES)
        except ValueError as exc:
            raise OnboardingError("approved configuration is no longer a bounded regular file") from exc
        if config["sha256"] is not None and hashlib.sha256(config_bytes).hexdigest() != config["sha256"]:
            raise OnboardingError("configuration changed after preview; create and approve a new plan")
        approved_config = staging / "configuration-snapshot.toml"
        with approved_config.open("xb") as handle:
            handle.write(config_bytes)
        assessment = run_assessment(
            root,
            output_dir=staging / "assessment",
            config_path=approved_config,
            scan_content=plan["consent"]["read_project_content"],
            inspect_config=plan["consent"]["inspect_redacted_configuration_structure"],
            include_wsl=plan["consent"]["inventory_wsl_names"],
        )
        _write_json(staging / "onboarding-plan.json", plan)
        result: dict[str, Any] = {
            "schema_version": "safe2.onboarding-result.v1",
            "plan_id": plan["plan_id"],
            "completed_at": datetime.now(UTC).isoformat(),
            "status": "completed",
            "configuration": {
                "path": config["path"],
                "outcome": "created" if config_created else "reused",
            },
            "assessment_summary": assessment["assessment"]["summary"],
            "artifacts": {
                "plan": "onboarding-plan.json",
                "assessment": "assessment/assessment.json",
                "assessment_card": "assessment/decision-card.md",
                "next_step_card": "next-step-card.md",
                "configuration_snapshot": "configuration-snapshot.toml",
            },
            "authorization": {
                "remediate": False,
                "deploy": False,
                "publish": False,
                "claim_conformance": False,
            },
            "limitations": [
                "Only local evidence within the approved inspection scope was collected.",
                "A completed run does not mean the assessed system is safe, compliant, or ready to deploy.",
            ],
            "integrity_sha256": "",
        }
        result["integrity_sha256"] = _digest(result, "integrity_sha256")
        if validate_artifact("onboarding-result-v1", result):
            raise OnboardingError("onboarding result failed its packaged contract")
        _write_json(staging / "onboarding-result.json", result)
        (staging / "next-step-card.md").write_text(
            _render_next_step_card(result), encoding="utf-8", newline="\n"
        )
        try:
            os.replace(staging, output)
        except FileExistsError as exc:
            raise OnboardingError(f"output directory already exists: {output}") from exc
        return {"plan": plan, "result": result, "output_dir": str(output)}
    except (AssessmentError, OSError, ValueError) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        if isinstance(exc, OnboardingError):
            raise
        raise OnboardingError(str(exc)) from exc
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
