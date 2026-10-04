from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli
from safe2.configuration import initialize_project
from safe2.contracts import validate_artifact
from safe2.evidence.manifest import verify_manifest


def test_default_assessment_is_honestly_incomplete_without_content_consent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    initialize_project(tmp_path, profile="local", project_name="demo")
    output = tmp_path / "evidence"
    result = CliRunner().invoke(
        cli, ["assess", str(tmp_path), "--output-dir", str(output), "--no-wsl"]
    )
    assert result.exit_code == 0, result.output
    assessment = json.loads((output / "assessment.json").read_text(encoding="utf-8"))
    scan = json.loads((output / "project-scan.json").read_text(encoding="utf-8"))
    assert assessment["summary"]["disposition"] == "INCOMPLETE"
    assert assessment["summary"]["static_violations"] is None
    assert scan["status"] == "not_requested"
    assert scan["content_read_locally"] is False
    assert not validate_artifact("project-assessment-v1", assessment)


def test_consented_assessment_writes_valid_sealed_bundle(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    initialize_project(tmp_path, profile="ci", project_name="demo")
    output = tmp_path / "evidence"
    result = CliRunner().invoke(
        cli,
        [
            "assess",
            str(tmp_path),
            "--output-dir",
            str(output),
            "--scan-content",
            "--inspect-config",
            "--no-wsl",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    scan = json.loads((output / "project-scan.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert scan["status"] == "completed"
    assert scan["content_read_locally"] is True
    assert not validate_artifact("project-scan-evidence-v1", scan)
    assert manifest["summary"] == {"artifacts": 2, "valid": 2, "invalid": 0}
    assert verify_manifest(manifest) == "valid"
    assert (
        (output / "decision-card.md")
        .read_text(encoding="utf-8")
        .startswith("# AI SAFE² Project Assessment Card")
    )
    assert not (output / ".incomplete").exists()
    assert {row["path"] for row in manifest["artifacts"]} == {
        "environment.json",
        "project-scan.json",
    }


def test_assessment_refuses_overwrite_and_preserves_first_bundle(tmp_path: Path) -> None:
    initialize_project(tmp_path, profile="local", project_name=None)
    output = tmp_path / "evidence"
    runner = CliRunner()
    first = runner.invoke(cli, ["assess", str(tmp_path), "--output-dir", str(output), "--no-wsl"])
    assert first.exit_code == 0, first.output
    original = (output / "assessment.json").read_bytes()
    second = runner.invoke(cli, ["assess", str(tmp_path), "--output-dir", str(output), "--no-wsl"])
    assert second.exit_code != 0
    assert "already exists" in second.output
    assert (output / "assessment.json").read_bytes() == original


def test_config_inspection_requires_explicit_content_consent(tmp_path: Path) -> None:
    initialize_project(tmp_path, profile="local", project_name=None)
    result = CliRunner().invoke(
        cli,
        ["assess", str(tmp_path), "--output-dir", str(tmp_path / "out"), "--inspect-config"],
    )
    assert result.exit_code != 0
    assert "requires explicit --scan-content consent" in result.output
    assert not (tmp_path / "out").exists()
