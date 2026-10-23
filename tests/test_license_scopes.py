"""Protect the existing component license scopes and discoverable full texts."""
from pathlib import Path
import json
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_separate_standard_license_texts_are_present():
    mit = (ROOT / "LICENSE-MIT").read_text(encoding="utf-8")
    apache = (ROOT / "LICENSE-APACHE-2.0").read_text(encoding="utf-8")
    cc = (ROOT / "LICENSE-CC-BY-SA-4.0").read_text(encoding="utf-8")
    assert mit.startswith("MIT License\n")
    assert "Copyright (c) 2025-2026 Cyber Strategy Institute" in mit
    assert "Permission is hereby granted, free of charge" in mit
    assert "APPENDIX: How to apply the Apache License to your work." in apache
    assert "Grant of Patent License" in apache
    assert "Attribution-ShareAlike 4.0 International" in cc
    assert "Sui Generis Database Rights" in cc
    assert len(apache) > 11_000 and len(cc) > 19_000


def test_nexus_preserves_apache_metadata_and_copyright_notice():
    project = tomllib.loads((ROOT / "NEXUS/pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["license"] == "Apache-2.0"
    assert {"LICENSE", "NOTICE"} <= set(project["license-files"])
    assert (ROOT / "NEXUS/LICENSE").read_text() == (ROOT / "LICENSE-APACHE-2.0").read_text()
    notice = (ROOT / "NEXUS/NOTICE").read_text()
    assert "Copyright 2026 Cyber Strategy Institute" in notice


def test_cli_and_mcp_implementation_metadata_remain_mit():
    for path in ["pyproject.toml", "skills/mcp/pyproject.toml"]:
        project = tomllib.loads((ROOT / path).read_text(encoding="utf-8"))["project"]
        assert project["license"] == {"text": "MIT"}


def test_root_scope_preserves_component_boundaries():
    scope = (ROOT / "COPYRIGHT").read_text()
    for term in ["NEXUS/", "Apache-2.0", "MIT", "CC-BY-SA-4.0", "SKILL.md", "developer-workflow/"]:
        assert term in scope
    assert "SPDX-License-Identifier: MIT" not in (ROOT / "LICENSE").read_text()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "[![NEXUS: Apache-2.0]" in readme
    assert "](NEXUS/LICENSE)" in readme
    assert "docs/LICENSING.md" in readme


def test_framework_data_license_notices_remain_unchanged():
    canonical = ROOT / "skills/mcp/data/ai-safe2-controls-v3.0.json"
    packaged = ROOT / "safe2/data/ai-safe2-controls-v3.0.json"
    assert json.loads(canonical.read_text(encoding="utf-8")) == json.loads(packaged.read_text(encoding="utf-8"))
    assert '"license": "CC-BY-SA 4.0 (framework/docs) | MIT (code)"' in canonical.read_text()


def test_framework_skill_guidance_declares_its_documentation_license():
    for name in ["skills/ai-safe2-secure-build-copilot/SKILL.md", "skills/codex/ai-safe2-secure-build-copilot/SKILL.md"]:
        source = (ROOT / name).read_text(encoding="utf-8")
        assert "license: CC-BY-SA-4.0" in source.split("---", 2)[1]
