"""Adversarial contract, provenance, signature, I/O and cross-suite checks."""

import copy
import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from safe2.aism.ingest import create_assessment
from safe2.challenge.adapters import example_source, import_source
from safe2.challenge.compare import compare_runs
from safe2.challenge.integrity import seal, sign_run
from safe2.challenge.io import parse_json, read_json, write_json
from safe2.challenge.model import validate_run, verify_comparison, verify_run
from safe2.challenge.runner import run_challenge
from safe2.contracts import validate_artifact
from safe2.evidence.manifest import create_manifest


@pytest.fixture
def run():
    return run_challenge(treatments=["safe2-reference"])


def _keys(tmp_path: Path, name: str = "test") -> tuple[Path, Path]:
    private = Ed25519PrivateKey.generate()
    key = tmp_path / (name + ".pem")
    public = tmp_path / (name + ".pub.pem")
    key.write_bytes(private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    public.write_bytes(private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    return key, public


def test_all_contracts_and_regrading(run):
    assert validate_artifact("challenge-run", run) == []
    assert validate_artifact("challenge-source", example_source()) == []
    comparison = compare_runs(run, import_source(example_source(), "tenir"))
    assert validate_artifact("challenge-comparison", comparison) == []
    assert verify_comparison(comparison, run, import_source(example_source(), "tenir"))["valid"] is False
    # A freshly imported run has a different run ID, even if observations match.
    assert verify_comparison(comparison)["source_revalidation"] == "not_performed"
    validate_run(run)
    assert verify_run(run) == {"valid": True, "errors": [], "signature_status": "not_present"}


@pytest.mark.parametrize("mutation", ["summary", "grade", "claims", "duplicate", "protocol", "time", "limitation"])
def test_resealed_semantic_forgery_rejected(run, mutation):
    changed = copy.deepcopy(run)
    if mutation == "summary":
        changed["summary"]["episodes"] += 1
    elif mutation == "grade":
        changed["episodes"][0]["grade"]["unauthorized_change"] = True
    elif mutation == "claims":
        changed["claims"]["challenge_maturity"] = "C5"
    elif mutation == "duplicate":
        changed["episodes"].append(copy.deepcopy(changed["episodes"][0]))
    elif mutation == "protocol":
        changed["experiment"]["grader_sha256"] = "0" * 64
    elif mutation == "time":
        changed["created_at"] = "2026-01-01T00:00:00"
    else:
        changed["limitations"] = ["Everything is safe"]
    assert not verify_run(seal(changed))["valid"]


def test_ed25519_caller_trust_tamper_and_signer_binding(run, tmp_path):
    private, public = _keys(tmp_path)
    signed = sign_run(run, private, "fixture-reviewer")
    assert verify_run(signed, public, True)["signature_status"] == "valid_trusted_key"
    assert verify_run(signed)["signature_status"] == "unverified_no_trusted_key"
    assert not verify_run(signed, require_signature=True)["valid"]
    assert not verify_run(run, public, True)["valid"]
    _, wrong = _keys(tmp_path, "wrong")
    assert not verify_run(signed, wrong)["valid"]
    forged_label = copy.deepcopy(signed)
    forged_label["signature"]["signer_id"] = "upstream-TENIR"
    assert not verify_run(forged_label, public)["valid"]
    signed["provider"]["version"] = "forged"
    assert not verify_run(signed, public)["valid"]
    with pytest.raises(ValueError):
        sign_run(signed, private, "another-signer")


@pytest.mark.parametrize("data", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'[]', b'{', b'\xff'])
def test_strict_json_rejects_ambiguous_input(data):
    with pytest.raises(ValueError):
        parse_json(data)


def test_write_no_overwrite_and_input_size(tmp_path, monkeypatch):
    target = tmp_path / "run.json"
    write_json(target, {"value": 1})
    with pytest.raises(FileExistsError):
        write_json(target, {"value": 2})
    assert read_json(target) == {"value": 1}
    monkeypatch.setattr("safe2.challenge.io.MAX_BYTES", 5)
    with pytest.raises(ValueError):
        parse_json(b'{"value":1}')


def test_output_link_rejected_if_supported(tmp_path):
    directory = tmp_path / "real"
    directory.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(directory, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not permit test symlinks")
    with pytest.raises(ValueError):
        write_json(link / "artifact.json", {})
    assert not (directory / "artifact.json").exists()


def test_manifest_and_aism_keep_scope_and_reject_tampering(run, tmp_path):
    path = tmp_path / "fixture.json"
    write_json(path, run)
    manifest = create_manifest((path,), subject_id="fixture")
    assert manifest["summary"] == {"artifacts": 1, "valid": 1, "invalid": 0}
    assert manifest["artifacts"][0]["challenge_verification"]["signature_status"] == "not_present"
    assessment = create_assessment([run], subject_id="fixture", subject_name="Test fixture")
    assert len(assessment["cells"]) == 30
    assert all(value is None for value in assessment["cells"].values())
    assert assessment["topics"]["evidence_imports"][0]["source_bundle"] == run
    run["summary"]["episodes"] = 99
    path.write_text(json.dumps(run), encoding="utf-8")
    assert create_manifest((path,), subject_id="fixture")["summary"]["invalid"] == 1
    with pytest.raises(ValueError):
        create_assessment([run], subject_id="fixture", subject_name="Test fixture")


def test_comparison_revalidation_rejects_resealed_scores(run):
    right = import_source(example_source(), "tenir")
    comparison = compare_runs(run, right)
    assert verify_comparison(comparison, run, right)["valid"]
    comparison["outcome_agreement"]["agreements"] = 0
    comparison["outcome_agreement"]["disagreements"] = 6
    comparison["outcome_agreement"]["rate"] = 0
    assert not verify_comparison(seal(comparison), run, right)["valid"]


def test_source_export_and_retained_translation_binding(tmp_path):
    source = example_source()
    raw = json.dumps(source, indent=2).encode("utf-8")
    path = tmp_path / "source.json"
    path.write_bytes(raw)
    imported = import_source(source, "tenir", hashlib.sha256(raw).hexdigest())
    assert imported["provenance"]["source_hash_basis"] == "original_bytes"
    assert verify_run(imported, source_export=path)["valid"]
    path.write_bytes(json.dumps(source).encode("utf-8"))
    assert not verify_run(imported, source_export=path)["valid"]
    imported["episodes"][0]["decision"]["raw"] = "ALLOW"
    assert not verify_run(seal(imported))["valid"]


def test_canonical_source_hash_detects_resealed_provenance_change():
    imported = import_source(example_source(), "tenir")
    assert verify_run(imported)["valid"]
    imported["provenance"]["producer_id"] = "an-independent-third-party"
    assert not verify_run(seal(imported))["valid"]


@pytest.mark.skipif(__import__("os").name != "nt", reason="Windows device namespace")
@pytest.mark.parametrize("target", ["NUL", "CON", "report.txt:secret", "//server/share/report.json"])
def test_windows_device_network_and_stream_paths_rejected(target):
    from safe2.challenge.io import safe_path

    with pytest.raises(ValueError):
        safe_path(target)


def test_special_file_is_rejected_before_open(tmp_path, monkeypatch):
    from safe2.challenge.io import read_bytes

    target = tmp_path / "special"
    target.write_text("fixture", encoding="utf-8")
    original = Path.lstat

    def special_stat(path):
        if path == target:
            return os.stat_result((stat.S_IFIFO | 0o600, 0, 0, 1, 0, 0, 0, 0, 0, 0))
        return original(path)

    monkeypatch.setattr(Path, "lstat", special_stat)
    monkeypatch.setattr(os, "open", lambda *args: pytest.fail("Special file must not be opened"))
    with pytest.raises(ValueError):
        read_bytes(target)


def test_file_identity_change_during_open_is_rejected(tmp_path, monkeypatch):
    from safe2.challenge.io import read_bytes

    target = tmp_path / "input.json"
    target.write_text("fixture", encoding="utf-8")
    original = os.fstat

    def changed_identity(descriptor):
        values = list(original(descriptor))
        values[1] += 1
        return os.stat_result(values)

    monkeypatch.setattr(os, "fstat", changed_identity)
    with pytest.raises(ValueError, match="changed identity"):
        read_bytes(target)


def test_failed_exclusive_write_leaves_no_partial_destination(tmp_path, monkeypatch):
    from safe2.challenge.io import write_text

    target = tmp_path / "result.json"

    def fail_sync(*_args, **_kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(os, "fsync", fail_sync)
    with pytest.raises(OSError, match="write failure"):
        write_text(target, "complete body")
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO behavior")
def test_fifo_rejected_without_waiting_for_writer(tmp_path):
    from safe2.challenge.io import read_bytes

    target = tmp_path / "pipe"
    os.mkfifo(target)
    with pytest.raises(ValueError):
        read_bytes(target)


def test_missing_source_has_accurate_error(tmp_path):
    imported = import_source(example_source(), "tenir")
    assert verify_run(imported, source_export=tmp_path / "absent.json")["errors"] == ["source_export_unreadable"]
