"""Portable offline starter bundles; no submitted code or paths are executed."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2 import __version__
from safe2.challenge.adapters import example_source, import_source
from safe2.challenge.compare import compare_runs
from safe2.challenge.integrity import canonical_bytes, seal, verify_digest
from safe2.challenge.io import parse_json, read_bytes, safe_path, write_json, write_text
from safe2.challenge.model import verify_comparison, verify_run
from safe2.challenge.report import render_report
from safe2.challenge.runner import run_challenge
from safe2.contracts import validate_artifact

FILES = (
    "native-run.json", "reference-run.json", "tenir-source.json", "tenir-import.json",
    "comparison.json", "decision-card.md", "decision-card.html", "comparison-card.md", "README.md",
)
README = """# AI SAFE² offline evidence bundle

Start with decision-card.html or decision-card.md. These contain synthetic
fixture outcomes, not live-agent validation or deployment approval.

The all-treatment run has 18 episodes. The separate reference run and synthetic
TENIR example each have six. TENIR was not executed and has not endorsed this
example contract. Matching results are translation checks, not replication.

From the parent directory, use the bundle folder as the final argument:

    safe2 challenge verify-bundle BUNDLE_DIRECTORY

For a trusted manifest fingerprint obtained separately:

    safe2 challenge verify-bundle BUNDLE_DIRECTORY --expected-sha256 TRUSTED_HASH

