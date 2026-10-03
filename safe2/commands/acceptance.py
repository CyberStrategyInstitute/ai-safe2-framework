"""First-time evaluator acceptance workflow."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.acceptance import create_bundle, verify_bundle


@click.group("acceptance")
def acceptance() -> None:
    """Run and replay an offline stranger acceptance bundle."""


@acceptance.command("run")
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Return the bundle status exit code.")
def run_acceptance(output_dir: Path, strict: bool) -> None:
    """Create a new offline installation and static-control acceptance bundle."""
    try:
        report = create_bundle(output_dir)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Acceptance run failed; inspect any retained .incomplete directory before retrying"
        ) from exc
    click.echo(json.dumps({
        "output_dir": str(output_dir),
        "status": report["status"],
        "independent_review_claim": False,
        "conformance_claim": False,
    }))
    if strict:
        raise SystemExit(report["exit_code"])


@acceptance.command("verify")
@click.argument("bundle", type=click.Path(path_type=Path, exists=True, file_okay=False))
def verify_acceptance(bundle: Path) -> None:
    """Replay fixture decisions and verify an existing bundle's byte integrity."""
    try:
        result = verify_bundle(bundle)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Acceptance bundle could not be verified safely") from exc
    click.echo(json.dumps(result, indent=2))
    if not result["valid"]:
        raise SystemExit(1)
