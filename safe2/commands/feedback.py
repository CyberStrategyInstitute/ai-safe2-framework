"""Capture operational agent friction as structured evaluation evidence."""

from __future__ import annotations

import json
from pathlib import Path

import click

from safe2.evidence.friction import (
    CATEGORIES,
    OUTCOMES,
    append_event,
    record_event,
    summarize_events,
)

DEFAULT_LOG = Path(".safe2/evidence/friction.jsonl")


@click.group("feedback")
def feedback() -> None:
    """Record privacy-safe LLM and agent workflow friction."""


@feedback.command("record")
@click.option("--category", type=click.Choice(sorted(CATEGORIES)), required=True)
@click.option("--outcome", type=click.Choice(sorted(OUTCOMES)), required=True)
@click.option("--severity", type=click.Choice(["low", "medium", "high", "critical"]), required=True)
@click.option("--summary", required=True, help="Short sanitized description; do not include secrets or prompt contents.")
@click.option("--harness", default=None)
@click.option("--environment", default=None)
@click.option("--evidence-ref", multiple=True, help="Reference to external verification, not raw sensitive output.")
@click.option("--resolved/--unresolved", default=False)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=DEFAULT_LOG, show_default=True)
def record_feedback(
    category: str,
    outcome: str,
    severity: str,
    summary: str,
    harness: str | None,
    environment: str | None,
    evidence_ref: tuple[str, ...],
    resolved: bool,
    output: Path,
) -> None:
    """Append one sanitized friction event to a local JSONL evidence log."""
    try:
        event = record_event(
            category=category,
            outcome=outcome,
            severity=severity,
            summary=summary,
            harness=harness,
            environment=environment,
            evidence_refs=evidence_ref,
            resolved=resolved,
        )
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    try:
        append_event(output, event)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(event, indent=2))


@feedback.command("summary")
@click.argument("source", type=click.Path(path_type=Path, dir_okay=False, exists=True), default=DEFAULT_LOG)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
@click.option("--max-bytes", default=20_000_000, type=click.IntRange(1, 100_000_000), show_default=True)
def feedback_summary(source: Path, output: Path | None, max_bytes: int) -> None:
    """Summarize friction and the claimed-versus-verified completion gap."""
    try:
        result = summarize_events(source, max_bytes=max_bytes)
    except (OSError, TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    body = json.dumps(result, indent=2) + "\n"
    if output:
        if output.is_symlink():
            raise click.ClickException("summary output must not be a symbolic link")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
        click.echo(f"Friction summary: {output}")
    else:
        click.echo(body, nl=False)
