from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.evidence.attribution import build
from safe2.evidence.system_identity import ingest

DATA = Path(__file__).parents[1] / "safe2" / "data"


def raw(value):
    return (json.dumps(value) + "\n").encode()


def identity():
    return ingest((DATA / "system-identity-source-demo.json").read_bytes())


def scope():
    ident = identity()
    return {"schema_version": "safe2.assessment-scope-manifest.v1", "created_at": "2026-09-15T00:00:00Z", "source": {"scope_id": "s", "declared_at": "2026-09-15T00:00:00Z", "sha256": "a" * 64, "bytes": 1, "system_identity_sha256": "b" * 64, "authentication": "not_checked"}, "subject": {"subject_id": ident["subject"]["subject_id"], "system_fingerprint_sha256": ident["system_fingerprint_sha256"]}, "deployment_subject": {"name": "App", "type": "application", "component_ids": ["harness-1"], "basis": "declared", "source_ref": "x"}, "root": {"display_name": "repo", "path_disclosed": False}, "entries": [], "conflicts": [], "summary": {"files": 0, "unsafe_links": 0, "conflicts": 0, "truncated": False, "included": 0, "excluded": 0, "partial": 0, "not_applicable": 0, "unclassified": 0, "classifications": {}}, "recommendations": [], "decision_scope": "assessment_scope_inventory_only", "scope_verified": False, "content_inspected": False, "conformance_claim": False, "limitations": ["a", "b", "c", "d"]}


def finding(key, evidence="1" * 64, severity="high"):
    return {"finding_key": key, "provider": "scanner", "rule_id": "R1", "component_ids": ["app"], "severity": severity, "title": key, "evidence_sha256": evidence, "control_ids": ["GOV.1"]}


def source(scope_bytes, complete=True):
    ident = identity()
    revision = lambda name, findings: {"revision_id": name, "scope_manifest_sha256": hashlib.sha256(scope_bytes).hexdigest(), "coverage_complete": complete, "findings": findings}
    return {"schema_version": "safe2.change-attribution-source.v1", "comparison_id": "cmp", "declared_at": "2026-09-15T00:00:00Z", "subject": {"subject_id": ident["subject"]["subject_id"], "system_fingerprint_sha256": ident["system_fingerprint_sha256"]}, "baseline": {**revision("base", [finding("same"), finding("changed"), finding("gone")]), "trusted": True, "trust_basis": "protected branch"}, "current": revision("head", [finding("same"), finding("changed", severity="medium"), finding("new")])}


def test_classifies_complete_comparison():
    scope_bytes = raw(scope())
    result = build(raw(source(scope_bytes)), raw(identity()), scope_bytes, scope_bytes)
    assert result["summary"] == {"inherited": 1, "introduced": 1, "changed": 1, "resolved": 1, "unknown": 0, "total": 4}


def test_incomplete_coverage_makes_all_correspondence_unknown():
    scope_bytes = raw(scope())
    result = build(raw(source(scope_bytes, complete=False)), raw(identity()), scope_bytes, scope_bytes)
    assert result["summary"]["unknown"] == 4


def test_set_like_order_does_not_create_false_change():
    scope_bytes = raw(scope())
    value = source(scope_bytes)
    value["baseline"]["findings"][0]["component_ids"] = ["tool-1", "harness-1"]
    value["current"]["findings"][0]["component_ids"] = ["harness-1", "tool-1"]
    value["baseline"]["findings"][0]["control_ids"] = ["GOV.2", "GOV.1"]
    value["current"]["findings"][0]["control_ids"] = ["GOV.1", "GOV.2"]
    result = build(raw(value), raw(identity()), scope_bytes, scope_bytes)
    assert next(row for row in result["changes"] if row["finding_key"] == "same")["status"] == "inherited"


def test_rejects_duplicate_keys_and_digest_mismatch():
    scope_bytes = raw(scope())
    value = source(scope_bytes)
    value["current"]["findings"].append(finding("new"))
    with pytest.raises(ValueError, match="Duplicate"):
        build(raw(value), raw(identity()), scope_bytes, scope_bytes)
    value = source(scope_bytes)
    value["current"]["scope_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        build(raw(value), raw(identity()), scope_bytes, scope_bytes)


def test_cli_writes_then_strict_fails_on_unknown(tmp_path):
    scope_bytes = raw(scope())
    paths = {}
    for name, payload in (("source", raw(source(scope_bytes, complete=False))), ("identity", raw(identity())), ("base", scope_bytes), ("head", scope_bytes)):
        paths[name] = tmp_path / f"{name}.json"; paths[name].write_bytes(payload)
    output = tmp_path / "out.json"
    result = CliRunner().invoke(cli, ["evidence", "attribute", str(paths["source"]), "--system-identity", str(paths["identity"]), "--baseline-scope", str(paths["base"]), "--current-scope", str(paths["head"]), "-o", str(output), "--strict"])
    assert result.exit_code == 1 and output.exists()
