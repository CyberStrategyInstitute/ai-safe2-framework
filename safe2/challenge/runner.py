"""Bounded in-memory fixtures; never executes an agent, subprocess or network call."""

from __future__ import annotations

from typing import Any

from safe2.challenge.protocol import TREATMENTS, experiment, protocol


def _decision(spec: dict[str, Any], treatment: str) -> dict[str, Any]:
    if treatment == "uncontrolled":
        verdict = "allow"
    elif treatment == "conventional":
        # Simple identity/target ACL, intentionally without action-bound approval.
        verdict = "deny" if spec["principal"] == "outsider" else "allow"
    elif not spec["control_available"]:
        verdict = "hold"
    else:
        # The reference checks the fixture conditions, not the expected grade.
        permitted = spec["principal"] != "outsider"
        approval_ok = not spec["requires_approval"] or spec["approval"] == "valid"
        verdict = "allow" if permitted and approval_ok else "deny"
    return {
        "raw": verdict.upper(),
        "mode": "enforce",
        "verdict": verdict,
        "constraints": [],
        "constraints_applied": None,
    }


def run_challenge(
    challenge_id: str = "001", seed: int = 0, repetitions: int = 1,
    treatments: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Execute six inert cases with explicit positive and negative controls.

    Candidate values encode seed/trial; no sampling, paid APIs or real systems
    are involved. Repetitions verify mechanics, not independent statistical runs.
    """
    if challenge_id != "001":
        raise ValueError("Only the offline Challenge 001 fixture study is available.")
    if type(repetitions) is not int or not 1 <= repetitions <= 100:
        raise ValueError("Repetitions must be an integer between 1 and 100.")
    pinned = experiment(seed)
    if treatments is not None and not isinstance(treatments, (list, tuple)):
        raise ValueError("Treatments must be a list of supported treatment identifiers.")
    selected = list(TREATMENTS if treatments is None else treatments)
    if (
        not selected
        or any(not isinstance(name, str) or name not in TREATMENTS for name in selected)
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Select one or more unique supported treatments.")
    # Stable canonical order avoids meaningless differences from option order.
    selected = [name for name in TREATMENTS if name in selected]
    episodes = []
    for trial in range(repetitions):
        for treatment in selected:
            for spec in protocol()["scenarios"]:
                decision = _decision(spec, treatment)
                value = f"candidate:{seed}:{trial}"
                before = dict(spec["initial_state"])
                after = dict(before)
                if decision["verdict"] == "allow":
                    after[spec["target"]] = value
                episodes.append({
                    "id": f"001:{treatment}:{spec['id']}:{trial}",
                    "scenario_id": spec["id"],
                    "trial": trial,
                    "treatment": treatment,
                    "action": {
                        "principal": spec["principal"], "operation": "write",
                        "target": spec["target"], "value": value,
                    },
                    "decision": decision,
                    "observation": {"status": "observed", "before": before, "after": after},
                    # This offline fixture observes neither real-world cost nor
                    # human approval. Null is more honest than an invented zero.
                    "metrics": {"elapsed_ms": None, "cost_usd": None, "human_interventions": None},
                })
    # Lazy import permits independent protocol/grader use without the CLI model.
    from safe2.challenge.model import make_run

    return make_run(
        episodes=episodes,
        experiment=pinned,
        provider={"name": "AI SAFE2 inert reference fixture", "version": "1.0"},
        provenance={
            "kind": "native_fixture", "producer_id": "ai-safe2-reference-fixture",
            "adapter_id": "native", "adapter_version": "1.0",
            "source_sha256": None, "source_hash_basis": None, "source_run_id": None,
        },
    )
