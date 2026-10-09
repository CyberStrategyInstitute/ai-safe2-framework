#!/usr/bin/env python3
"""Evaluate evidence completeness without making the human decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(record: dict) -> dict:
    revision = record["subject"]["revision"]
    produced = {
        item["capability"]
        for item in record["evidence"]
        if item["status"] == "produced" and item["subject_revision"] == revision
    }
    missing = sorted(set(record["required_evidence"]) - produced)
    result = dict(record)
    result["outcome"] = "hold" if missing else "ready_for_human_decision"
    result["risks"] = (
        [{"status": "unknown", "reason": f"Missing produced evidence: {capability}"} for capability in missing]
        if missing
        else []
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    if record["outcome"] in {"approved", "rejected"}:
        raise SystemExit("Refusing to overwrite a completed human decision.")
    result = evaluate(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": result["outcome"], "merge_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
