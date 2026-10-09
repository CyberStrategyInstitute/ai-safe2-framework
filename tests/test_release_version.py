from __future__ import annotations

import tomllib
from pathlib import Path

from safe2 import __package_version__, __version__

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent_across_package_and_qualification() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == "1.1.0"
    assert __package_version__ == __version__ == "1.1.0"
    workflow = (ROOT / ".github/workflows/cli-release-qualification.yml").read_text(
        encoding="utf-8"
    )
    publish = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    for source in (workflow, publish):
        assert "tomllib.load" in source
        assert "steps.package.outputs.version" in source
        assert "--expected-version 1.0" not in source  # read from pyproject, never hardcoded


def test_release_documentation_links_exist() -> None:
    for relative in (
        "safe2/docs/CLI-1.0-WORKFLOW.md",
        "safe2/docs/CLI-1.0-RELEASE-QUALIFICATION.md",
        "safe2/docs/CLI-STABILITY.md",
        "safe2/docs/PYTHON-COMPATIBILITY.md",
        "safe2/docs/STRANGER-ACCEPTANCE.md",
        "safe2/docs/GUIDED-START.md",
        "MIGRATION.md",
    ):
        assert (ROOT / relative).is_file(), relative
