from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2 import __version__
from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.installation import REQUIRED_DISTRIBUTIONS, inspect_installation


def dependencies() -> dict[str, str]:
    return {name: "1.0" for name in REQUIRED_DISTRIBUTIONS}


def test_supported_complete_installation_passes() -> None:
    result = inspect_installation(
        runtime=(3, 14, 1),
        installed=dependencies(),
        distribution_version=__version__,
        console_entrypoints={"safe2"},
    )
    assert result["verdict"] == "pass"
    assert result["exit_code"] == 0
    assert result["contracts"]["loaded"] == result["contracts"]["declared"]
    assert not validate_artifact("installation-check-v1", result)


def test_unsupported_missing_dependency_fails() -> None:
    installed = dependencies()
    installed.pop("click")
    result = inspect_installation(
        runtime=(3, 10, 9),
        installed=installed,
        distribution_version=__version__,
        console_entrypoints={"safe2"},
    )
    assert result["verdict"] == "fail"
    assert result["python"]["support"] == "unsupported"
    assert result["dependencies"]["missing"] == ["click"]


def test_newer_python_or_unresolved_metadata_holds() -> None:
    result = inspect_installation(
        runtime=(3, 15, 0),
        installed=dependencies(),
        distribution_version=None,
        console_entrypoints=None,
    )
    assert result["verdict"] == "hold"
    assert result["exit_code"] == 2
    assert result["python"]["support"] == "not_yet_qualified"


def test_imported_code_and_distribution_version_mismatch_fails() -> None:
    result = inspect_installation(
        runtime=(3, 14, 0),
        installed=dependencies(),
        distribution_version="different-version",
        console_entrypoints={"safe2"},
    )
    assert result["verdict"] == "fail"
    assert result["distribution"]["version_match"] is False


def test_cli_writes_new_machine_report(tmp_path: Path) -> None:
    output = tmp_path / "self-check.json"
    result = CliRunner().invoke(cli, ["self-check", "--format", "json", "--output", str(output)])
    assert result.exit_code == 0, result.output
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert not validate_artifact("installation-check-v1", artifact)
    again = CliRunner().invoke(cli, ["self-check", "--output", str(output)])
    assert again.exit_code != 0
