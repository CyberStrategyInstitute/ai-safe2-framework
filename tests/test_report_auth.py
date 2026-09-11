"""Origin and freshness are not truth; test trust boundaries and signed tampering."""

import hashlib
import json

import pytest
from click.testing import CliRunner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence import report_auth
from safe2.evidence.task_receipt import evaluate_task


@pytest.fixture
def material(tmp_path, monkeypatch):
    monkeypatch.setattr(report_auth.time, "time", lambda: 1000)
    private = Ed25519PrivateKey.generate()
    key, public = tmp_path / "key.pem", tmp_path / "key.pub.pem"
    key.write_bytes(private.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public.write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo))
    report = {"schema_version": "safe2.tool-result.v1", "task_id": "t1",
              "revision": "r1", "environment": "env1", "source_ref": "event1",
              "call_id": "c1", "tool": "search", "outcome": "unavailable"}
    payload = json.dumps(report).encode()
    return key, public, payload


def test_roundtrip_and_contract(material):
    key, public, payload = material
    attestation = report_auth.sign_report(payload, key, "collector-1")
    assert validate_artifact("report-attestation-v1", attestation) == []
    assert report_auth.verify_report(payload, attestation, public) == "authenticated_trusted_key"


@pytest.mark.parametrize("field,value", [("signer_id", "other"), ("issued_at", 999),
                                        ("expires_at", 4599), ("signature_base64", "A" * 86 + "==")])
def test_signed_metadata_tamper_rejected(material, field, value):
    key, public, payload = material
    attestation = report_auth.sign_report(payload, key, "collector-1")
    attestation[field] = value
    assert report_auth.verify_report(payload, attestation, public) != "authenticated_trusted_key"


def test_report_changed_and_digest_rewritten(material):
    key, public, payload = material
    attestation = report_auth.sign_report(payload, key, "collector-1")
    changed = payload.replace(b"unavailable", b"succeeded")
    assert report_auth.verify_report(changed, attestation, public) == "report_digest_mismatch"
    attestation["report_sha256"] = hashlib.sha256(changed).hexdigest()
    assert report_auth.verify_report(changed, attestation, public) == "invalid_signature_or_key"


@pytest.mark.parametrize("now,expected", [(999, "not_yet_valid"), (1000, "authenticated_trusted_key"),
                                         (1059, "authenticated_trusted_key"), (1060, "expired")])
def test_expiry_boundaries(material, monkeypatch, now, expected):
    key, public, payload = material
    attestation = report_auth.sign_report(payload, key, "collector-1", 60)
    monkeypatch.setattr(report_auth.time, "time", lambda: now)
    assert report_auth.verify_report(payload, attestation, public) == expected


def test_report_cannot_supply_its_own_trust(material, tmp_path):
    key, _, payload = material
    other = Ed25519PrivateKey.generate().public_key()
    public = tmp_path / "other.pub.pem"
    public.write_bytes(other.public_bytes(serialization.Encoding.PEM,
                                         serialization.PublicFormat.SubjectPublicKeyInfo))
    attestation = report_auth.sign_report(payload, key, "collector-1")
    assert report_auth.verify_report(payload, attestation, public) == "untrusted_key"


@pytest.mark.parametrize("ttl", [0, -1, 86401, True])
def test_invalid_ttl(material, ttl):
    key, _, payload = material
    with pytest.raises(ValueError):
        report_auth.sign_report(payload, key, "collector", ttl)


def test_unrecognized_content_not_signed(material):
    key, _, _ = material
    with pytest.raises(ValueError):
        report_auth.sign_report(b'{"schema_version":"other"}', key, "collector")


def document(tmp_path, payload, attestation):
    (tmp_path / "report.json").write_bytes(payload)
    (tmp_path / "signature.json").write_text(json.dumps(attestation), encoding="utf-8")
    return {"schema_version": "safe2.task-receipt-input.v1", "task_id": "t1",
            "parent_task_id": None, "harness": "test", "usage": [], "criteria": [{
                "id": "claim", "kind": "tool_report", "path": "report.json",
                "attestation_path": "signature.json", "expected_sha256": hashlib.sha256(payload).hexdigest(),
                "expected_revision": "r1", "expected_environment": "env1", "expected_tool": "search",
                "expected_call_id": "c1", "claimed_outcome": "succeeded"}]}


def test_signed_failure_is_still_failure(material, tmp_path):
    key, public, payload = material
    source = document(tmp_path, payload, report_auth.sign_report(payload, key, "collector"))
    result = evaluate_task(source, tmp_path, trusted_public_key=public, require_authentication=True)
    assert result["criteria"][0]["authentication"] == "authenticated_trusted_key"
    assert result["counts"]["contradicted"] == 1
    assert result["completion_verified"] is False
    assert validate_artifact("task-receipt-v1", result) == []


def test_required_authentication_and_no_key(material, tmp_path):
    key, _, payload = material
    source = document(tmp_path, payload, report_auth.sign_report(payload, key, "collector"))
    with pytest.raises(ValueError):
        evaluate_task(source, tmp_path, require_authentication=True)
    result = evaluate_task(source, tmp_path)
    assert result["criteria"][0]["authentication"] == "unverified_no_trusted_key"


@pytest.mark.parametrize("mode", ["missing", "malformed", "expired", "path_missing"])
def test_required_authentication_cannot_downgrade_to_unsigned(material, tmp_path, monkeypatch, mode):
    key, public, payload = material
    source = document(tmp_path, payload, report_auth.sign_report(payload, key, "collector"))
    if mode == "missing":
        del source["criteria"][0]["attestation_path"]
    elif mode == "path_missing":
        source["criteria"][0]["attestation_path"] = "missing.json"
    elif mode == "malformed":
        (tmp_path / "signature.json").write_bytes(b'{"x":1,"x":2}')
    else:
        monkeypatch.setattr(report_auth.time, "time", lambda: 10000)
    result = evaluate_task(source, tmp_path, trusted_public_key=public, require_authentication=True)
    assert result["counts"]["unverifiable"] == 1
    assert result["criteria"][0]["reason"] == "report_authentication_not_established"


def test_cli_sign_verify_and_no_overwrite(material, tmp_path):
    key, public, payload = material
    report = tmp_path / "report.json"
    report.write_bytes(payload)
    signature = tmp_path / "signature.json"
    args = ["feedback", "sign-report", str(report), "--private-key", str(key),
            "--signer-id", "collector", "--output", str(signature)]
    runner = CliRunner()
    assert runner.invoke(cli, args).exit_code == 0
    assert runner.invoke(cli, args).exit_code != 0
    result = runner.invoke(cli, ["feedback", "verify-report", str(report), str(signature),
                                 "--trusted-public-key", str(public)])
    assert result.exit_code == 0
    assert json.loads(result.output)["execution_verified"] is False
    report.write_bytes(payload + b" ")
    result = runner.invoke(cli, ["feedback", "verify-report", str(report), str(signature),
                                 "--trusted-public-key", str(public)])
    assert result.exit_code == 1
