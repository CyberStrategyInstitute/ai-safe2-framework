"""Unified project assessment command."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.assessment import AssessmentError, run_assessment


@click.command("assess")
@click.argument(
    "target", default=".", type=click.Path(path_type=Path, file_okay=False, exists=True)
)
@click.option("--output-dir", type=click.Path(path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--scan-content",
    is_flag=True,
    help="Consent to bounded local project-content reads for static analysis.",
)
@click.option(
    "--inspect-config",
    is_flag=True,
    help="Emit redacted structural configuration evidence; requires content consent.",
)
@click.option(
    "--wsl/--no-wsl", default=False, help="Inventory WSL distribution names when available."
)
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
def assess_project(
    target: Path,
    output_dir: Path | None,
    config_path: Path | None,
    scan_content: bool,
    inspect_config: bool,
    wsl: bool,
    fmt: str,
) -> None:
    """Create one reviewable environment and project evidence bundle."""
    try:
        result = run_assessment(
            target,
            output_dir=output_dir,
            config_path=config_path,
            scan_content=scan_content,
            inspect_config=inspect_config,
            include_wsl=wsl,
        )
    except (AssessmentError, OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if fmt == "json":
        click.echo(json.dumps(result, indent=2))
        return
    summary = result["assessment"]["summary"]
    click.echo("AI SAFE2 Project Assessment")
    click.echo(f"Disposition: {summary['disposition']}")
    click.echo(f"Evidence confidence: {summary['evidence_confidence']}")
    click.echo(f"Harnesses detected: {summary['harnesses_detected']}")
    click.echo(f"Environment findings: {summary['environment_findings']}")
    click.echo(
        f"Static violations: {summary['static_violations'] if summary['static_violations'] is not None else 'NOT ASSESSED'}"
    )
    click.echo(f"Evidence bundle: {result['output_dir']}")
