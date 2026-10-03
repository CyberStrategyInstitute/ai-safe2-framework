"""Provider-neutral adapter validation and conformance commands."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.adapters import AdapterError, evaluate_conformance, load_json_regular
from safe2.adapters.codex_jsonl import descriptor as codex_descriptor
from safe2.adapters.codex_jsonl import translate as translate_codex
from safe2.adapters.otel_jsonl import descriptor as otel_descriptor
from safe2.adapters.otel_jsonl import export_metadata as export_otel_metadata
from safe2.adapters.otel_jsonl import translate as translate_otel
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


def _write_new_json(output: Path, value: dict) -> None:
    if output.exists() or output.is_symlink():
        raise click.ClickException(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _write_new_jsonl(output: Path, value: dict) -> None:
    """Write one compact JSON value as exactly one JSON Lines record."""
    if output.exists() or output.is_symlink():
        raise click.ClickException(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        )
        handle.write("\n")


@adapter.command("codex-jsonl")
@click.argument("trace", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--codex-version", required=True, help="Version declared by the trace producer.")
@click.option("--output", type=click.Path(path_type=Path), required=True)
def codex_jsonl(trace: Path, codex_version: str, output: Path) -> None:
    """Translate an explicit Codex JSONL trace into privacy-safe evidence."""
    try:
        value = translate_codex(trace, codex_version)
        _write_new_json(output, value)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(value, indent=2))


@adapter.command("codex-descriptor")
@click.option("--codex-version", required=True, help="Version declared by the trace producer.")
@click.option("--output", type=click.Path(path_type=Path), required=True)
def write_codex_descriptor(codex_version: str, output: Path) -> None:
    """Write the matching Codex adapter descriptor for conformance checks."""
    try:
        value = codex_descriptor(codex_version)
        _write_new_json(output, value)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(value, indent=2))


@adapter.command("otel-jsonl")
@click.argument("trace", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--otel-version", required=True, help="OpenTelemetry version declared by producer.")
@click.option("--output", type=click.Path(path_type=Path), required=True)
def otel_jsonl(trace: Path, otel_version: str, output: Path) -> None:
    """Translate an OTLP/JSON traces file into privacy-safe evidence."""
    try:
        value = translate_otel(trace, otel_version)
        _write_new_json(output, value)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(value, indent=2))


@adapter.command("otel-descriptor")
@click.option("--otel-version", required=True, help="OpenTelemetry version declared by producer.")
@click.option("--output", type=click.Path(path_type=Path), required=True)
def write_otel_descriptor(otel_version: str, output: Path) -> None:
    """Write the matching OpenTelemetry adapter descriptor."""
    try:
        value = otel_descriptor(otel_version)
        _write_new_json(output, value)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(value, indent=2))


@adapter.command("otel-export")
@click.argument("evidence", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", type=click.Path(path_type=Path), required=True)
def otel_export(evidence: Path, output: Path) -> None:
    """Export non-content SAFE2 evidence metadata as OTLP/JSON LogsData."""
    try:
        value = export_otel_metadata(load_json_regular(evidence))
        _write_new_jsonl(output, value)
    except AdapterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(value, indent=2))
