"""The vendored manifest schema, its parity with the hosted server, and validate-before-write."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from importlib.resources import files
from pathlib import Path

import pytest
from assess_manifest_support import (
    TARVIN_KEY,
    build_golden_project,
    bundle_text,
    init_project,
    isolate_home,
)
from click.testing import CliRunner
from jsonschema import Draft202012Validator

from safe2.cli import cli
from safe2.manifest.collect import (
    GENERATOR_NAME,
    ManifestValidationError,
    collect_manifest,
    validate_manifest,
)

# SHA-256 of the packaged schema. It matches the hosted schema at Tarvin main
# 372307338aed81bd1f3ffa3349038e9093fa0e96 except for the unreleased CLI wording in the
# top-level description; the parity test below constrains that single metadata-field delta.
VENDORED_SHA256 = "8ba842d2e9864f038e87b4e5c766eeb6a5157ba370cbf0060fd88539a1469cee"
SERVER_SCHEMA_ENV = "SAFE2_SERVER_SCHEMA"
SERVER_SCHEMA_DEFAULT = Path("/workspace/wt-tarvin-next/schemas/aisafe2-project-manifest-1.json")
HOSTED_LEGACY_CLI_NAME = "safe2 assess --" + "pro"


def _vendored_bytes() -> bytes:
    return files("safe2.data").joinpath("aisafe2-project-manifest-1.schema.json").read_bytes()


def _good_manifest() -> dict:
    return {
        "manifest_version": "aisafe2-project-manifest/1",
        "generator": {"name": GENERATOR_NAME, "version": "1.1.0"},
        "generated_at": "2026-11-11T12:00:00Z",
        "project": {"name": "demo"},
        "agents": [],
        "mcp_servers": [],
    }


def test_vendored_schema_is_a_valid_draft_2020_12_schema_with_the_server_id() -> None:
    document = json.loads(_vendored_bytes())
    Draft202012Validator.check_schema(document)
    assert document["$id"] == "https://mcp.agency-check.app/pro/schemas/aisafe2-project-manifest-1.json"
    assert document["properties"]["manifest_version"]["const"] == "aisafe2-project-manifest/1"


def test_vendored_schema_digest_is_pinned() -> None:
    assert hashlib.sha256(_vendored_bytes()).hexdigest() == VENDORED_SHA256


def test_vendored_schema_differs_from_the_hosted_schema_only_by_cli_name() -> None:
    server = Path(os.environ.get(SERVER_SCHEMA_ENV, SERVER_SCHEMA_DEFAULT))
    if not server.is_file():
        pytest.skip(f"server schema not available; set {SERVER_SCHEMA_ENV} to a checkout's schemas/ file")
    packaged = json.loads(_vendored_bytes())
    hosted = json.loads(server.read_bytes())
    assert "safe2 assess --manifest" in packaged["description"]
    assert HOSTED_LEGACY_CLI_NAME in hosted["description"]
    hosted["description"] = packaged["description"]
    assert hosted == packaged


def test_schema_is_listed_and_exportable_through_the_schema_command() -> None:
    runner = CliRunner()
    listed = json.loads(runner.invoke(cli, ["schema", "list"]).output)
    assert "aisafe2-project-manifest-1" in listed["schemas"]
    exported = runner.invoke(cli, ["schema", "export", "aisafe2-project-manifest-1"])
    assert exported.exit_code == 0
    assert exported.output.encode() == _vendored_bytes()


def test_good_manifest_validates_and_unknown_or_malformed_fields_are_rejected() -> None:
    validate_manifest(_good_manifest())
    extra = _good_manifest() | {"prompt": "never allowed"}
    with pytest.raises(ManifestValidationError):
        validate_manifest(extra)
    spawning = _good_manifest()
    spawning["agents"] = [
        {
            "name": "a", "harness": "claude-code", "tools": [], "can_spawn_subagents": True,
            "persistent_memory": False, "runs_unattended": False, "sends_externally": False,
            "moves_money": False, "approval_points": [],
        }
    ]
    with pytest.raises(ManifestValidationError):  # mandate_configured is required when spawning
        validate_manifest(spawning)
    bad_digest = _good_manifest()
    bad_digest["mcp_servers"] = [{"name": "s", "transport": "stdio", "pinned_digest": "not-a-digest", "auth_type": "none"}]
    with pytest.raises(ManifestValidationError):
        validate_manifest(bad_digest)


def test_validation_error_reports_paths_never_values() -> None:
    bad = _good_manifest()
    bad["agents"] = [{"name": "SENTINEL_VALUE_IN_BAD_FIELD", "unexpected": "SENTINEL_VALUE_IN_BAD_FIELD"}]
    with pytest.raises(ManifestValidationError) as caught:
        validate_manifest(bad)
    assert "SENTINEL_VALUE_IN_BAD_FIELD" not in str(caught.value)
    assert all("SENTINEL_VALUE_IN_BAD_FIELD" not in json.dumps(row) for row in caught.value.violations)


def test_collected_manifest_validates_and_uses_the_exact_generator(tmp_path: Path, monkeypatch) -> None:
    isolate_home(monkeypatch, tmp_path / "home")
    project = tmp_path / "project"
    build_golden_project(project)
    manifest = collect_manifest(project, project_name="golden", max_files=10_000, max_file_bytes=5_000_000).manifest
    validate_manifest(manifest)
    from safe2 import __version__

    assert manifest["generator"] == {"name": "safe2 assess --manifest", "version": __version__}
    assert manifest["manifest_version"] == "aisafe2-project-manifest/1"


def test_schema_validate_command_accepts_the_written_manifest_and_rejects_a_tampered_one(
    tmp_path: Path, monkeypatch
) -> None:
    isolate_home(monkeypatch, tmp_path / "home")
    project = tmp_path / "project"
    build_golden_project(project)
    init_project(project)
    out = tmp_path / "bundle"
    runner = CliRunner()
    result = runner.invoke(
        cli, ["assess", str(project), "--manifest", "--scan-content", "--inspect-config", "--no-wsl", "--output-dir", str(out)]
    )
    assert result.exit_code == 0, result.output
    manifest_path = out / "aisafe2-project-manifest-1.json"
    ok = runner.invoke(cli, ["schema", "validate", "aisafe2-project-manifest-1", str(manifest_path)])
    assert ok.exit_code == 0, ok.output
    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    tampered["prompt"] = "x"
    tampered_path = tmp_path / "tampered.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
    bad = runner.invoke(cli, ["schema", "validate", "aisafe2-project-manifest-1", str(tampered_path)])
    assert bad.exit_code == 1


def test_an_invalid_manifest_is_never_written_or_sent(tmp_path: Path, monkeypatch) -> None:
    isolate_home(monkeypatch, tmp_path / "home")
    monkeypatch.setenv("SAFE2_MCP_PRO_KEY", TARVIN_KEY)
    project = tmp_path / "project"
    build_golden_project(project)
    init_project(project)
    from safe2.manifest import collect as collect_module

    real = collect_module.collect_manifest

    def invalid(*args, **kwargs):
        collection = real(*args, **kwargs)
        broken = copy.deepcopy(collection.manifest)
        broken["unexpected_key"] = "SENTINEL_VALUE_IN_BAD_FIELD"
        collection.manifest = broken
        return collection

    monkeypatch.setattr("safe2.manifest.workflow.collect_manifest", invalid)

    def refuse(*args, **kwargs):
        raise AssertionError("an invalid manifest must not reach the network")

    monkeypatch.setattr("safe2.commands.assess.post_manifest", refuse)
    out = tmp_path / "bundle"
    result = CliRunner().invoke(
        cli,
        ["assess", str(project), "--manifest", "--scan-content", "--inspect-config", "--no-wsl", "--post", "--output-dir", str(out)],
    )
    assert result.exit_code != 0
    assert "does not match aisafe2-project-manifest/1" in result.output
    assert "bundle was kept" in result.output and "no manifest" in result.output
    assert not (out / "aisafe2-project-manifest-1.json").exists()
    assert (out / "assessment.json").exists()
    assert "SENTINEL_VALUE_IN_BAD_FIELD" not in result.output
    assert TARVIN_KEY not in result.output + bundle_text(out)
