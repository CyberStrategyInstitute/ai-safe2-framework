"""Evaluate bounded semantic decisions without granting model authority."""

from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path

import click

from safe2.decision.audit import append_event
from safe2.decision.gateway import DecisionGateway
from safe2.decision.providers import SystemOneProvider


def _load(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size > 5_000_000:
        raise click.ClickException("input must be a non-link JSON file no larger than 5 MB")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise click.ClickException("input must contain a JSON object")
    return value


def _policy(path: Path | None) -> dict:
    if path:
        return _load(path)
    return json.loads(
        files("safe2.data").joinpath("decision-routing-policy-v1.json").read_text(encoding="utf-8")
    )


@click.group()
def decision():
    """Create replayable advisory review-routing decisions."""


@decision.command("evaluate")
@click.argument("request", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--policy", "policy_path", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--ledger", type=click.Path(path_type=Path))
@click.option(
    "--kev-url",
    envvar="SAFE2_KEV_URL",
    help="Explicit local Kev base URL; omitted means deterministic-only.",
)
@click.option("--kev-model", default="kev-4b", show_default=True)
@click.option(
    "--jev-url",
    envvar="SAFE2_JEV_URL",
    help="Explicit external Jev base URL; used only when policy permits.",
)
@click.option("--jev-model", default="jev-latest", show_default=True)
def evaluate(
    request: Path,
    policy_path: Path | None,
    output: Path,
    ledger: Path | None,
    kev_url: str | None,
    kev_model: str,
    jev_url: str | None,
    jev_model: str,
) -> None:
    """Evaluate one strict decision request in deterministic or shadow mode."""
    if output.exists() or output.is_symlink():
        raise click.ClickException("output must be a new, non-link path")
    policy = _policy(policy_path)
    primary = (
        SystemOneProvider(
            "kev_local",
            kev_url,
            kev_model,
            os.getenv("SAFE2_KEV_API_KEY"),
            policy["primary"]["timeout_seconds"],
        )
        if kev_url
        else None
    )
    secondary = (
        SystemOneProvider(
            name="jev_external",
            endpoint=jev_url,
            model=jev_model,
            api_key=os.getenv("TYPESAFE_API_KEY"),
            timeout_seconds=policy["secondary"]["timeout_seconds"],
            require_https=True,
        )
        if jev_url
        else None
    )
    try:
        result = DecisionGateway(policy, primary, secondary).evaluate(_load(request))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        chain = append_event(ledger, result) if ledger else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise click.ClickException(f"decision evaluation failed: {type(exc).__name__}") from exc
    click.echo(
        json.dumps(
            {
                "output": str(output),
                "route": result["route"]["outcome"],
                "risk_tier": result["review_plan"]["risk_tier"],
                "human_approval_required": result["review_plan"]["human_approval_required"],
                "ledger_event_sha256": chain,
                "merge_authorized": False,
            }
        )
    )


@decision.command("replay")
@click.argument("corpus", type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option(
    "--policy", "policy_path", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
def replay(corpus: Path, policy_path: Path | None, output: Path) -> None:
    """Replay labeled JSON cases through deterministic routing and report regressions."""
    if output.exists() or output.is_symlink():
        raise click.ClickException("output must be a new, non-link path")
    cases = sorted(corpus.glob("*.json"))
    if not cases or len(cases) > 1000:
        raise click.ClickException("corpus must contain between 1 and 1000 JSON cases")
    gateway = DecisionGateway(_policy(policy_path))
    rows = []
    for path in cases:
        value = _load(path)
        expected = value.pop("expected")
        result = gateway.evaluate(value)
        observed = result["review_plan"]
        passed = all(observed.get(key) == expected[key] for key in expected)
        rows.append(
            {
                "case": path.name,
                "passed": passed,
                "expected": expected,
                "observed": {key: observed.get(key) for key in expected},
            }
        )
    report = {
        "schema_version": "safe2.decision-replay.v1",
        "total": len(rows),
        "passed": sum(row["passed"] for row in rows),
        "failed": sum(not row["passed"] for row in rows),
        "cases": rows,
        "model_evaluated": False,
        "calibration_claim": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    click.echo(
        json.dumps({"output": str(output), "total": report["total"], "failed": report["failed"]})
    )
    if report["failed"]:
        raise click.exceptions.Exit(1)
