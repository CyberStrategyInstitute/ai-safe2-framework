"""Deterministic Challenge 001 JSON evaluator example; no external side effects."""

from __future__ import annotations

import json
import sys


def main() -> None:
    request = json.load(sys.stdin)
    conditions = request["conditions"]
    allowed = (
        conditions["control_available"]
        and conditions["authorized"]
        and (not conditions["requires_approval"] or conditions["approval"] == "valid")
    )
    before = request["initial_state"]
    after = dict(before)
    if allowed:
        after[request["action"]["target"]] = request["action"]["value"]
    raw = "ALLOW" if allowed else ("HOLD" if not conditions["control_available"] else "DENY")
    json.dump({
        "schema_version": "safe2.challenge-executor-response.v1",
        "decision": {"raw": raw, "mode": "enforce", "constraints": [],
                     "constraints_applied": None},
        "observation": {"status": "observed", "before": before, "after": after},
        "metrics": {"cost_usd": None, "human_interventions": 0},
    }, sys.stdout, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main()
