"""Executable baseline-to-policy example for the AI SAFE2 environment workflow."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli


def _run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    project = output / "sample-project"
    project.mkdir(exist_ok=True)
    instruction = project / "AGENTS.md"
    instruction.write_text("# Approved agent policy\n", encoding="utf-8")
    baseline = output / "baseline.json"
    current = output / "current-decision.json"
    runner = CliRunner()
    first = runner.invoke(
        cli,
        [
            "doctor", str(project), "--no-wsl", "--assess", "--hash-assets",
            "--output", str(baseline), "--format", "json",
        ],
    )
    if first.exit_code != 0:
        raise RuntimeError(first.output)

    instruction.write_text("# Approved agent policy\nRequire human approval.\n", encoding="utf-8")
    policy = output / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": "safe2.environment-policy.v1",
                "id": "example-zero-drift",
                "allowed_dispositions": ["REVIEW"],
                "require_baseline": True,
                "require_baseline_integrity": True,
                "max_drift_changes": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    decision = runner.invoke(
        cli,
        [
            "doctor", str(project), "--no-wsl", "--assess", "--hash-assets",
            "--baseline", str(baseline), "--policy", str(policy), "--enforce-policy",
            "--output", str(current), "--format", "json", "--card-format", "markdown",
            "--card-output", str(output / "environment-card.md"),
        ],
    )
    if decision.exit_code != 1:
        raise RuntimeError(f"expected policy DENY exit 1, received {decision.exit_code}")
    html = runner.invoke(
        cli,
        [
            "doctor", str(project), "--no-wsl", "--assess", "--hash-assets",
            "--baseline", str(baseline), "--policy", str(policy),
            "--card-format", "html", "--card-output", str(output / "environment-card.html"),
        ],
    )
    if html.exit_code != 0:
        raise RuntimeError(html.output)

    log = output / "friction.jsonl"
    recorded = runner.invoke(
        cli,
        [
            "feedback", "record", "--category", "missing_evidence", "--outcome", "blocked",
            "--severity", "medium", "--summary", "Example evidence prerequisite was absent.",
            "--output", str(log),
        ],
    )
    if recorded.exit_code != 0:
        raise RuntimeError(recorded.output)
    friction_summary = output / "friction-summary.json"
    summarized = runner.invoke(
        cli, ["feedback", "summary", str(log), "--output", str(friction_summary)]
    )
    if summarized.exit_code != 0:
        raise RuntimeError(summarized.output)

    manifest = output / "run-manifest.json"
    bundled = runner.invoke(
        cli,
        [
            "evidence", "manifest", str(current), str(friction_summary),
            "--subject-id", "example-agent-environment", "--output", str(manifest), "--strict",
        ],
    )
    if bundled.exit_code != 0:
        raise RuntimeError(bundled.output)
    decision_json = json.loads(current.read_text(encoding="utf-8"))
    manifest_json = json.loads(manifest.read_text(encoding="utf-8"))
    result = {
        "policy_decision": decision_json["policy_decision"]["disposition"],
        "drift_changes": decision_json["drift"]["changes"],
        "manifest_invalid": manifest_json["summary"]["invalid"],
        "output": str(output),
    }
    if result["policy_decision"] != "DENY" or result["manifest_invalid"] != 0:
        raise RuntimeError(f"unexpected example result: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.output_dir:
        print(json.dumps(_run(args.output_dir.resolve()), indent=2))
        return
    with tempfile.TemporaryDirectory(prefix="safe2-environment-example-") as temporary:
        print(json.dumps(_run(Path(temporary)), indent=2))


if __name__ == "__main__":
    main()
