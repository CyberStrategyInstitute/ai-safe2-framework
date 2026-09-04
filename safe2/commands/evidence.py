"""Collect attributed evidence from repository and third-party providers."""

from __future__ import annotations

import json
from pathlib import Path

import click


def _emit(result: dict, output: str | None) -> None:
    body = json.dumps(result, indent=2) + "\n"
    if output:
        Path(output).write_text(body, encoding="utf-8")
        click.echo(f"Evidence bundle: {output}")
    else:
        click.echo(body, nl=False)


@click.group()
def evidence():
    """Collect attributed evidence without claiming conformance."""


@evidence.command("nexus")
@click.argument("target")
@click.option("--output", "-o", default=None)
@click.option("--timeout", default=5.0, type=float)
@click.option("--strict", is_flag=True, help="Exit 1 when runtime collection has failed endpoints.")
def nexus_evidence(target: str, output: str | None, timeout: float, strict: bool):
    """Collect evidence from a NEXUS checkout or read-only runtime endpoints."""
    from safe2.evidence.nexus import collect, collect_runtime

    if target.startswith(("http://", "https://")):
        result = collect_runtime(target, timeout=timeout)
    else:
        path = Path(target)
        if not path.is_dir():
            raise click.ClickException(f"NEXUS path does not exist or is not a directory: {target}")
        result = collect(path)
    _emit(result, output)
    if strict and result["summary"].get("failed", 0):
        raise click.ClickException("NEXUS runtime evidence collection was incomplete")


@evidence.command("skillspector")
@click.argument("target")
@click.option("--llm/--no-llm", default=False)
@click.option("--output", "-o", default=None)
@click.option("--timeout", default=300.0, type=click.FloatRange(min=1.0))
def skillspector_evidence(target: str, llm: bool, output: str | None, timeout: float):
    """Collect SkillSpector JSON while retaining provider attribution."""
    from safe2.evidence.skillspector import collect

    try:
        result = collect(target, no_llm=not llm, timeout=timeout)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(result, output)
