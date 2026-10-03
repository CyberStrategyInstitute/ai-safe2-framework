"""Installed-runtime verification command."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.challenge.io import safe_path, write_json
from safe2.installation import inspect_installation


@click.command("self-check")
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human", show_default=True)
@click.option("--output", type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Return the verdict exit code after writing output.")
def self_check(fmt: str, output: Path | None, strict: bool) -> None:
    """Verify this installed CLI, runtime, dependencies, and contract catalog."""
    try:
        result = inspect_installation()
        if output is not None:
            destination = safe_path(output)
            if destination.exists():
                raise ValueError("Output must be new")
            write_json(destination, result)
    except (OSError, TypeError, ValueError) as exc:
        raise click.ClickException("Installation self-check could not complete safely") from exc
    if fmt == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo("AI SAFE2 Installation Check")
        click.echo(f"Verdict: {result['verdict'].upper()}")
        click.echo(f"CLI: {result['cli_version']}")
        click.echo(f"Python: {result['python']['version']} ({result['python']['support']})")
        click.echo(
            f"Contracts: {result['contracts']['loaded']}/{result['contracts']['declared']} loaded"
        )
        click.echo(f"Missing dependencies: {len(result['dependencies']['missing'])}")
        click.echo(f"Console entry point: {result['console_entrypoint']}")
        if output is not None:
            click.echo(f"Evidence: {output}")
    if strict:
        raise SystemExit(result["exit_code"])
