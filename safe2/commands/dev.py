"""Plan and verify risk-adjusted development work."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import click

from safe2.challenge.io import read_json, write_json
from safe2.development.workflow import create_plan, create_receipt, verify_development_artifact


def _policy(path: Path | None) -> dict[str, Any]:
    if path is not None:
        return read_json(path)
    repository_policy = Path(".ai-safe2/development-policy.json")
    if repository_policy.is_file() and not repository_policy.is_symlink():
        return read_json(repository_policy)
    return json.loads(
        files("safe2.data").joinpath("development-policy-v1.json").read_text(encoding="utf-8")
    )


def _risk_policy(path: Path | None) -> dict[str, Any] | None:
    if path is not None:
        return read_json(path)
    repository_policy = Path(".ai-safe2/review-policy.json")
    if repository_policy.is_file() and not repository_policy.is_symlink():
        return read_json(repository_policy)
    return None


@click.group()
def dev() -> None:
    """Create replayable development plans and evidence receipts."""


@dev.command("plan")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--policy", "policy_path", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--review-policy",
    "risk_policy_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Repository path-risk policy; defaults to .ai-safe2/review-policy.json when present.",
)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.pass_context
def plan_command(
    ctx: click.Context,
    source: Path,
    policy_path: Path | None,
    risk_policy_path: Path | None,
    output: Path,
) -> None:
    """Derive risk-adjusted requirements. Exit 0 means ready to implement."""
    try:
        result = create_plan(
            read_json(source), _policy(policy_path), _risk_policy(risk_policy_path)
        )
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Development plan could not be produced: invalid input, policy, or output"
        ) from exc
    click.echo(
        json.dumps(
            {
                "output": str(output),
                "disposition": result["disposition"],
                "risk_tier": result["task"]["risk_tier"],
                "declared_risk_tier": result["task"]["declared_risk_tier"],
                "risk_raised": result["risk_classification"]["risk_raised"],
                "delivery_shape": result["task"]["delivery_shape"],
                "gap_count": len(result["gaps"]),
                "authorization_granted": False,
            }
        )
    )
    if result["disposition"] != "ready":
        ctx.exit(1)


@dev.command("receipt")
@click.argument("plan", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--artifact-root",
    required=True,
    type=click.Path(path_type=Path, exists=True, file_okay=False),
)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.pass_context
def receipt_command(
    ctx: click.Context, plan: Path, source: Path, artifact_root: Path, output: Path
) -> None:
    """Check plan-bound evidence. Exit 0 means internally supported, not approved."""
    try:
        result = create_receipt(read_json(plan), read_json(source), artifact_root)
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Development receipt could not be produced: invalid plan, evidence, or output"
        ) from exc
    click.echo(
        json.dumps(
            {
                "output": str(output),
                "claim_status": result["claim_status"],
                "revision": result["revision"],
                "authorization_granted": False,
            }
        )
    )
    if result["claim_status"] != "supported":
        ctx.exit(1)


@dev.command("verify")
@click.argument("artifact", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.pass_context
def verify_command(ctx: click.Context, artifact: Path) -> None:
    """Verify structure and integrity only; workflow state remains separate."""
    try:
        result = verify_development_artifact(read_json(artifact))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Development artifact could not be verified") from exc
    click.echo(json.dumps(result, allow_nan=False))
    if not result["valid"]:
        ctx.exit(1)


@dev.command("replay")
@click.argument("corpus", type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option(
    "--policy", "policy_path", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--review-policy",
    "risk_policy_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Repository path-risk policy; defaults to .ai-safe2/review-policy.json when present.",
)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.pass_context
def replay_command(
    ctx: click.Context,
    corpus: Path,
    policy_path: Path | None,
    risk_policy_path: Path | None,
    output: Path,
) -> None:
    """Replay deterministic methodology cases; this is not a live-model evaluation."""
    try:
        cases = sorted(corpus.glob("*.json"))
        if not cases or len(cases) > 1000:
            raise ValueError("corpus must contain between 1 and 1000 JSON files")
        selected_policy = _policy(policy_path)
        selected_risk_policy = _risk_policy(risk_policy_path)
        rows = []
        for path in cases:
            case = read_json(path)
            source = case.get("source")
            expected = case.get("expected")
            if not isinstance(source, dict) or not isinstance(expected, dict):
                raise TypeError("each replay case needs source and expected objects")
            plan = create_plan(source, selected_policy, selected_risk_policy)
            observed = {
                "disposition": plan["disposition"],
                "gap_codes": sorted(item["code"] for item in plan["gaps"]),
                "human_design_approval": plan["requirements"]["human_design_approval"],
                "threat_model": plan["requirements"]["threat_model"],
                "greptile_recommended": plan["requirements"]["greptile_recommended"],
            }
            passed = all(observed.get(key) == value for key, value in expected.items())
            rows.append(
                {
                    "case": path.name,
                    "passed": passed,
                    "expected": expected,
                    "observed": {key: observed.get(key) for key in expected},
                }
            )
        report = {
            "schema_version": "safe2.development-replay.v1",
            "total": len(rows),
            "passed": sum(item["passed"] for item in rows),
            "failed": sum(not item["passed"] for item in rows),
            "cases": rows,
            "model_evaluated": False,
            "authorization_granted": False,
        }
        write_json(output, report)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Development replay could not be completed: invalid corpus, policy, or output"
        ) from exc
    click.echo(json.dumps({"output": str(output), "total": report["total"], "failed": report["failed"]}))
    if report["failed"]:
        ctx.exit(1)
