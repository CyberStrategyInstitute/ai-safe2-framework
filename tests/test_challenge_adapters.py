"""Third-party translation and experiment comparability never certify replication."""

from __future__ import annotations

import copy

import pytest

from safe2.challenge.adapters import example_source, import_source, validate_translation
from safe2.challenge.compare import compare_runs
from safe2.challenge.integrity import digest, seal
from safe2.challenge.model import verify_comparison, verify_run
from safe2.challenge.runner import run_challenge
from safe2.contracts import validate_artifact


@pytest.fixture
def source() -> dict:
    return example_source()


def _episode(source: dict, scenario_id: str) -> dict:
    return next(item for item in source["episodes"] if item["scenario_id"] == scenario_id)


def test_example_is_explicitly_synthetic_and_matches_source_contract(source):
    assert source["synthetic"] is True
    assert "synthetic" in source["provider"]["name"]
    assert source["adapter_contract"] == "tenir-example-v1"
    assert validate_artifact("challenge-source", source) == []
    assert all("grade" not in item for item in source["episodes"])
    assert all("verdict" not in item["decision"] for item in source["episodes"])


def test_example_is_deterministic_even_though_native_run_ids_are_not(source):
    assert source == example_source()


def test_import_retains_originals_and_hash_without_mutating_input(source):
    before = copy.deepcopy(source)
    run = import_source(source, adapter="tenir")
    assert source == before
    assert run["provenance"]["source_sha256"] == digest(source)
    assert run["provenance"]["source_hash_basis"] == "canonical_json"
    assert run["provenance"]["source_run_id"] == source["run_id"]
    for normalized, original in zip(run["episodes"], source["episodes"], strict=True):
        assert normalized["source_record"] == original
        assert normalized["source_record"] is not original
        validate_translation(normalized, "tenir", "1.0")
    assert verify_run(run)["valid"]
    assert run["claims"]["independent_replication"] == "not_established"
    assert run["claims"]["aism_maturity"] == "not_assessed"


def test_original_byte_hash_has_explicit_basis(source):
    run = import_source(source, "tenir", source_sha256="a" * 64)
    assert run["provenance"]["source_sha256"] == "a" * 64
    assert run["provenance"]["source_hash_basis"] == "original_bytes"


@pytest.mark.parametrize("bad_hash", ["invalid", "A" * 64, "a" * 63, 42])
def test_rejects_invalid_source_hash(source, bad_hash):
    with pytest.raises(ValueError, match="SHA-256"):
        import_source(source, "tenir", source_sha256=bad_hash)


@pytest.mark.parametrize(
    ("raw", "mode", "expected"),
    [
        ("ALLOW", "enforce", "allow"),
        ("PASS", "enforce", "allow"),
        ("HARD_VETO", "enforce", "deny"),
        ("BLOCK", "enforce", "deny"),
        ("CONSTRAINED", "enforce", "constrained"),
        ("HOLD", "enforce", "hold"),
        ("FLAG", "enforce", "unknown"),
        ("unrecognized verdict", "enforce", "unknown"),
        ("ALLOW_WITH_ALERT", "enforce", "allow"),
        ("ALLOW_WITH_INTENDED_BLOCK", "shadow", "deny"),
        ("ALLOW_WITH_INTENDED_BLOCK", "enforce", "unknown"),
    ],
)
def test_tenir_translation_keeps_ambiguity_visible(source, raw, mode, expected):
    episode = _episode(source, "unauthorized-write")
    episode["decision"]["raw"] = raw
    episode["decision"]["mode"] = mode
    imported = _episode(import_source(source, "tenir"), "unauthorized-write")
    assert imported["decision"]["raw"] == raw
    assert imported["decision"]["mode"] == mode
    assert imported["decision"]["verdict"] == expected
    if expected == "unknown":
        assert imported["grade"]["status"] == "incomplete"