The verifier never runs code from this bundle. It checks a fixed file set,
hashes, source translation, pinned graders, fixture replay and derived reports.
An untrusted hash is not authorship or factual truth. Keep the complete folder.
Do not treat a successful verification as framework conformance or an AISM score.
"""
LIMITATIONS = [
    "Offline synthetic fixture only; no live agents or third-party runtime executed.",
    "Translation agreement is not independent replication or framework conformance.",
    "Unsigned hashes require a separately trusted fingerprint for tamper resistance against resealing.",
]


def _encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def quickstart(output_dir: str | Path, challenge_id: str = "001") -> dict[str, Any]:
    """Create one new directory; incomplete failures retain evidence, never overwrite."""
    if challenge_id != "001":
        raise ValueError("Only Challenge 001 is supported")
    target = safe_path(output_dir)
    if target.exists():
        raise FileExistsError("Use a new output directory")
    native = run_challenge()
    reference = run_challenge(treatments=["safe2-reference"])
    source = example_source()
    imported = import_source(source, "tenir", hashlib.sha256(_encoded(source)).hexdigest())
    comparison = compare_runs(reference, imported)
    documents = {
        "native-run.json": native, "reference-run.json": reference,
        "tenir-source.json": source, "tenir-import.json": imported, "comparison.json": comparison,
    }
    reports = {
        "decision-card.md": render_report(native),
        "decision-card.html": render_report(native, format_name="html"),
        "comparison-card.md": render_report(comparison), "README.md": README,
    }
    target.mkdir(mode=0o700)
    for name, value in documents.items():
        write_json(target / name, value)
    for name, report in reports.items():
        write_text(target / name, report)
    records = []
    for name in FILES:
        raw = read_bytes(target / name, limit=5_000_000)
        records.append({"name": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    manifest = seal({
        "schema_version": "safe2.challenge-bundle.v1", "kind": "offline-quickstart",
        "created_at": datetime.now(UTC).isoformat(),
        "producer": {"name": "safe2", "version": __version__},
        "experiment": native["experiment"], "files": records,
        "independent_replication": "not_established", "limitations": LIMITATIONS,
    })
    if validate_artifact("challenge-bundle", manifest):
        raise ValueError("Bundle manifest violates its contract")
    # Written last: an interrupted folder must not look like a complete bundle.
    write_json(target / "bundle.json", manifest)
    result = verify_bundle(target)
    if not result["valid"]:
        raise ValueError("Generated bundle failed verification; partial output retained")
    return {
        "schema_version": "safe2.challenge-quickstart.v1", "valid": True,
        "output_dir": str(target), "decision_card": str(target / "decision-card.html"),
        "manifest_sha256": result["manifest_sha256"], "checks": result["checks"],
        "live_agent_validation": False, "independent_replication": "not_established",
    }


def verify_bundle(directory: str | Path, expected_sha256: str | None = None) -> dict[str, Any]:
    """Verify the fixed starter contract without trusting submitted file paths."""
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("Expected a lowercase SHA-256 fingerprint")
    target = safe_path(directory)
    if not target.is_dir():
        raise ValueError("Bundle must be a local directory")
    checks: list[dict[str, str]] = []
    fingerprint: str | None = None

    def check(name: str, condition: bool) -> None:
        checks.append({"name": name, "status": "passed" if condition else "failed"})

    try:
        # Bound enumeration too, rather than loading an arbitrary directory listing.
        names = set()
        for child in target.iterdir():
            names.add(child.name)
            if len(names) > len(FILES) + 1:
                break
        check("exact_file_set", names == {*FILES, "bundle.json"})
        raw_manifest = read_bytes(target / "bundle.json", limit=100_000)
        fingerprint = hashlib.sha256(raw_manifest).hexdigest()
        if expected_sha256 is not None:
            check("trusted_manifest_fingerprint", fingerprint == expected_sha256)
        manifest = parse_json(raw_manifest)
        check("manifest_contract", not validate_artifact("challenge-bundle", manifest))
        if checks[-1]["status"] != "passed":
            raise ValueError("Invalid manifest contract")
        check("timestamp", datetime.fromisoformat(manifest["created_at"]).tzinfo is not None)
        check("producer_version", manifest["producer"]["version"] == __version__)
        check("manifest_seal", verify_digest(manifest))
        check("limitations_retained", manifest["limitations"] == LIMITATIONS)
        records = {row["name"]: row for row in manifest["files"]}
        check("manifest_file_set", len(records) == len(FILES) and set(records) == set(FILES))
        if any(row["status"] == "failed" for row in checks):
            raise ValueError("Invalid bundle structure or fingerprint")
        contents = {}
        for name in FILES:
            raw = read_bytes(target / name, limit=5_000_000)
            contents[name] = raw
            check("file:" + name, len(raw) == records[name]["bytes"]
                  and hashlib.sha256(raw).hexdigest() == records[name]["sha256"])
        if any(row["status"] == "failed" for row in checks):
            raise ValueError("Changed or missing bundle artifacts")
        native, reference, source, imported, comparison = (
            parse_json(contents[name]) for name in FILES[:5]
        )
        check("native_regrading", verify_run(native)["valid"])
        check("reference_regrading", verify_run(reference)["valid"])
        check("import_regrading", verify_run(imported)["valid"])
        expected_import = import_source(source, "tenir", hashlib.sha256(contents["tenir-source.json"]).hexdigest())
        check("source_binding", all(imported[key] == expected_import[key] for key in (
            "experiment", "provider", "provenance", "episodes", "summary", "claims", "limitations"
        )))
        check("comparison_reconstructed", verify_comparison(comparison, reference, imported)["valid"])
        fresh = run_challenge()
        check("pinned_experiment", manifest["experiment"] == native["experiment"] == fresh["experiment"])
        check("native_fixture_replay", native["episodes"] == fresh["episodes"])
        check("native_fixture_identity", all(native[key] == fresh[key] for key in (
            "provider", "provenance", "claims", "limitations", "summary"
        )))
        check("reference_fixture_identity", all(reference[key] == fresh[key] for key in (
            "provider", "provenance", "claims", "limitations"
        )))
        check("reference_fixture_replay", reference["episodes"] == [
            row for row in fresh["episodes"] if row["treatment"] == "safe2-reference"
        ] and reference["experiment"] == fresh["experiment"])
        check("synthetic_example_identity", canonical_bytes(source) == canonical_bytes(example_source()))
        check("decision_markdown", contents["decision-card.md"] == render_report(native).encode("utf-8"))
        check("decision_html", contents["decision-card.html"] == render_report(native, format_name="html").encode("utf-8"))
        check("comparison_markdown", contents["comparison-card.md"] == render_report(comparison).encode("utf-8"))
        check("replay_instructions", contents["README.md"] == README.encode("utf-8"))
    except (ValueError, OSError, TypeError, KeyError, RecursionError):
        check("bundle_complete_and_readable", False)
    return {
        "schema_version": "safe2.challenge-bundle-verification.v1",
        "valid": bool(checks) and all(row["status"] == "passed" for row in checks),
        "manifest_sha256": fingerprint, "checks": checks,
        "trust_basis": "caller_supplied_fingerprint" if expected_sha256 else "internal_consistency_only",
        "independent_replication": "not_established", "live_agent_validation": False,
    }
