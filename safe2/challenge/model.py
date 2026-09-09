"""Validate and independently regrade Challenge Lab evidence before trusting output."""

from __future__ import annotations

import copy
import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.challenge.integrity import canonical_bytes, digest, seal, verify_digest, verify_signature
from safe2.contracts import validate_artifact

LIMITATIONS = [
    "Fixture mechanics do not establish real-agent effectiveness or framework conformance.",
    "Imported observations and producer identity are declarations, not independently verified facts.",
    "Translation and replay are not independent replication; independent operators and source evidence are required.",
    "SHA-256 detects changes relative to a recorded digest; it does not authenticate the author.",
    "Artifact signatures authenticate only against the caller-supplied key, not upstream observations or human approval.",
    "Rates describe these selected episodes, not probabilities of deployment success or failure.",
]


def _claims(kind: str) -> dict[str, str]:
    return {
        "challenge_maturity": "unverified" if kind == "external_import" else "C2",
        "framework_profile_conformance": "not_assessed",
        "aism_maturity": "not_assessed",
        "independent_replication": "not_established",
    }


def _source_envelope(run: dict[str, Any]) -> dict[str, Any]:
    from safe2.challenge.adapters import ADAPTER_CONTRACTS

    return {
        "schema_version": "safe2.challenge-source.v1",
        "adapter_contract": ADAPTER_CONTRACTS[run["provenance"]["adapter_id"]],
        "provider": run["provider"], "producer_id": run["provenance"]["producer_id"],
        "run_id": run["provenance"]["source_run_id"],
        "synthetic": run["provenance"]["kind"] == "synthetic_import",
        "experiment": run["experiment"],
        "episodes": [episode["source_record"] for episode in run["episodes"]],
    }


def validate_run(run: dict[str, Any]) -> None:
    from safe2.challenge.grading import grade_episode, summarize
    from safe2.challenge.protocol import experiment as pinned_experiment
    from safe2.challenge.protocol import scenario

    # JSON serialization also rejects non-finite values hidden in nested source data.
    canonical_bytes(run)
    if validate_artifact("challenge-run", run):
        raise ValueError("Challenge run violates its packaged schema")
    pinned = pinned_experiment(run["experiment"]["seed"])
    for key in ("challenge_id", "protocol_version", "scenario_set_sha256", "grader_version",
                "grader_sha256", "framework_version", "enforcement_plane"):
        if run["experiment"][key] != pinned[key]:
            raise ValueError("Unsupported protocol or grader identity; use its pinned implementation")
    if datetime.fromisoformat(run["created_at"]).tzinfo is None:
        raise ValueError("Artifact timestamp must include a timezone")
    seen_ids: set[str] = set()
    seen_cases: set[tuple[str, int, str]] = set()
    imported = run["provenance"]["kind"] != "native_fixture"
    if imported and (not run["provenance"]["source_sha256"]
                     or not run["provenance"]["source_hash_basis"]
                     or not run["provenance"]["source_run_id"]):
        raise ValueError("Imported runs require source identity")
    if not imported and any(run["provenance"][key] is not None for key in (
        "source_sha256", "source_hash_basis", "source_run_id"
    )):
        raise ValueError("Native fixture provenance must not claim an imported source")
    for episode in run["episodes"]:
        scenario(episode["scenario_id"])
        case_key = (episode["scenario_id"], episode["trial"], episode["treatment"])
        if episode["id"] in seen_ids or case_key in seen_cases:
            raise ValueError("Duplicate episode identity or case/trial/treatment")
        seen_ids.add(episode["id"])
        seen_cases.add(case_key)
        if imported and "source_record" not in episode:
            raise ValueError("Imported runs must retain original episode records")
        if imported:
            from safe2.challenge.adapters import validate_translation

            validate_translation(episode, run["provenance"]["adapter_id"],
                                 run["provenance"]["adapter_version"])
        if episode["grade"] != grade_episode(episode):
            raise ValueError("Episode grade differs from independent state grading")
    if run["summary"] != summarize(run["episodes"]):
        raise ValueError("Summary differs from independently regraded episodes")
    if (imported and run["provenance"]["source_hash_basis"] == "canonical_json"
            and digest(_source_envelope(run)) != run["provenance"]["source_sha256"]):
        raise ValueError("Retained source differs from its canonical source digest")
    if run["claims"] != _claims(run["provenance"]["kind"]):
        raise ValueError("Unsupported maturity or conformance claim")
    if not set(LIMITATIONS).issubset(run["limitations"]):
        raise ValueError("Artifact must preserve evidence limitations")


