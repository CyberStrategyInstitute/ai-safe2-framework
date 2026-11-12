"""CLI behavior of `safe2 assess --pro`: consent gate, no network by default, output location."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from assess_pro_support import (
    PRO_KEY,
    build_golden_project,
    bundle_text,
    init_project,
    isolate_home,
)
from click.testing import CliRunner

from safe2.cli import cli
from safe2.commands.assess import assess_project

CONSENT = ["--scan-content", "--inspect-config"]
CONSENT_MESSAGE = "--pro requires explicit --scan-content and --inspect-config consent"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    isolate_home(monkeypatch, tmp_path / "home")
    root = tmp_path / "project"
    build_golden_project(root)
    init_project(root)
    return root


@pytest.fixture
def no_sockets(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Any attempt to create a socket, resolve a name, or connect fails the test."""
    attempts: list[str] = []

    class Forbidden:
        def __init__(self, *args, **kwargs) -> None:
            attempts.append("socket")
            raise AssertionError("a socket was opened")

    def forbidden(*args, **kwargs):
        attempts.append("network call")
        raise AssertionError("a network call was made")

    monkeypatch.setattr(socket, "socket", Forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    return attempts


@pytest.mark.parametrize("flags", [[], ["--scan-content"], ["--inspect-config"]])
def test_pro_without_both_consent_flags_fails_closed_and_reads_nothing(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_sockets, flags: list[str]
) -> None:
    monkeypatch.setenv("SAFE2_MCP_PRO_KEY", PRO_KEY)
    calls: list[str] = []

    def record(name: str):
        def inner(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"{name} ran without consent")

        return inner

    monkeypatch.setattr("safe2.commands.assess.run_assessment", record("run_assessment"))
    monkeypatch.setattr("safe2.pro.collect.read_regular_bounded", record("read_regular_bounded"))
    monkeypatch.setattr("safe2.pro.workflow.build_and_write", record("build_and_write"))
    monkeypatch.setattr("safe2.commands.assess.build_and_write", record("build_and_write"))
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), "--pro", "--post", *flags, "--output-dir", str(out)])
    assert result.exit_code != 0
    assert CONSENT_MESSAGE in result.output
    assert calls == [] and no_sockets == []
    assert not out.exists() and not (project / ".safe2" / "evidence").exists()
    assert PRO_KEY not in result.output


def test_consent_message_matches_the_existing_consent_gate_wording(project: Path, tmp_path: Path) -> None:
    existing = CliRunner().invoke(
        cli, ["assess", str(project), "--inspect-config", "--output-dir", str(tmp_path / "x")]
    )
    assert "requires explicit --scan-content consent" in existing.output
    pro = CliRunner().invoke(cli, ["assess", str(project), "--pro", "--output-dir", str(tmp_path / "y")])
    assert "requires explicit --scan-content" in pro.output and "--inspect-config consent" in pro.output


