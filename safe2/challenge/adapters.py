"""Loss-aware, offline translation of provider evidence into Challenge Lab runs.

The TENIR adapter is an illustrative contract, not an upstream integration. It
does not run provider code, validate a provider ledger, or authenticate a source.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from safe2.contracts import validate_artifact

from .integrity import digest
from .model import make_run

ADAPTER_VERSION = "1.0"
ADAPTER_CONTRACTS = {"generic": "generic-v1", "tenir": "tenir-example-v1"}

_GENERIC_VERDICTS = {
    "ALLOW": "allow",
    "DENY": "deny",
    "CONSTRAINED": "constrained",
    "HOLD": "hold",
    "UNKNOWN": "unknown",
}
_TENIR_VERDICTS = {
    "ALLOW": "allow",
    "PASS": "allow",
    "HARD_VETO": "deny",
    "BLOCK": "deny",
    "CONSTRAINED": "constrained",
    "HOLD": "hold",
    "ALLOW_WITH_ALERT": "allow",
}


def _verdict(raw: str, mode: str, adapter: str) -> str:
    label = raw.strip().upper()
    if adapter == "tenir":
        # This label describes an intended block, not an enforced block. Without
        # the corresponding shadow mode even that interpretation is ambiguous.
        if label == "ALLOW_WITH_INTENDED_BLOCK":
            return "deny" if mode == "shadow" else "unknown"
        return _TENIR_VERDICTS.get(label, "unknown")
    return _GENERIC_VERDICTS.get(label, "unknown")


def validate_translation(episode: dict[str, Any], adapter: str, adapter_version: str) -> None:
    """Reproduce an import from retained source, without authenticating that source."""
    if adapter not in ADAPTER_CONTRACTS or adapter_version != ADAPTER_VERSION:
        raise ValueError("Unsupported challenge adapter identity or version.")
    original = episode.get("source_record")
    if not isinstance(original, dict):
        raise ValueError("Imported episode is missing its original source record.")  # noqa: TRY004
    expected = copy.deepcopy(original)
    decision = expected.get("decision")
    if (
        not isinstance(decision, dict)
        or "verdict" in decision
        or not isinstance(decision.get("raw"), str)
        or decision.get("mode") not in {"enforce", "shadow", "unknown"}
    ):
        raise ValueError("Imported episode has an invalid original decision record.")
    decision["verdict"] = _verdict(decision["raw"], decision["mode"], adapter)
    actual = {key: value for key, value in episode.items() if key not in {"grade", "source_record"}}
    if digest(expected) != digest(actual):
        raise ValueError("Normalized episode does not reproduce its retained source record.")


def import_source(
    source: dict[str, Any],
    adapter: str = "generic",
    source_sha256: str | None = None,
) -> dict[str, Any]:
    """Translate a validated source without trusting producer-authored grades.

    ``source_sha256`` may bind the original bytes read by the caller; otherwise
    the hash binds the canonical source JSON. Neither form authenticates it.
    """
    if adapter not in ADAPTER_CONTRACTS:
        raise ValueError("Unknown challenge adapter; choose generic or tenir.")
    if validate_artifact("challenge-source", source):
        raise ValueError("Challenge source does not satisfy its evidence contract.")
    if source["adapter_contract"] != ADAPTER_CONTRACTS[adapter]:
        raise ValueError("Source adapter contract does not match the selected adapter.")
    if source_sha256 is not None and (
        not isinstance(source_sha256, str)
        or re.fullmatch(r"[a-f0-9]{64}", source_sha256) is None
    ):
        raise ValueError("Source SHA-256 must be 64 lowercase hexadecimal characters.")

    # Also rejects nonfinite floats supplied through the Python API, independently
    # of the bounded JSON reader used by the command line.
    canonical_source_hash = digest(source)
    episodes = []
    for original in source["episodes"]:
        episode = copy.deepcopy(original)
        decision = episode["decision"]
        decision["verdict"] = _verdict(decision["raw"], decision["mode"], adapter)
        episode["source_record"] = copy.deepcopy(original)
        episodes.append(episode)

    return make_run(
        episodes=episodes,
        experiment=copy.deepcopy(source["experiment"]),
        provenance={
            "kind": "synthetic_import" if source["synthetic"] else "external_import",
            "producer_id": source["producer_id"],
            "adapter_id": adapter,
            "adapter_version": ADAPTER_VERSION,
            "source_sha256": source_sha256 or canonical_source_hash,
            "source_hash_basis": "original_bytes" if source_sha256 is not None else "canonical_json",
            "source_run_id": source["run_id"],
        },
        provider=copy.deepcopy(source["provider"]),
    )


def example_source() -> dict[str, Any]:
    """Return openly synthetic evidence mirroring the native reference fixture.

    Building against the packaged protocol keeps scenario and grader hashes
    current. This is a translation demonstration, never an independent result.
    """
    from .runner import run_challenge

    run = run_challenge(seed=0, repetitions=1, treatments=["safe2-reference"])
    raw_labels = {"allow": "ALLOW", "deny": "HARD_VETO", "hold": "HOLD"}
    episodes = []
    for native in run["episodes"]:
        episode = copy.deepcopy(native)
        episode.pop("grade", None)
        episode.pop("source_record", None)
        verdict = episode["decision"].pop("verdict")
        episode["decision"]["raw"] = raw_labels.get(verdict, "UNKNOWN")
        episodes.append(episode)
    return {
        "schema_version": "safe2.challenge-source.v1",
        "adapter_contract": "tenir-example-v1",
        "provider": {"name": "TENIR illustrative synthetic example", "version": "example-1"},
        "producer_id": "ai-safe2-synthetic-fixtures",
        "run_id": "tenir-synthetic-reference-fixture-seed-0",
        "synthetic": True,
        "experiment": copy.deepcopy(run["experiment"]),
        "episodes": episodes,
    }