def make_run(episodes: list[dict[str, Any]], experiment: dict[str, Any],
             provenance: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    from safe2.challenge.grading import grade_episode, summarize

    graded = copy.deepcopy(episodes)
    for episode in graded:
        episode["grade"] = grade_episode(episode)
    result = seal({
        "schema_version": "safe2.challenge-run.v1",
        "run_id": f"challenge-run-{uuid.uuid4()}",
        "created_at": datetime.now(UTC).isoformat(),
        "experiment": copy.deepcopy(experiment), "provider": copy.deepcopy(provider),
        "provenance": copy.deepcopy(provenance), "episodes": graded,
        "summary": summarize(graded), "claims": _claims(provenance["kind"]),
        "limitations": list(LIMITATIONS),
    })
    validate_run(result)
    return result


def verify_run(run: dict[str, Any], public_key: str | Path | None = None,
               require_signature: bool = False,
               source_export: str | Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    signature_status = "not_checked"
    try:
        validate_run(run)
        if not verify_digest(run):
            errors.append("integrity_mismatch")
        signature_status = verify_signature(run, public_key)
        if signature_status == "invalid":
            errors.append("signature_invalid")
        if require_signature and signature_status != "valid_trusted_key":
            errors.append("trusted_signature_required")
        if source_export is not None:
            from safe2.challenge.io import parse_json, read_bytes

            if run["provenance"]["kind"] == "native_fixture":
                errors.append("native_run_has_no_source_export")
            else:
                try:
                    raw = read_bytes(source_export)
                except OSError:
                    errors.append("source_export_unreadable")
                    return {"valid": False, "errors": errors, "signature_status": signature_status}
                source = parse_json(raw)
                source_hash = (hashlib.sha256(raw).hexdigest()
                               if run["provenance"]["source_hash_basis"] == "original_bytes"
                               else digest(source))
                if source_hash != run["provenance"]["source_sha256"] or source != _source_envelope(run):
                    errors.append("source_export_mismatch")
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        errors.append("invalid_artifact")
    except OSError:
        errors.append("trusted_key_unreadable")
    return {"valid": not errors, "errors": errors, "signature_status": signature_status}


def verify_comparison(artifact: dict[str, Any], left: dict[str, Any] | None = None,
                      right: dict[str, Any] | None = None) -> dict[str, Any]:
    """A standalone comparison is change-detectable, not independently re-evaluated."""
    errors: list[str] = []
    try:
        canonical_bytes(artifact)
        if validate_artifact("challenge-comparison", artifact):
            raise ValueError("Invalid comparison structure")
        if not verify_digest(artifact):
            errors.append("integrity_mismatch")
        if artifact["comparable"] != (not artifact["mismatches"]):
            errors.append("inconsistent_comparability")
        agreement = artifact["outcome_agreement"]
        if artifact["comparable"] != (agreement is not None):
            errors.append("inconsistent_outcome_agreement")
        if agreement:
            total = agreement["agreements"] + agreement["disagreements"]
            if total != agreement["evaluated_pairs"]:
                errors.append("inconsistent_counts")
            pairs = total + agreement["incomplete_pairs"]
            if pairs > 1800 or agreement["conflict_pairs"] > pairs:
                errors.append("inconsistent_pair_counts")
            rate = agreement["agreements"] / total if total else None
            if agreement["rate"] != rate:
                errors.append("inconsistent_rate")
        if left is not None and right is not None:
            from safe2.challenge.compare import compare_runs
            expected = compare_runs(left, right)
            for key in ("left", "right", "comparable", "mismatches", "outcome_agreement",
                        "independent_replication", "limitations"):
                if artifact[key] != expected[key]:
                    errors.append("source_comparison_mismatch")
                    break
        elif left is not None or right is not None:
            errors.append("both_source_runs_required")
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        errors.append("invalid_artifact")
    return {"valid": not errors, "errors": errors,
            "source_revalidation": "performed" if left is not None and right is not None else "not_performed"}
