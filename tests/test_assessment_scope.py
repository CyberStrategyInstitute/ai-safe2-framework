from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.evidence.manifest import create_manifest
from safe2.evidence.scope import build
from safe2.evidence.system_identity import ingest

DATA = Path(__file__).parents[1] / "safe2" / "data"


def payload(value: object) -> bytes:
    return json.dumps(value).encode()


def identity() -> dict:
    return ingest((DATA / "system-identity-source-demo.json").read_bytes())


def source() -> dict:
    return {
        "schema_version": "safe2.assessment-scope-source.v1",
        "scope_id": "scope-test",
        "declared_at": "2026-09-15T00:00:00Z",
        "subject": {
            "subject_id": "demo-agent-system",
            "system_fingerprint_sha256": identity()["system_fingerprint_sha256"],
        },
        "deployment_subject": {
            "name": "test application",
            "type": "application",
            "component_ids": ["harness-1", "tool-1"],
            "basis": "declared",
            "source_ref": "owner-declaration",
        },
        "rules": [
            {
                "rule_id": "product",
                "patterns": ["src/**"],
                "classification": "product",
                "disposition": "included",
                "component_ids": ["tool-1"],
                "rationale": "Shipped application package.",
                "basis": "declared",
                "source_ref": "build-layout",
            },
            {
                "rule_id": "tests",
                "patterns": ["tests/**"],
                "classification": "test",
                "disposition": "excluded",
                "component_ids": ["harness-1"],
                "rationale": "Test-only evaluation code.",
                "basis": "declared",
                "source_ref": "test-layout",
            },
        ],
        "default": {
            "classification": "unknown",
            "disposition": "partial",
            "rationale": "No scope rule covers this path.",
        },
    }


def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(exist_ok=True)
    (root / "src" / "app.py").write_text("SECRET-CONTENT-MUST-NOT-LEAK")
    (root / "tests" / "test_app.py").write_text("assert True")
    return root


def run(value: dict, root: Path) -> dict:
    return build(payload(value), payload(identity()), root)


def test_build_classifies_paths_without_reading_content(tmp_path: Path):
    result = run(source(), project(tmp_path))
    assert result["summary"] == {
        "files": 2, "unsafe_links": 0, "conflicts": 0, "truncated": False,
        "included": 1, "excluded": 1, "partial": 0, "not_applicable": 0,
        "unclassified": 0, "classifications": {"product": 1, "test": 1},
    }
    assert [item["path"] for item in result["entries"]] == ["src/app.py", "tests/test_app.py"]
    assert "SECRET-CONTENT-MUST-NOT-LEAK" not in json.dumps(result)
    assert result["scope_verified"] is False
    assert result["content_inspected"] is False
    assert result["conformance_claim"] is False


def test_cli_release_scope_is_bound_to_release_identity(tmp_path: Path):
    identity_value = ingest((DATA / "cli-0.6-system-identity-source.json").read_bytes())
    source_value = json.loads((DATA / "cli-0.6-assessment-scope-source.json").read_text())
    assert source_value["subject"]["system_fingerprint_sha256"] == identity_value[
        "system_fingerprint_sha256"
    ]
    root = tmp_path / "wheel"
    root.mkdir()
    (root / "package.py").write_text("value = 1", encoding="utf-8")
    result = build(payload(source_value), payload(identity_value), root)
    assert result["summary"]["included"] == 1
    assert result["summary"]["partial"] == 0
    assert result["summary"]["unclassified"] == 0


def test_unmatched_path_remains_partial_and_unknown(tmp_path: Path):
    root = project(tmp_path)
    (root / "NOTICE.txt").write_text("notice")
    result = run(source(), root)
    assert result["summary"]["partial"] == 1
    assert result["summary"]["unclassified"] == 1
    assert result["recommendations"]


