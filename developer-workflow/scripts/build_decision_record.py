#!/usr/bin/env python3
"""Build a replayable, human-authorized decision-record skeleton."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--route", choices=["standard", "enhanced", "critical"], required=True)
    parser.add_argument("--workflow", type=Path, default=Path(".ai-safe2/workflow.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    required = workflow["routes"][args.route]["required_capabilities"]
    record = {
        "schema_version": "ai-safe2.decision-record.v1",
        "decision_id": f"{args.subject}@{args.revision}",
        "subject": {"identifier": args.subject, "revision": args.revision},
        "route": args.route,
        "outcome": "hold",
        "required_evidence": required,
        "evidence": [],
        "risks": [{"status": "unknown", "reason": "Evidence has not been attached."}],
        "human_authority": {"required": True, "decision_owner": None, "decision_at": None, "rationale": None},
        "replay": {
            "policy_digest": digest(args.workflow),
            "configuration_digest": digest(args.workflow),
            "producer_versions": {"ai-safe2-cli": workflow["minimum_cli_version"]},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

