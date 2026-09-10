from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.challenge.integrity import seal
from safe2.challenge.io import read_json, write_json
from safe2.challenge.report import render_report
from safe2.challenge.runner import run_challenge
from safe2.cli import cli


def invoke(*arguments: str):
    return CliRunner().invoke(cli, ["challenge", *arguments])


def test_cli_discovers_and_validates_packaged_study():
    result = invoke("list")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["challenges"][0]["live_agent_execution"] is False
    result = invoke("validate", "001")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["framework_profile_conformance"] == "not_assessed"


def test_cli_native_run_verify_report(tmp_path: Path):
    output = tmp_path / "native.json"
    result = invoke("run", "001", "--output", str(output))
    assert result.exit_code == 0, result.output
    assert read_json(output)["summary"]["episodes"] == 18
    assert invoke("verify", str(output)).exit_code == 0
    card = tmp_path / "card.md"
    result = invoke("report", str(output), "--output", str(card))
    assert result.exit_code == 0, result.output
    text = card.read_text(encoding="utf-8")
    assert "AI SAFE² Challenge Decision Card" in text
    assert "Conformance" not in text or "not" in text
    assert "probabilities of deployment success" in text
    assert "conventional" in text
    assert "unknown or not applicable" in text


def test_cli_existing_output_is_not_overwritten(tmp_path: Path):
    output = tmp_path / "keep.json"
    output.write_text("keep this", encoding="utf-8")
    result = invoke("run", "001", "--output", str(output))
    assert result.exit_code == 2
    assert output.read_text(encoding="utf-8") == "keep this"


@pytest.mark.parametrize("arguments", [
    ("run", "001", "--repetitions", "0"),
    ("run", "001", "--repetitions", "101"),
    ("run", "001", "--seed", "-1"),
    ("run", "002"),
])
def test_cli_bounds(arguments: tuple[str, ...], tmp_path: Path):
    assert invoke(*arguments, "--output", str(tmp_path / "not-created.json")).exit_code == 2
    assert not (tmp_path / "not-created.json").exists()


@pytest.mark.parametrize("payload", [
    '{"secret":"DO_NOT_ECHO",',
    '{"secret":"DO_NOT_ECHO","secret":"duplicate"}',
    '{"value":NaN,"secret":"DO_NOT_ECHO"}',
    '["DO_NOT_ECHO"]',
])
def test_cli_malformed_source_has_sanitized_json_error(tmp_path: Path, payload: str):
    source = tmp_path / "malformed.json"
    source.write_text(payload, encoding="utf-8")
    result = invoke("import", str(source), "--output", str(tmp_path / "out.json"))
    assert result.exit_code == 2
    assert "DO_NOT_ECHO" not in result.output
    assert json.loads(result.output)["instance_values_emitted"] is False


def test_cli_synthetic_provider_source_fingerprint_and_comparison(tmp_path: Path):
    source, imported, native, comparison = [tmp_path / name for name in (
        "source.json", "import.json", "native.json", "comparison.json",
    )]
    assert invoke("example", "--provider", "tenir", "--output", str(source)).exit_code == 0
    result = invoke("import", str(source), "--adapter", "tenir", "--output", str(imported))
    assert result.exit_code == 0, result.output
    assert read_json(imported)["provenance"]["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert invoke("verify", str(imported), "--source-export", str(source)).exit_code == 0
    assert invoke("run", "001", "--treatment", "safe2-reference", "--output", str(native)).exit_code == 0
    result = invoke("compare", str(native), str(imported), "--output", str(comparison))
    assert result.exit_code == 0, result.output
    assert read_json(comparison)["independent_replication"] == "not_established"
    result = invoke("verify", str(comparison), "--left-run", str(native), "--right-run", str(imported))
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["source_revalidation"] == "performed"
    result = invoke("report", str(comparison))
    assert result.exit_code == 0, result.output
    assert "Verification boundary" in result.output


def test_cli_mismatch_comparison_retains_explanation(tmp_path: Path):
    left, right, output = [tmp_path / name for name in ("left.json", "right.json", "out.json")]
    write_json(left, run_challenge(seed=0))
    write_json(right, run_challenge(seed=1))
    result = invoke("compare", str(left), str(right), "--output", str(output))
    assert result.exit_code == 1, result.output
    assert read_json(output)["comparable"] is False
    assert read_json(output)["outcome_agreement"] is None


def test_cli_tampered_run_rejected_by_verify_and_report(tmp_path: Path):
    run = run_challenge()
    run["summary"]["episodes"] = 999
    source = tmp_path / "tampered.json"
    write_json(source, run)
    assert invoke("verify", str(source)).exit_code == 1
    result = invoke("report", str(source), "--output", str(tmp_path / "no.md"))
    assert result.exit_code == 1
    assert not (tmp_path / "no.md").exists()


def test_reports_escape_untrusted_values_and_remain_self_contained():
    run = copy.deepcopy(run_challenge())
    run["provider"]["name"] = '<script>alert(1)</script> [link](https://example.invalid)'
    run = seal(run)
    html = render_report(run, format_name="html")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert 'href="https://example.invalid"' not in html
    assert "Content-Security-Policy" in html
    markdown = render_report(run)
    assert "<script>" not in markdown
    assert r"\[link\]" in markdown
    assert "not independently observed live-system facts" in markdown


def test_cli_signature_round_trip_and_wrong_key(tmp_path: Path):
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.generate()
    private, public, wrong = [tmp_path / name for name in ("private.pem", "public.pem", "wrong.pem")]
    private.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption(),
    ))
    public.write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    wrong.write_bytes(Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    source, signed = tmp_path / "source.json", tmp_path / "signed.json"
    write_json(source, run_challenge())
    result = invoke("sign", str(source), "--key", str(private), "--signer-id", "test-operator", "--output", str(signed))
    assert result.exit_code == 0, result.output
    result = invoke("verify", str(signed), "--public-key", str(public), "--require-signature")
    assert result.exit_code == 0, result.output
    assert invoke("verify", str(signed), "--public-key", str(wrong), "--require-signature").exit_code == 1


def test_aism_ingest_rejects_tampered_challenge_cleanly(tmp_path: Path):
    source, output = tmp_path / "source.json", tmp_path / "assessment.json"
    run = run_challenge()
    run["summary"]["episodes"] = 99
    write_json(source, run)
    result = CliRunner().invoke(cli, ["aism", "ingest", str(source), "--subject-id", "fixture",
        "--subject-name", "Fixture", "--output", str(output)])
    assert result.exit_code == 1
    assert "Evidence ingestion failed" in result.output
    assert "Traceback" not in result.output
    assert not output.exists()


def test_aism_ingest_does_not_overwrite(tmp_path: Path):
    source, output = tmp_path / "source.json", tmp_path / "assessment.json"
    write_json(source, run_challenge())
    output.write_text("keep", encoding="utf-8")
    result = CliRunner().invoke(cli, ["aism", "ingest", str(source), "--subject-id", "fixture",
        "--subject-name", "Fixture", "--output", str(output)])
    assert result.exit_code == 1
    assert output.read_text(encoding="utf-8") == "keep"