def test_conflicting_rules_remain_visible(tmp_path: Path):
    value = source()
    conflicting = copy.deepcopy(value["rules"][0])
    conflicting.update(rule_id="exclude-product", classification="example", disposition="excluded")
    value["rules"].append(conflicting)
    result = run(value, project(tmp_path))
    assert result["summary"]["conflicts"] == 1
    assert result["entries"][0]["disposition"] == "included"
    assert result["conflicts"][0]["rule_ids"] == ["product", "exclude-product"]


@pytest.mark.parametrize("pattern", ["../secret/**", "/absolute/**", "C:/drive/**", r"src\**"])
def test_unsafe_patterns_rejected(tmp_path: Path, pattern: str):
    value = source()
    value["rules"][0]["patterns"] = [pattern]
    with pytest.raises(ValueError):
        run(value, project(tmp_path))


def test_identity_and_component_bindings_enforced(tmp_path: Path):
    value = source()
    value["subject"]["system_fingerprint_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        run(value, project(tmp_path))
    value = source()
    value["rules"][0]["component_ids"] = ["absent"]
    with pytest.raises(ValueError):
        run(value, project(tmp_path))


def test_duplicate_rules_rejected(tmp_path: Path):
    value = source()
    value["rules"].append(copy.deepcopy(value["rules"][0]))
    with pytest.raises(ValueError):
        run(value, project(tmp_path))


def test_bounded_inventory_reports_truncation(tmp_path: Path):
    result = build(payload(source()), payload(identity()), project(tmp_path), max_entries=1)
    assert result["summary"]["truncated"] is True
    assert len(result["entries"]) == 1


@pytest.mark.skipif(os.name == "nt", reason="ordinary Windows test sessions cannot reliably create symlinks")
def test_symlink_is_inventoried_but_not_followed(tmp_path: Path):
    root = project(tmp_path)
    (root / "linked.py").symlink_to(root / "src" / "app.py")
    result = run(source(), root)
    link = next(item for item in result["entries"] if item["path"] == "linked.py")
    assert link["kind"] == "unsafe_link"
    assert link["classification"] == "unknown"


def test_cli_strict_success_and_no_overwrite(tmp_path: Path):
    root = project(tmp_path)
    source_path = tmp_path / "scope.json"
    identity_path = tmp_path / "identity.json"
    output = tmp_path / "manifest.json"
    source_path.write_bytes(payload(source()))
    identity_path.write_bytes(payload(identity()))
    arguments = [
        "evidence", "scope", str(source_path), "--project-root", str(root),
        "--system-identity", str(identity_path), "--output", str(output), "--strict",
    ]
    first = CliRunner().invoke(cli, arguments)
    assert first.exit_code == 0, first.output
    assert json.loads(output.read_text())["summary"]["included"] == 1
    second = CliRunner().invoke(cli, arguments)
    assert second.exit_code != 0


def test_cli_strict_writes_then_fails_on_gap(tmp_path: Path):
    root = project(tmp_path)
    (root / "unknown.txt").write_text("unknown")
    source_path = tmp_path / "scope.json"
    identity_path = tmp_path / "identity.json"
    output = tmp_path / "manifest.json"
    source_path.write_bytes(payload(source()))
    identity_path.write_bytes(payload(identity()))
    result = CliRunner().invoke(cli, [
        "evidence", "scope", str(source_path), "--project-root", str(root),
        "--system-identity", str(identity_path), "--output", str(output), "--strict",
    ])
    assert result.exit_code == 1
    assert output.exists()


@pytest.mark.parametrize("kind", ["source", "manifest"])
def test_evidence_manifest_recognizes_scope_contracts(tmp_path: Path, kind: str):
    artifact = source() if kind == "source" else run(source(), project(tmp_path))
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(artifact))
    result = create_manifest((path,), subject_id="demo-agent-system")
    assert result["summary"]["valid"] == 1
    assert result["artifacts"][0]["contract"] == f"assessment-scope-{kind}-v1"
