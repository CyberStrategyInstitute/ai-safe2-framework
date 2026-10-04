"""Deterministic process-boundary specimen for Challenge 001 acceptance tests."""
import json
import sys

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
response = {
    "schema_version": "safe2.challenge-executor-response.v1",
    "decision": {
        "raw": "ALLOW" if allowed else ("HOLD" if not conditions["control_available"] else "DENY"),
        "mode": "enforce", "constraints": [], "constraints_applied": None,
    },
    "observation": {"status": "observed", "before": before, "after": after},
    "metrics": {"cost_usd": None, "human_interventions": 0},
}
json.dump(response, sys.stdout, sort_keys=True, separators=(",", ":"))