def test_post_and_manifest_out_require_pro(project: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    for extra in (["--post"], ["--manifest-out", str(tmp_path / "m.json")]):
        result = runner.invoke(cli, ["assess", str(project), *CONSENT, *extra, "--output-dir", str(tmp_path / "o")])
        assert result.exit_code == 2
        assert "require --pro" in result.output
        assert not (tmp_path / "o").exists()


def test_pro_without_post_opens_no_sockets_even_with_a_key_in_the_environment(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_sockets
) -> None:
    monkeypatch.setenv("SAFE2_MCP_PRO_KEY", PRO_KEY)
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--output-dir", str(out)])
    assert result.exit_code == 0, result.output
    assert no_sockets == []
    assert (out / "aisafe2-project-manifest-1.json").is_file()
    assert "Nothing was sent" in result.output
    assert PRO_KEY not in result.output + bundle_text(out)


def test_post_without_a_key_prints_the_path_and_exact_call_and_exits_zero(
    project: Path, tmp_path: Path, no_sockets
) -> None:
    out = tmp_path / "bundle"
    result = CliRunner().invoke(
        cli, ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--post", "--output-dir", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert no_sockets == []
    manifest_path = out / "aisafe2-project-manifest-1.json"
    assert f"Manifest: {manifest_path}" in result.output
    assert "SAFE2_MCP_PRO_KEY is not set; nothing was sent." in result.output
    assert "UNSIGNED" in result.output
    line = next(row for row in result.output.splitlines() if row.startswith("jq -n --slurpfile"))
    assert str(manifest_path) in line
    assert 'Authorization: Bearer $SAFE2_MCP_PRO_KEY' in line  # references the variable, never a value
    assert "https://mcp.agency-check.app/pro/mcp" in line
    assert "assess_project" in line and "tools/call" in line


def test_post_without_a_key_in_json_format_reports_the_skip(project: Path, tmp_path: Path, no_sockets) -> None:
    result = CliRunner().invoke(
        cli,
        ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--post", "--format", "json", "--output-dir", str(tmp_path / "b")],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["post"]["status"] == "skipped_no_key" and payload["post"]["sent"] is False
    assert payload["manifest"]["signed"] is False and payload["manifest"]["schema_validated"] is True
    assert payload["manifest"]["agents"] == 5 and payload["manifest"]["mcp_servers"] == 3


def test_a_malformed_key_is_rejected_before_anything_is_read_and_is_never_echoed(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_sockets
) -> None:
    secret = "not-an-as2k-key-SENTINELBADKEY"
    monkeypatch.setenv("SAFE2_MCP_PRO_KEY", secret)
    out = tmp_path / "bundle"
    result = CliRunner().invoke(
        cli, ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--post", "--output-dir", str(out)]
    )
    assert result.exit_code != 0
    assert "SAFE2_MCP_PRO_KEY is set but is not an as2k_" in result.output
    assert secret not in result.output and "SENTINELBADKEY" not in result.output
    assert not out.exists() and no_sockets == []


def test_the_key_cannot_be_supplied_on_the_command_line_or_through_a_click_envvar(project: Path, tmp_path: Path) -> None:
    for option in ("--key", "--api-key", "--token", "--pro-key"):
        result = CliRunner().invoke(
            cli, ["assess", str(project), "--pro", *CONSENT, option, PRO_KEY, "--output-dir", str(tmp_path / "z")]
        )
        assert result.exit_code == 2 and "No such option" in result.output
        assert PRO_KEY not in result.output
        assert not (tmp_path / "z").exists()
    assert all(param.envvar is None for param in assess_project.params)
    help_text = CliRunner().invoke(cli, ["assess", "--help"]).output
    assert "SAFE2_MCP_PRO_KEY" in help_text  # documented as an environment variable only
    assert not any(option in help_text for option in ("--key", "--api-key", "--token"))


def test_manifest_out_writes_there_relative_to_the_caller_and_refuses_overwrite(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.chdir(caller)
    bundle = tmp_path / "bundle"
    args = ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--manifest-out", "out/manifest.json", "--output-dir", str(bundle)]
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    written = caller / "out" / "manifest.json"
    assert json.loads(written.read_text(encoding="utf-8"))["manifest_version"] == "aisafe2-project-manifest/1"
    assert not (bundle / "aisafe2-project-manifest-1.json").exists()
    assert (bundle / "pro-collection-notes.json").is_file()  # explanations stay in the bundle
    original = written.read_bytes()
    again = CliRunner().invoke(cli, [*args[:-1], str(tmp_path / "bundle2")])
    assert again.exit_code != 0 and "already exists" in again.output
    assert written.read_bytes() == original


def test_a_collection_failure_keeps_the_bundle_writes_no_manifest_and_names_the_next_step(
    project: Path, tmp_path: Path
) -> None:
    (project / ".mcp.json").write_text("{broken", encoding="utf-8")
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), "--pro", *CONSENT, "--no-wsl", "--output-dir", str(out)])
    assert result.exit_code != 0
    assert ".mcp.json: not a valid JSON object" in result.output
    assert f"bundle was kept at {out}" in result.output and "new --output-dir" in result.output
    assert (out / "assessment.json").is_file()
    assert not (out / "aisafe2-project-manifest-1.json").exists()


def test_a_truncated_inventory_stops_the_manifest_but_not_the_ordinary_assessment(tmp_path: Path, monkeypatch) -> None:
    isolate_home(monkeypatch, tmp_path / "home")
    root = tmp_path / "project"
    for index in range(12):
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / f"f{index}.py").write_text("x = 1\n", encoding="utf-8")
    init_project(root, max_files=5)
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(root), "--pro", *CONSENT, "--no-wsl", "--output-dir", str(out)])
    assert result.exit_code != 0 and "limits.max_files" in result.output
    assert not (out / "aisafe2-project-manifest-1.json").exists()


def test_ordinary_assess_output_and_options_are_unchanged_without_pro(project: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), *CONSENT, "--no-wsl", "--output-dir", str(out)])
    assert result.exit_code == 0, result.output
    assert "Pro Manifest" not in result.output
    assert not (out / "aisafe2-project-manifest-1.json").exists()
    assert not (out / "pro-collection-notes.json").exists()
