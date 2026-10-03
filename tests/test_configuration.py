from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli
from safe2.configuration import ConfigurationError, read_configuration, resolve_configuration


def test_init_creates_secure_defaults_and_never_overwrites(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "--project-name", "demo"])
    assert result.exit_code == 0, result.output
    target = tmp_path / ".safe2" / "config.toml"
    first = target.read_bytes()
    config = read_configuration(target)
    assert config["project"] == {"profile": "local", "name": "demo"}
    assert set(config["privacy"].values()) == {False}
    assert config["output"]["overwrite"] is False

    again = runner.invoke(cli, ["init", str(tmp_path)])
    assert again.exit_code != 0
    assert "already exists" in again.output
    assert target.read_bytes() == first


def test_config_show_reports_precedence_without_hidden_value_overrides(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(cli, ["init", str(tmp_path), "--profile", "ci"]).exit_code == 0
    result = runner.invoke(cli, ["config", "show", "--start", str(tmp_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["source"] == "project"
    assert payload["configuration"]["project"]["profile"] == "ci"


def test_resolution_precedence_is_explicit_environment_project_defaults(tmp_path: Path) -> None:
    runner = CliRunner()
    project = tmp_path / "project"
    explicit = tmp_path / "explicit"
    project.mkdir()
    explicit.mkdir()
    assert runner.invoke(cli, ["init", str(project), "--profile", "local"]).exit_code == 0
    assert runner.invoke(cli, ["init", str(explicit), "--profile", "enterprise"]).exit_code == 0
    explicit_file = explicit / ".safe2" / "config.toml"

    config, source = resolve_configuration(
        explicit=explicit_file,
        start=project,
        environ={"SAFE2_CONFIG": str(project / ".safe2" / "config.toml")},
    )
    assert source == "explicit"
    assert config["project"]["profile"] == "enterprise"

    config, source = resolve_configuration(
        start=project, environ={"SAFE2_CONFIG": str(explicit_file)}
    )
    assert source == "environment"
    assert config["project"]["profile"] == "enterprise"

    config, source = resolve_configuration(start=project, environ={})
    assert source == "project"
    assert config["project"]["profile"] == "local"

    empty = tmp_path / "empty"
    empty.mkdir()
    config, source = resolve_configuration(start=empty, environ={})
    assert source == "defaults"
    assert config["project"]["profile"] == "local"


def test_unknown_keys_and_unsafe_output_paths_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "config.toml"
    source.write_text('schema_version = "safe2.config.v1"\nunknown = true\n', encoding="utf-8")
    result = CliRunner().invoke(cli, ["config", "validate", str(source)])
    assert result.exit_code != 0
    assert "unknown top-level keys" in result.output

    source.write_text(
        'schema_version = "safe2.config.v1"\n[output]\ndirectory = "../escape"\n',
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["config", "validate", str(source)])
    assert result.exit_code != 0
    assert "must not escape" in result.output

    source.write_text(
        'schema_version = "safe2.config.v1"\n[limits]\nmax_files = 1000001\n',
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["config", "validate", str(source)])
    assert result.exit_code != 0
    assert "must not exceed" in result.output


def test_symlink_configuration_is_rejected_when_supported(tmp_path: Path) -> None:
    target = tmp_path / "real.toml"
    target.write_text('schema_version = "safe2.config.v1"\n', encoding="utf-8")
    link = tmp_path / "link.toml"
    try:
        link.symlink_to(target)
    except OSError:
        return
    try:
        read_configuration(link)
    except ConfigurationError as exc:
        assert "symbolic-link" in str(exc)
    else:
        raise AssertionError("symlinked configuration was accepted")


def test_symlink_project_root_is_rejected_when_supported(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "linked-project"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        return
    result = CliRunner().invoke(cli, ["init", str(link)])
    assert result.exit_code != 0
    assert "symbolic-link project" in result.output
    assert not (real / ".safe2").exists()
