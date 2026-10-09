"""Guided, consent-first first assessment command."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.configuration import PROFILES
from safe2.onboarding import OnboardingError, create_onboarding_plan, execute_onboarding


@click.command("start")
@click.argument("target", default=".", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--profile", type=click.Choice(PROFILES), default="local", show_default=True)
@click.option("--project-name", default=None, help="Name used only when a configuration is created.")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None)
@click.option("--scan-content", is_flag=True, help="Consent to bounded local project-content reads.")
@click.option("--inspect-config", is_flag=True, help="Inspect redacted configuration structure; requires --scan-content.")
@click.option("--wsl/--no-wsl", default=False, help="Inventory WSL distribution names when available.")
@click.option("--execute", is_flag=True, help="Execute the displayed plan; preview-only by default.")
@click.option("--yes", is_flag=True, help="Confirm an authorized non-interactive execution.")
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
def start(
    target: Path,
    profile: str,
    project_name: str | None,
    output_dir: Path | None,
    scan_content: bool,
    inspect_config: bool,
    wsl: bool,
    execute: bool,
    yes: bool,
    fmt: str,
) -> None:
    """Preview or run a bounded local first assessment with explicit consent."""
    try:
        plan = create_onboarding_plan(
            target,
            profile=profile,
            output_dir=output_dir,
            scan_content=scan_content,
            inspect_config=inspect_config,
            include_wsl=wsl,
        )
    except OnboardingError as exc:
        raise click.ClickException(str(exc)) from exc

    if fmt == "json" and not execute:
        click.echo(json.dumps(plan, indent=2))
    elif fmt == "human":
        click.echo("AI SAFE2 Guided Start Plan")
        click.echo(f"Target: {plan['target']}")
        click.echo(f"Configuration: {plan['configuration']['action']} ({plan['configuration']['profile']})")
        click.echo(f"Read project content: {plan['consent']['read_project_content']}")
        click.echo(f"Content-read source: {plan['consent']['read_project_content_source']}")
        click.echo(f"Inspect redacted config structure: {plan['consent']['inspect_redacted_configuration_structure']}")
        click.echo(f"Network access: {plan['consent']['network_access']}")
        click.echo(f"Evidence output: {plan['output_dir']}")
        click.echo("Stops before: " + "; ".join(plan["stops_before"]))

    if not execute:
        if fmt == "human":
            click.echo("Preview only; no files were written. Rerun with --execute to proceed.")
        return
    if not yes and not click.confirm("Execute this bounded local plan?", default=False):
        raise click.ClickException("execution not confirmed; no assessment was run")
    try:
        completed = execute_onboarding(plan, project_name=project_name)
    except OnboardingError as exc:
        raise click.ClickException(str(exc)) from exc
    if fmt == "json":
        click.echo(json.dumps(completed["result"], indent=2))
    else:
        summary = completed["result"]["assessment_summary"]
        click.echo(f"Completed: {completed['output_dir']}")
        click.echo(f"Disposition: {summary['disposition']} (not a conformance claim)")
        click.echo("Next: open next-step-card.md and assessment/decision-card.md")