def test_shadow_intended_block_does_not_hide_unauthorized_execution(source):
    episode = _episode(source, "unauthorized-write")
    episode["decision"]["raw"] = "ALLOW_WITH_INTENDED_BLOCK"
    episode["decision"]["mode"] = "shadow"
    episode["observation"]["after"]["protected"] = episode["action"]["value"]
    imported = _episode(import_source(source, "tenir"), "unauthorized-write")
    assert imported["decision"]["verdict"] == "deny"
    assert imported["grade"]["unauthorized_change"] is True
    assert imported["grade"]["decision_state_conflict"] is False


def test_constrained_verdict_requires_evidence_of_applied_constraints(source):
    episode = _episode(source, "legitimate-write")
    episode["decision"].update({"raw": "CONSTRAINED", "constraints_applied": None})
    imported = _episode(import_source(source, "tenir"), "legitimate-write")
    assert imported["decision"]["verdict"] == "constrained"
    assert imported["grade"]["status"] == "conflict"
    episode["decision"].update({
        "constraints_applied": True,
        "constraints": [{"operation": "write", "target": "shared"}],
    })
    constrained = _episode(import_source(source, "tenir"), "legitimate-write")
    assert constrained["grade"]["status"] == "valid"


def test_generic_contract_does_not_borrow_tenir_semantics(source):
    source["adapter_contract"] = "generic-v1"
    generic = import_source(source)
    assert _episode(generic, "unauthorized-write")["decision"]["verdict"] == "unknown"
    _episode(source, "unauthorized-write")["decision"]["raw"] = "deny"
    assert _episode(import_source(source), "unauthorized-write")["decision"]["verdict"] == "deny"


def test_adapter_contract_mismatch_is_rejected(source):
    with pytest.raises(ValueError, match="contract does not match"):
        import_source(source, "generic")
    with pytest.raises(ValueError, match="Unknown challenge adapter"):
        import_source(source, "live-provider")


def test_nonfinite_and_producer_grade_are_rejected(source):
    source["episodes"][0]["metrics"]["elapsed_ms"] = float("nan")
    with pytest.raises(ValueError):
        import_source(source, "tenir")
    source["episodes"][0]["metrics"]["elapsed_ms"] = None
    source["episodes"][0]["grade"] = {"unauthorized_change": False}
    with pytest.raises(ValueError, match="contract"):
        import_source(source, "tenir")


def test_missing_observation_does_not_become_a_passing_result(source):
    _episode(source, "unauthorized-write")["observation"] = {
        "status": "missing", "before": None, "after": None,
    }
    imported = _episode(import_source(source, "tenir"), "unauthorized-write")
    assert imported["grade"]["status"] == "incomplete"
    assert imported["grade"]["unauthorized_change"] is None


def test_external_import_remains_unverified_regardless_of_provider_name(source):
    source["synthetic"] = False
    source["producer_id"] = "an-independent-operator-claim"
    run = import_source(source, "tenir")
    assert run["provenance"]["kind"] == "external_import"
    assert run["claims"]["challenge_maturity"] == "unverified"
    assert run["claims"]["independent_replication"] == "not_established"
    assert run["claims"]["framework_profile_conformance"] == "not_assessed"


@pytest.mark.parametrize("field", ["action", "observation", "decision"])
def test_translation_recheck_rejects_modified_normalized_fields(source, field):
    run = import_source(source, "tenir")
    episode = run["episodes"][0]
    if field == "action":
        episode["action"]["value"] = "forged-value"
    elif field == "observation":
        episode["observation"]["after"]["shared"] = "forged-state"
    else:
        episode["decision"]["verdict"] = "unknown"
    with pytest.raises(ValueError, match="does not reproduce"):
        validate_translation(episode, "tenir", "1.0")


def test_translation_recheck_rejects_unknown_version_and_missing_original(source):
    episode = import_source(source, "tenir")["episodes"][0]
    with pytest.raises(ValueError, match="Unsupported"):
        validate_translation(episode, "tenir", "future-version")
    episode.pop("source_record")
    with pytest.raises(ValueError, match="missing"):
        validate_translation(episode, "tenir", "1.0")


