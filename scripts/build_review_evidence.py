#!/usr/bin/env python3
"""Create bounded PR/release evidence from Git metadata and AI SAFE2 output."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _run(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
    )
    return result.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _matches(path: str, pattern: str) -> bool:
    # PurePath.match treats ** differently at the repository root; fnmatch gives
    # the policy author one predictable, slash-normalized vocabulary.
    return fnmatch.fnmatchcase(path.replace("\\", "/"), pattern)


def classify(paths: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    for rule in policy["rules"]:
        affected = sorted({path for path in paths for pattern in rule["patterns"] if _matches(path, pattern)})
        if affected:
            matched.append({
                "rule_id": rule["id"], "tier": rule["tier"], "reason": rule["reason"],
                "paths": affected, "required_evidence": rule["required_evidence"],
                "review_lenses": rule["review_lenses"],
            })
    tier = max((row["tier"] for row in matched), key=RANK.get, default=policy["default_tier"])
    required = sorted({item for row in matched for item in row["required_evidence"]})
    lenses = sorted({item for row in matched for item in row["review_lenses"]})
    recommend = tier in policy["greptile"]["recommend_for"]
    return {
        "tier": tier, "matched_rules": matched, "required_evidence": required,
        "review_lenses": lenses,
        "greptile": {"recommended": recommend, "blocking": False,
                     "reason": "Strategic review recommended for this risk tier." if recommend
                     else "Routine PR-Agent and deterministic gates are proportionate to this tier."},
    }


def _diff(root: Path, base: str, head: str) -> tuple[list[str], dict[str, int]]:
    paths = [line for line in _run(root, "diff", "--name-only", f"{base}...{head}").splitlines() if line]
    stats = {"files": len(paths), "additions": 0, "deletions": 0, "binary_files": 0}
    for line in _run(root, "diff", "--numstat", f"{base}...{head}").splitlines():
        added, deleted, *_ = line.split("\t", 2)
        if added == "-" or deleted == "-":
            stats["binary_files"] += 1
        else:
            stats["additions"] += int(added)
            stats["deletions"] += int(deleted)
    return sorted(paths), stats


def _checks(values: list[str]) -> list[dict[str, str]]:
    rows = []
    for value in values:
        parts = value.split("=", 2)
        if len(parts) != 3 or parts[1] not in {"passed", "failed", "pending", "cancelled", "unavailable"}:
            raise ValueError("--check must be NAME=STATUS=EVIDENCE_REF")
        rows.append({"name": parts[0], "status": parts[1], "evidence_ref": parts[2]})
    return rows


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    policy = _read_json(args.policy)
    paths, stats = _diff(root, args.base, args.head)
    risk = classify(paths, policy)
    checks = _checks(args.check)
    safe2 = _read_json(args.safe2_evidence) if args.safe2_evidence else None
    supplied_names = {row["name"] for row in checks}
    missing_required = sorted(set(risk["required_evidence"]) - supplied_names)
    failed = [row["name"] for row in checks if row["status"] in {"failed", "cancelled"}]
    incomplete = [row["name"] for row in checks if row["status"] in {"pending", "unavailable"}]
    status = "hold" if failed else "review" if incomplete or not checks or missing_required else "ready_for_human_decision"
    reasons = (["Deterministic checks failed or were cancelled: " + ", ".join(failed)] if failed else [])
    gaps = (["Checks are pending or unavailable: " + ", ".join(incomplete)] if incomplete else [])
    if not checks:
        gaps.append("No check outcomes were supplied to this evidence run.")
    if missing_required:
        gaps.append("Risk policy evidence is not represented in supplied outcomes: " + ", ".join(missing_required))
    if safe2 is None:
        gaps.append("No AI SAFE2 0.9.0 environment evidence was supplied.")
    history = {
        "comparison_available": False,
        "introduced": None, "changed": None, "resolved": None, "inherited": None,
        "reason": "No comparable prior structured finding set was supplied; Git diff is not finding attribution."
    }
    created = datetime.now(UTC).isoformat()
    return {
        "schema_version": "ai-safe2.review-evidence.v1",
        "created_at": created,
        "policy": {"id": policy["policy_id"], "sha256": hashlib.sha256(args.policy.read_bytes()).hexdigest()},
        "subject": {
            "repository": args.repository or _run(root, "config", "--get", "remote.origin.url"),
            "base_revision": _run(root, "rev-parse", args.base),
            "head_revision": _run(root, "rev-parse", args.head),
            "pull_request": args.pull_request,
        },
        "change": {"paths": paths, "summary": stats},
        "risk": risk,
        "checks": checks,
        "ai_safe2": {
            "cli_version": args.safe2_version,
            "evidence_supplied": safe2 is not None,
            "environment_evidence": safe2,
            "claim_boundary": "Inventory and drift evidence; not proof of safety or AI SAFE2 conformance.",
        },
        "finding_history": history,
        "decision": {
            "status": status, "reasons": reasons, "gaps": gaps,
            "owner": policy["decision_owner"], "release_authorized": False,
            "merge_authorized": False, "conformance_claim": False,
        },
        "retention": {"artifact_days": policy["retention_days"], "longitudinal_key": "head_revision"},
    }


def render(value: dict[str, Any]) -> str:
    risk, decision, change = value["risk"], value["decision"], value["change"]["summary"]
    lines = [
        "# Review Decision Evidence", "",
        f"**Decision support:** `{decision['status']}` · **Risk:** `{risk['tier']}`",
        f"**Revision:** `{value['subject']['head_revision']}` against `{value['subject']['base_revision']}`", "",
        "This report supports the named human decision; it does not authorize merge or release.", "",
        "## What changed", "",
        f"- {change['files']} files; +{change['additions']} / -{change['deletions']}; {change['binary_files']} binary files.",
    ]
    for row in risk["matched_rules"]:
        lines.append(f"- **{row['tier']} · {row['rule_id']}:** {row['reason']}")
    lines += ["", "## Required reviewer evidence", ""]
    lines.extend(f"- `{item}`" for item in risk["required_evidence"] or ["proportionate tests and human review"])
    lines += ["", "## Specialist review lenses", ""]
    lines.extend(f"- `{item}`" for item in risk["review_lenses"] or ["correctness", "regression risk"])
    lines += ["", "## Deterministic checks", ""]
    if value["checks"]:
        lines += ["| Check | Status | Evidence |", "| --- | --- | --- |"]
        lines.extend(f"| {r['name']} | `{r['status']}` | {r['evidence_ref']} |" for r in value["checks"])
    else:
        lines.append("No outcomes supplied; this is an evidence gap, not a pass.")
    lines += ["", "## Before / after finding attribution", "", value["finding_history"]["reason"], "",
              "## Strategic review", "", f"- Greptile recommended: `{str(risk['greptile']['recommended']).lower()}`",
              f"- Blocking: `false`", f"- Rationale: {risk['greptile']['reason']}", "", "## Decision gaps", ""]
    lines.extend(f"- {item}" for item in decision["gaps"] or ["No gap was identified in the supplied evidence."])
    lines += ["", "## Evidence boundary", "",
              "Hashes bind this report to inputs and revisions; they do not prove that claims are true. Advisory AI review remains separate from deterministic gates. Human maintainers retain merge, release, and risk-acceptance authority.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--pull-request")
    parser.add_argument("--safe2-evidence", type=Path)
    parser.add_argument("--safe2-version", default="0.9.0")
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    if args.json_output.exists() or args.markdown_output.exists():
        raise SystemExit("outputs must be new files")
    result = build(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render(result), encoding="utf-8")
    print(json.dumps({"status": result["decision"]["status"], "risk": result["risk"]["tier"],
                      "greptile_recommended": result["risk"]["greptile"]["recommended"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
