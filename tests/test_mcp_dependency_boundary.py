"""Keep the deployed v1 server out of an unqualified MCP SDK major upgrade."""
from pathlib import Path
import tomllib

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_knowledge_server_retains_qualified_mcp_v1_range():
    project = tomllib.loads((ROOT / "skills/mcp/pyproject.toml").read_text())
    requirements = [Requirement(value) for value in project["project"]["dependencies"]]
    mcp = [requirement for requirement in requirements if requirement.name == "mcp"]
    assert len(mcp) == 1
    assert mcp[0].specifier == SpecifierSet(">=1.12,<2"), (
        "MCP SDK v2 requires the migration matrix and transport/auth regression evidence; "
        "do not widen the v1 server's dependency range alone."
    )


def test_dependabot_does_not_expand_the_mcp_major_boundary():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    updates = [entry for entry in config["updates"]
               if entry["package-ecosystem"] == "pip" and entry["directory"] == "/skills/mcp"]
    assert len(updates) == 1
    assert any(
        rule["dependency-name"] == "mcp"
        and rule.get("update-types") == ["version-update:semver-major"]
        for rule in updates[0].get("ignore", [])
    ), "Keep MCP minor/patch updates enabled, but require a deliberate major migration."