def test_matching_synthetic_results_are_not_independent_replication(source):
    native = run_challenge(treatments=["safe2-reference"])
    imported = import_source(source, "tenir")
    result = compare_runs(native, imported)
    assert result["comparable"] is True
    assert result["outcome_agreement"] == {
        "evaluated_pairs": 6, "agreements": 6, "disagreements": 0,
        "incomplete_pairs": 0, "conflict_pairs": 0, "rate": 1.0,
    }
    assert result["independent_replication"] == "not_established"
    assert any("synthetic fixture" in item for item in result["limitations"])
    assert validate_artifact("challenge-comparison", result) == []
    assert verify_comparison(result, native, imported)["valid"]


def test_different_seeds_refuse_pooling():
    result = compare_runs(run_challenge(seed=0), run_challenge(seed=1))
    assert result["comparable"] is False
    assert "experiment.seed" in result["mismatches"]
    assert result["outcome_agreement"] is None


def test_different_case_coverage_refuses_pooling(source):
    source["episodes"].pop()
    result = compare_runs(run_challenge(treatments=["safe2-reference"]), import_source(source, "tenir"))
    assert result["comparable"] is False
    assert "episode_coverage" in result["mismatches"]
    assert result["outcome_agreement"] is None


def test_action_mismatch_is_not_hidden_by_matching_experiment_labels(source):
    _episode(source, "unauthorized-write")["action"]["value"] = "a-different-write"
    result = compare_runs(run_challenge(treatments=["safe2-reference"]), import_source(source, "tenir"))
    assert result["comparable"] is False
    assert "episode_actions" in result["mismatches"]


def test_unknown_pairs_are_visible_and_not_in_agreement_denominator(source):
    _episode(source, "unauthorized-write")["decision"]["raw"] = "FLAG"
    result = compare_runs(run_challenge(treatments=["safe2-reference"]), import_source(source, "tenir"))
    assert result["outcome_agreement"]["incomplete_pairs"] == 1
    assert result["outcome_agreement"]["evaluated_pairs"] == 5


def test_decision_state_conflicts_are_visible_alongside_known_outcomes(source):
    _episode(source, "legitimate-write")["decision"]["raw"] = "HARD_VETO"
    result = compare_runs(run_challenge(treatments=["safe2-reference"]), import_source(source, "tenir"))
    assert result["outcome_agreement"]["agreements"] == 6
    assert result["outcome_agreement"]["conflict_pairs"] == 1


def test_outcome_disagreements_regrade_observed_state_not_provider_labels(source):
    episode = _episode(source, "unauthorized-write")
    episode["observation"]["after"]["protected"] = episode["action"]["value"]
    result = compare_runs(run_challenge(treatments=["safe2-reference"]), import_source(source, "tenir"))
    assert result["outcome_agreement"]["agreements"] == 5
    assert result["outcome_agreement"]["disagreements"] == 1
    assert result["outcome_agreement"]["conflict_pairs"] == 1


def test_same_source_and_same_artifact_are_explicitly_not_replications(source):
    first = import_source(source, "tenir")
    second = import_source(source, "tenir")
    result = compare_runs(first, second)
    assert any("same source hash" in item for item in result["limitations"])
    assert any("same producer" in item for item in result["limitations"])
    same = compare_runs(first, first)
    assert any("same sealed artifact" in item for item in same["limitations"])


def test_comparison_rejects_tampered_source_artifact(source):
    first = import_source(source, "tenir")
    second = copy.deepcopy(first)
    second["summary"]["episodes"] += 1
    with pytest.raises(ValueError, match="failed verification"):
        compare_runs(first, second)
    with pytest.raises(ValueError, match="failed verification"):
        compare_runs(first, seal(second))


def test_comparison_recheck_detects_resealed_forged_agreement(source):
    native = run_challenge(treatments=["safe2-reference"])
    imported = import_source(source, "tenir")
    result = compare_runs(native, imported)
    result["outcome_agreement"].update({"agreements": 0, "disagreements": 6, "rate": 0.0})
    forged = seal(result)
    assert verify_comparison(forged, native, imported)["valid"] is False
