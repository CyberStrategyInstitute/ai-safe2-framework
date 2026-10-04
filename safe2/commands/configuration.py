"""Project initialization and configuration inspection commands."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.configuration import (
    PROFILES,
    ConfigurationError,
    initialize_project,
    read_configuration,
    resolve_configuration,
)


@click.command("init")
@click.argument("path", default=".", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--profile", type=click.Choice(PROFILES), default="local", show_default=True)
@click.option("--project-name", default=None, help="Optional human-readable project name.")
def init_project(path: Path, profile: str, project_name: str | None) -> None:
    """Create a secure-default .safe2/config.toml without overwriting files."""
    try:
        target = initialize_project(path, profile=profile, project_name=project_name)
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Created {target}")
    click.echo("Privacy defaults: no prompts, content, environment values, or network export.")


@click.group("config")
def config() -> None:
    """Inspect and validate the effective project configuration."""


@config.command("show")
@click.option("--config", "config_path", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--start", type=click.Path(path_type=Path, exists=True), default=".")
def show_configuration(config_path: Path | None, start: Path) -> None:
    """Show normalized configuration and the selected precedence source."""
    try:
        data, source = resolve_configuration(explicit=config_path, start=start)
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps({"source": source, "configuration": data}, indent=2, sort_keys=True))


@config.command("validate")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
def validate_config(source: Path) -> None:
    """Validate a bounded safe2.config.v1 TOML document."""
    try:
        data = read_configuration(source)
    except ConfigurationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps({"valid": True, "schema_version": data["schema_version"]}, indent=2))
