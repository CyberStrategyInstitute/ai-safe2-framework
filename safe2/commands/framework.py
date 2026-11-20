"""Query v3.5 requirements and inspect attributed mapping/readiness records."""
from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.framework import audit_registry, data, query, readiness
from safe2.secure_io import read_regular_bounded


def read_object(path: Path) -> dict:
    try:
        value = json.loads(read_regular_bounded(path, limit=5_000_000).decode('utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        raise click.ClickException(type(exc).__name__) from exc
    if not isinstance(value, dict):
        raise click.ClickException('Input must be a JSON object')
    return value


@click.group()
def framework() -> None:
    """Inspect v3.5 controls, Rosetta Stone records and scoped readiness evidence."""


@framework.command('query')
@click.option('--control', 'control_id')
@click.option('--source', 'source_id')
def query_command(control_id: str | None, source_id: str | None) -> None:
    try:
        result = query(control_id, source_id)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, indent=2))


@framework.command('audit')
@click.argument('source', type=click.Path(path_type=Path, exists=True, dir_okay=False), required=False)
@click.option('--strict', is_flag=True, help='Fail when any mapping rule is unassessed or distribution evidence is absent.')
@click.pass_context
def audit_command(ctx: click.Context, source: Path | None, strict: bool) -> None:
    try:
        result = audit_registry(read_object(source) if source else data('rosetta-v3.5.json'))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, indent=2))
    failed = result['errors'] or any(c['status'] == 'fail' for c in result['checks'].values())
    if failed or strict and any(c['status'] != 'pass' for c in result['checks'].values()):
        ctx.exit(1)


@framework.command('readiness')
@click.argument('source', type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.pass_context
def readiness_command(ctx: click.Context, source: Path) -> None:
    try:
        result = readiness(read_object(source))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, indent=2))
    if result['result'] == 'hold':
        ctx.exit(1)
