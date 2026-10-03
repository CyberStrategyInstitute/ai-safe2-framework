from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.acceptance import create_bundle, verify_bundle
from safe2.cli import cli
from safe2.contracts import validate_artifact


def test_bundle_is_readable_replayable_and_claim_bounded(tmp_path: Path) -> None:
    root = tmp_path / "acceptance"
    report = create_bundle(root)
    assert report["status"] in {"passed", "held"}
    assert report["fixtures"][0]["observed_decision"] == "APPROVE"
    assert report["fixtures"][1]["observed_decision"] == "REJECT"
    assert report["independent_review_claim"] is False
    assert report["security_claim"] is False
    assert not validate_artifact("acceptance-report-v1", report)
    assert verify_bundle(root)["valid"] is True
    assert not (root / ".incomplete").exists()


def test_changed_fixture_fails_replay(tmp_path: Path) -> None:
    root = tmp_path / "acceptance"
    create_bundle(root)
    fixture = root / "fixtures" / "benign-control" / "SKILL.md"
    fixture.write_text("changed\n", encoding="utf-8")
    result = verify_bundle(root)
    assert result["valid"] is False
    assert "fixture_digest_mismatch:benign-control" in result["errors"]


def test_added_fixture_file_and_changed_human_card_fail_verification(tmp_path: Path) -> None:
    root = tmp_path / "acceptance"
    create_bundle(root)
    (root / "fixtures" / "benign-control" / "extra.txt").write_text("extra", encoding="utf-8")
    (root / "acceptance-card.md").write_text("PASSED", encoding="utf-8")
    result = verify_bundle(root)
    assert result["valid"] is False
    assert "fixture_digest_mismatch:benign-control" in result["errors"]
    assert "human_card_mismatch" in result["errors"]


def test_report_cannot_redirect_fixture_verification_outside_bundle(tmp_path: Path) -> None:
    root = tmp_path / "acceptance"
    create_bundle(root)
    report_path = root / "acceptance-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["fixtures"][0]["path"] = "../outside/SKILL.md"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = verify_bundle(root)
    assert result["valid"] is False
    assert "report_integrity_mismatch" in result["errors"]
    assert "fixture_path_invalid:benign-control" in result["errors"]


def test_cli_requires_new_directory_and_verifies_bundle(tmp_path: Path) -> None:
    root = tmp_path / "acceptance"
    runner = CliRunner()
    created = runner.invoke(cli, ["acceptance", "run", str(root)])
    assert created.exit_code == 0, created.output
    summary = json.loads(created.output)
    assert summary["independent_review_claim"] is False
    verified = runner.invoke(cli, ["acceptance", "verify", str(root)])
    assert verified.exit_code == 0, verified.output
    again = runner.invoke(cli, ["acceptance", "run", str(root)])
    assert again.exit_code != 0
