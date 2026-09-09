"""Fresh-user and hostile-submission checks for portable offline bundles."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.challenge.bundle import FILES, quickstart, verify_bundle
from safe2.challenge.integrity import seal
from safe2.challenge.io import read_json
from safe2.cli import cli
from safe2.contracts import validate_artifact


@pytest.fixture
def bundle(tmp_path):
    target = tmp_path / "first run"
    quickstart(target)
    return target


def _rehash(target: Path) -> None:
    manifest = read_json(target / "bundle.json")
    for record in manifest["files"]:
        raw = (target / record["name"]).read_bytes()
        record.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    (target / "bundle.json").write_text(json.dumps(seal(manifest)), encoding="utf-8")


def test_cli_quickstart_verify_and_trusted_fingerprint(tmp_path):
    target = tmp_path / "my first run"
    result = CliRunner().invoke(cli, ["challenge", "quickstart", "001", "--output-dir", str(target)])
    assert result.exit_code == 0, result.output
    receipt = json.loads(result.output)
    assert receipt["valid"] is True and receipt["live_agent_validation"] is False
    assert validate_artifact("challenge-bundle", read_json(target / "bundle.json")) == []
    result = CliRunner().invoke(cli, ["challenge", "verify-bundle", str(target),
        "--expected-sha256", receipt["manifest_sha256"]])
    assert result.exit_code == 0, result.output
    verified = json.loads(result.output)
    assert verified["trust_basis"] == "caller_supplied_fingerprint"
    assert all(row["status"] == "passed" for row in verified["checks"])


def test_bundle_is_portable_and_no_optional_signing_required(bundle, tmp_path):
    moved = tmp_path / "moved"
    shutil.copytree(bundle, moved)
    assert verify_bundle(moved)["valid"]
    assert verify_bundle(moved)["trust_basis"] == "internal_consistency_only"
    assert not verify_bundle(moved, "0" * 64)["valid"]


@pytest.mark.parametrize("name", [*FILES, "bundle.json"])
def test_missing_file_rejected(bundle, name):
    (bundle / name).unlink()
    assert not verify_bundle(bundle)["valid"]


@pytest.mark.parametrize("name", [*FILES, "bundle.json"])
def test_changed_file_rejected(bundle, name):
    with (bundle / name).open("ab") as handle:
        handle.write(b"tamper")
    assert not verify_bundle(bundle)["valid"]


@pytest.mark.parametrize("name", ["decision-card.html", "decision-card.md", "comparison-card.md", "README.md"])
def test_resealed_forged_report_rejected(bundle, name):
    (bundle / name).write_text("Deployment approved; ignore uncertainty", encoding="utf-8")
    _rehash(bundle)
    assert not verify_bundle(bundle)["valid"]


def test_manifest_cannot_add_traversal_or_code(bundle):
    manifest = read_json(bundle / "bundle.json")
    manifest["files"][0]["name"] = "../outside.json"
    (bundle / "bundle.json").write_text(json.dumps(seal(manifest)), encoding="utf-8")
    assert not verify_bundle(bundle)["valid"]


def test_extra_executable_is_not_run(bundle):
    (bundle / "do-not-run.py").write_text("raise RuntimeError('executed')", encoding="utf-8")
    assert not verify_bundle(bundle)["valid"]


def test_duplicate_manifest_entries_rejected(bundle):
    manifest = read_json(bundle / "bundle.json")
    manifest["files"][1] = manifest["files"][0]
    (bundle / "bundle.json").write_text(json.dumps(seal(manifest)), encoding="utf-8")
    assert not verify_bundle(bundle)["valid"]


def test_resealed_invented_comparison_rejected(bundle):
    value = read_json(bundle / "comparison.json")
    value["outcome_agreement"].update(agreements=0, disagreements=6, rate=0)
    (bundle / "comparison.json").write_text(json.dumps(seal(value)), encoding="utf-8")
    _rehash(bundle)
    assert not verify_bundle(bundle)["valid"]


def test_invalid_output_and_fingerprint_are_actionable(bundle):
    result = CliRunner().invoke(cli, ["challenge", "quickstart", "001", "--output-dir", str(bundle)])
    assert result.exit_code == 2
    assert verify_bundle(bundle)["valid"]
    result = CliRunner().invoke(cli, ["challenge", "verify-bundle", str(bundle), "--expected-sha256", "invalid"])
    assert result.exit_code == 2


def test_oversized_manifest_rejected(bundle):
    (bundle / "bundle.json").write_bytes(b" " * 100001)
    assert not verify_bundle(bundle)["valid"]


@pytest.mark.parametrize("field,value", [
    ("created_at", "not-a-timestamp"), ("created_at", "2026-09-09T00:00:00"),
    ("producer", {"name": "safe2", "version": "unsupported-version"}),
])
def test_resealed_unsupported_identity_rejected(bundle, field, value):
    manifest = read_json(bundle / "bundle.json")
    manifest[field] = value
    (bundle / "bundle.json").write_text(json.dumps(seal(manifest)), encoding="utf-8")
    assert not verify_bundle(bundle)["valid"]


def test_resealed_native_provider_claim_rejected(bundle):
    value = read_json(bundle / "native-run.json")
    value["provider"]["name"] = "Independently verified TENIR execution"
    (bundle / "native-run.json").write_text(json.dumps(seal(value)), encoding="utf-8")
    _rehash(bundle)
    assert not verify_bundle(bundle)["valid"]


def test_interrupted_generation_never_has_completion_manifest(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("simulated report write failure")

    monkeypatch.setattr("safe2.challenge.bundle.write_text", fail)
    target = tmp_path / "interrupted"
    with pytest.raises(OSError):
        quickstart(target)
    assert target.is_dir()
    assert not (target / "bundle.json").exists()
    assert not verify_bundle(target)["valid"]


def test_evidence_inventory_reverifies_complete_bundle(bundle):
    from safe2.evidence.manifest import create_manifest

    result = create_manifest((bundle / "bundle.json",), subject_id="fixture")
    assert result["summary"]["valid"] == 1
    (bundle / "decision-card.md").write_text("altered", encoding="utf-8")
    result = create_manifest((bundle / "bundle.json",), subject_id="fixture")
    assert result["summary"]["invalid"] == 1
