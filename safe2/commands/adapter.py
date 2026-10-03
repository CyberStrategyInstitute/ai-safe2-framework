"""Provider-neutral adapter validation and conformance commands."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.adapters import AdapterError, evaluate_conformance, load_json_regular
from safe2.contracts import validate_artifact


@click.group("adapter")
def adapter() -> None:
    """Validate third-party evidence adapters without executing them."""


@adapter.command("validate")
@click.argument("descriptor", type=click.Path(path_type=Path, exists=True, dir_okay=False))
def validate_adapter(descriptor: Path) -> None:
    """Validate one safe2.adapter.v1 descriptor."""
    try:
        value = load_json_regular(descriptor)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    errors = validate_artifact("adapter-descriptor-v1", value)
    click.echo(
        json.dumps({"valid": not errors, "error_count": len(errors), "errors": errors}, indent=2)
    )
    if errors:
        raise SystemExit(1)


@adapter.command("conformance")
@click.argument("descriptor", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.argument(
    "specimens",
    nargs=-1,
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
)
@click.option("--output", "output", type=click.Path(path_type=Path), required=True)
def conformance(descriptor: Path, specimens: tuple[Path, ...], output: Path) -> None:
    """Evaluate attributed evidence specimens against one adapter descriptor."""
    if output.exists() or output.is_symlink():
        raise click.ClickException(f"output already exists: {output}")
    try:
        definition = load_json_regular(descriptor)
        cases = [(path.name, load_json_regular(path)) for path in specimens]
        report = evaluate_conformance(definition, cases)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    click.echo(json.dumps(report, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)
