"""Discover and export versioned machine-readable evidence contracts."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.contracts import SCHEMAS, schema_text, validate_artifact


@click.group("schema")
def schema() -> None:
    """List or export stable JSON Schemas for agent integration."""


@schema.command("list")
def list_schemas() -> None:
    """Print available schema identifiers as JSON."""
    click.echo(json.dumps({"schema_version": "safe2.schema-catalog.v1", "schemas": sorted(SCHEMAS)}, indent=2))


@schema.command("export")
@click.argument("name", type=click.Choice(sorted(SCHEMAS)))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
def export_schema(name: str, output: Path | None) -> None:
    """Export one schema to stdout or a file."""
    content = schema_text(name)
    if output is None:
        click.echo(content, nl=False)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    click.echo(f"Schema written: {output}")


@schema.command("validate")
@click.argument("name", type=click.Choice(sorted(SCHEMAS)))
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False, exists=True))
@click.option("--max-bytes", default=20_000_000, type=click.IntRange(1, 100_000_000), show_default=True)
@click.pass_context
def validate_schema(ctx: click.Context, name: str, source: Path, max_bytes: int) -> None:
    """Validate a JSON artifact; exit 0 valid, 1 contract failure, 2 input failure."""
    if source.is_symlink():
        click.echo(json.dumps({"schema": name, "valid": False, "error": "symbolic_link_rejected"}))
        ctx.exit(2)
    try:
        if source.stat().st_size > max_bytes:
            raise ValueError("input_size_limit_exceeded")
        artifact = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        error = "input_size_limit_exceeded" if str(exc) == "input_size_limit_exceeded" else type(exc).__name__
        click.echo(json.dumps({"schema": name, "valid": False, "error": error}))
        ctx.exit(2)

    violations = validate_artifact(name, artifact)
    result = {
        "schema_version": "safe2.schema-validation.v1",
        "schema": name,
        "valid": not violations,
        "error_count": len(violations),
        "errors": [
            {
                "instance_path": error["instance_path"],
                "validator": error["validator"],
                "schema_path": error["schema_path"],
            }
            for error in violations[:50]
        ],
        "errors_truncated": len(violations) > 50,
        "privacy": {"instance_values_emitted": False, "validator_messages_emitted": False},
    }
    click.echo(json.dumps(result, indent=2))
    if violations:
        ctx.exit(1)
