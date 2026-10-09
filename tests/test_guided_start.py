from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli
from safe2.configuration import CONFIG_RELATIVE_PATH, initialize_project
from safe2.contracts import validate_artifact
from safe2.onboarding import OnboardingError, create_onboarding_plan, execute_onboarding


def test_start_previews_without_writing(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["start", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    assert plan["configuration"]["action"] == "create"
    assert plan["consent"]["network_access"] is False
    assert not validate_artifact("onboarding-plan-v1", plan)
    assert not (tmp_path / ".safe2").exists()


def test_start_rejects_unconfirmed_execution_without_assessing(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["start", str(tmp_path), "--execute"], input="n\n")
    assert result.exit_code != 0
    assert "execution not confirmed" in result.output
    assert not (tmp_path / ".safe2").exists()


def test_start_executes_bounded_flow_and_writes_valid_artifacts(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    output = tmp_path / "evidence"
    result = CliRunner().invoke(
        cli,
        [
            "start", str(tmp_path), "--execute", "--yes", "--scan-content",
            "--inspect-config", "--no-wsl", "--output-dir", str(output),
            "--project-name", "guided-demo",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / CONFIG_RELATIVE_PATH).exists()
    plan = json.loads((output / "onboarding-plan.json").read_text(encoding="utf-8"))
    completed = json.loads((output / "onboarding-result.json").read_text(encoding="utf-8"))
    assert not validate_artifact("onboarding-plan-v1", plan)
    assert not validate_artifact("onboarding-result-v1", completed)
    assert completed["configuration"]["outcome"] == "created"
    assert (output / "configuration-snapshot.toml").read_bytes() == (tmp_path / CONFIG_RELATIVE_PATH).read_bytes()
    assert completed["authorization"] == {
        "remediate": False, "deploy": False, "publish": False, "claim_conformance": False
    }
    assert (output / "assessment" / "assessment.json").exists()
    assert "made no remote connection" in (output / "next-step-card.md").read_text(encoding="utf-8")


def test_start_json_execution_emits_one_machine_document(tmp_path: Path) -> None:
    output = tmp_path / "machine-evidence"
    result = CliRunner().invoke(
        cli,
        ["start", str(tmp_path), "--execute", "--yes", "--format", "json", "--output-dir", str(output)],
    )
    assert result.exit_code == 0, result.output
    document = json.loads(result.output)
    assert document["schema_version"] == "safe2.onboarding-result.v1"
    assert document["status"] == "completed"


def test_start_reuses_config_and_refuses_output_overwrite(tmp_path: Path) -> None:
    config = initialize_project(tmp_path, profile="enterprise", project_name="existing")
    before = config.read_bytes()
    output = tmp_path / "guided"
    runner = CliRunner()
    first = runner.invoke(cli, ["start", str(tmp_path), "--execute", "--yes", "--output-dir", str(output)])
    assert first.exit_code == 0, first.output
    assert config.read_bytes() == before
    completed = json.loads((output / "onboarding-result.json").read_text(encoding="utf-8"))
    assert completed["configuration"]["outcome"] == "reused"
    original = (output / "onboarding-result.json").read_bytes()
    second = runner.invoke(cli, ["start", str(tmp_path), "--execute", "--yes", "--output-dir", str(output)])
    assert second.exit_code != 0
    assert "already exists" in second.output
    assert (output / "onboarding-result.json").read_bytes() == original


def test_start_requires_content_consent_for_config_inspection(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["start", str(tmp_path), "--inspect-config"])
    assert result.exit_code != 0
    assert "requires explicit --scan-content consent" in result.output
    assert not (tmp_path / ".safe2").exists()


def test_start_resolves_relative_output_from_target(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli, ["start", str(tmp_path), "--execute", "--yes", "--output-dir", "relative-evidence"]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "relative-evidence" / "onboarding-result.json").exists()


def test_start_exposes_content_enabled_by_existing_configuration(tmp_path: Path) -> None:
    initialize_project(tmp_path, profile="local", project_name="configured")
    config = tmp_path / CONFIG_RELATIVE_PATH
    config.write_text(config.read_text(encoding="utf-8").replace("collect_content = false", "collect_content = true"), encoding="utf-8")
    result = CliRunner().invoke(cli, ["start", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    assert plan["consent"]["read_project_content"] is True
    assert plan["consent"]["read_project_content_source"] == "configuration"
    assert len(plan["configuration"]["sha256"]) == 64


def test_start_refuses_configuration_changed_after_preview(tmp_path: Path) -> None:
    initialize_project(tmp_path, profile="local", project_name="configured")
    output = tmp_path / "bound-evidence"
    plan = create_onboarding_plan(
        tmp_path,
        profile="local",
        output_dir=output,
        scan_content=False,
        inspect_config=False,
        include_wsl=False,
    )
    config = tmp_path / CONFIG_RELATIVE_PATH
    config.write_text(config.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    try:
        execute_onboarding(plan, project_name=None)
    except OnboardingError as exc:
        assert "changed after preview" in str(exc)
    else:
        raise AssertionError("changed configuration was accepted")
    assert not output.exists()
