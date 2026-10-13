#!/usr/bin/env python3
"""Build the required AI SAFE2 CLI decision-routing request for one revision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RISK_TIERS = {"standard": "low", "enhanced": "medium", "critical": "critical"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--route-file", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, default=Path(".ai-safe2/workflow.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    route = json.loads(args.route_file.read_text(encoding="utf-8"))
    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    route_name = route["route"]
    required = workflow["routes"][route_name]["required_capabilities"]
    request = {
        "schema_version": "safe2.decision-request.v1",
        "decision_id": f"{args.subject}:{args.revision}",
        "decision_class": "review_module_selection",
        "data_classification": "internal",
        "structured_state": {
            "subject": args.subject,
            "revision": args.revision,
            "route": route_name,
            "profile": route["profile"],
            "changed_paths": route["paths"],
        },
        "questions": {
            "required_review_modules": {
                "type": "noul",
                "instructions": "Identify unresolved review capabilities without authorizing merge or release.",
            }
        },
        "deterministic": {
            "risk_tier": RISK_TIERS[route_name],
            "required_evidence": required,
            "evidence_status": {capability: "pending" for capability in required},
            "policy_flags": {
                "human_decision_required": True,
                "provider_failure_is_pass": False,
            },
        },
        "external_adjudication_allowed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
