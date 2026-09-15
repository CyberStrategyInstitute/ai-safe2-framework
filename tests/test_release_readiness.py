from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.evidence.attribution import build as attribute
from safe2.evidence.readiness import build
from safe2.evidence.readiness_card import render
from safe2.evidence.scope import build as inventory
from safe2.evidence.system_identity import ingest

DATA = Path(__file__).parents[1] / "safe2" / "data"
def raw(v): return (json.dumps(v) + "\n").encode()


def evidence(tmp_path, complete=True, severity="low"):
    identity = ingest((DATA / "system-identity-source-demo.json").read_bytes()); identity_bytes = raw(identity)
    root = tmp_path / "project"; (root / "safe2").mkdir(parents=True); (root / "safe2" / "app.py").write_text("x=1")
    source = json.loads((DATA / "assessment-scope-source-demo.json").read_text())
    source["subject"]["system_fingerprint_sha256"] = identity["system_fingerprint_sha256"]
    scope = inventory(raw(source), identity_bytes, root); scope_bytes = raw(scope)
    finding = {"finding_key": "F1", "provider": "scanner", "rule_id": "R1", "component_ids": ["tool-1"], "severity": severity, "title": "Finding", "evidence_sha256": "1" * 64, "control_ids": ["GOV.1"]}
    subject = scope["subject"]; digest = hashlib.sha256(scope_bytes).hexdigest()
    attr_source = {"schema_version": "safe2.change-attribution-source.v1", "comparison_id": "cmp", "declared_at": "2026-09-15T00:00:00Z", "subject": subject, "baseline": {"revision_id": "base", "scope_manifest_sha256": digest, "coverage_complete": complete, "findings": [], "trusted": True, "trust_basis": "protected branch"}, "current": {"revision_id": "head", "scope_manifest_sha256": digest, "coverage_complete": complete, "findings": [finding]}}
    attribution = attribute(raw(attr_source), identity_bytes, scope_bytes, scope_bytes)
    return identity_bytes, scope_bytes, raw(attribution)


def source(status="passed", risk=None):
    return {"schema_version": "safe2.release-readiness-source.v1", "assessment_id": "release-1", "declared_at": "2026-09-15T00:00:00Z", "target": {"name": "SAFE2 CLI", "version": "0.6.0", "revision": "abc123"}, "decision_owner": {"owner_id": "release-owner", "role": "maintainer"}, "required_checks": ["ci"], "checks": [{"check_id": "ci", "provider": "GitHub", "status": status, "evidence_ref": "run-1"}], "residual_risks": [] if risk is None else [risk], "actions": [{"action_id": "merge", "priority": "before_release", "owner_id": "release-owner", "description": "Review evidence and decide."}], "assumptions": ["Hosted result belongs to this revision."], "rollback": {"available": True, "procedure": "Revert the release commit."}}


def test_ready_is_still_not_release_authority(tmp_path):
    identity, scope, attribution = evidence(tmp_path)
    result = build(raw(source()), identity, scope, attribution)
    assert result["gate"]["status"] == "ready_for_human_decision"
    assert result["release_authorized"] is False
    assert "Release authorized: `false`" in render(result)


def test_failed_check_and_high_change_hold(tmp_path):
    identity, scope, attribution = evidence(tmp_path, severity="high")
    result = build(raw(source("failed")), identity, scope, attribution)
    assert result["gate"]["status"] == "hold"
    assert len(result["gate"]["reasons"]) == 2


def test_incomplete_evidence_and_open_low_risk_require_review(tmp_path):
    identity, scope, attribution = evidence(tmp_path, complete=False)
    risk = {"risk_id": "RISK1", "title": "Coverage", "severity": "low", "disposition": "open", "owner_id": "release-owner", "action": "Collect evidence."}
    assert build(raw(source(risk=risk)), identity, scope, attribution)["gate"]["status"] == "review"


def test_duplicate_checks_and_subject_mismatch_rejected(tmp_path):
    identity, scope, attribution = evidence(tmp_path)
    value = source(); value["checks"].append(value["checks"][0])
    with pytest.raises(ValueError, match="Duplicate"): build(raw(value), identity, scope, attribution)
    altered = json.loads(attribution); altered["subject"]["subject_id"] = "other"
    with pytest.raises(ValueError, match="subjects"): build(raw(source()), identity, scope, raw(altered))


def test_cli_writes_both_outputs_before_strict_exit(tmp_path):
    identity, scope, attribution = evidence(tmp_path / "e")
    items = {"source": raw(source("pending")), "identity": identity, "scope": scope, "attr": attribution}
    paths = {}
    for key, payload in items.items(): paths[key] = tmp_path / f"{key}.json"; paths[key].write_bytes(payload)
    output, card = tmp_path / "result.json", tmp_path / "card.md"
    result = CliRunner().invoke(cli, ["evidence", "readiness", str(paths["source"]), "--system-identity", str(paths["identity"]), "--assessment-scope", str(paths["scope"]), "--change-attribution", str(paths["attr"]), "-o", str(output), "--card", str(card), "--strict"])
    assert result.exit_code == 1 and output.exists() and card.exists()
