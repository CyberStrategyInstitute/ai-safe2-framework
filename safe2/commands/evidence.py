"""Collect attributed evidence from repository and third-party providers."""

from __future__ import annotations

import json
from pathlib import Path

import click


def _emit(result: dict, output: str | None) -> None:
    body = json.dumps(result, indent=2) + "\n"
    if output:
        path = Path(output)
        if path.is_symlink():
            raise click.ClickException("evidence output must not be a symbolic link")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        except OSError as exc:
            raise click.ClickException(
                f"evidence output could not be written: {type(exc).__name__}"
            ) from exc
        click.echo(f"Evidence bundle: {output}")
    else:
        click.echo(body, nl=False)


@click.group()
def evidence():
    """Collect attributed evidence without claiming conformance."""


@evidence.command("system")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Exit 1 after writing when identity gaps remain.")
@click.pass_context
def system_evidence(ctx: click.Context, source: Path, output: Path, strict: bool) -> None:
    """Normalize a model/harness/tool/system identity declaration."""
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.system_identity import ingest

    try:
        result = ingest(read_bytes(source, limit=1_000_000))
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("System identity intake failed: invalid source or unsafe/unavailable I/O") from exc
    click.echo(json.dumps({"output": str(output), "summary": result["summary"],
                           "identity_verified": False, "configuration_verified": False,
                           "conformance_claim": False}))
    summary = result["summary"]
    if strict and any((summary["coverage_partial"], summary["coverage_missing"],
                       summary["unknown_components"], summary["unversioned_components"],
                       summary["unbound_components"])):
        ctx.exit(1)


@evidence.command("harness")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Exit 1 after writing when any coverage domain is not complete.")
@click.pass_context
def harness_evidence(ctx: click.Context, source: Path, output: Path, strict: bool) -> None:
    """Import a normalized harness export; no native logs or target code are read."""
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.harness import ingest

    try:
        result = ingest(read_bytes(source, limit=1_000_000))
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Harness intake failed: invalid source or unsafe/unavailable I/O") from exc
    click.echo(json.dumps({"output": str(output), "summary": result["summary"],
                           "completion_verified": False, "conformance_claim": False}))
    if strict and (result["summary"]["coverage_partial"] or result["summary"]["coverage_missing"]):
        ctx.exit(1)


@evidence.command("nexus")
@click.argument("target")
@click.option("--output", "-o", default=None)
@click.option("--timeout", default=5.0, type=float)
@click.option("--strict", is_flag=True, help="Exit 1 when runtime collection has failed endpoints.")
def nexus_evidence(target: str, output: str | None, timeout: float, strict: bool):
    """Collect evidence from a NEXUS checkout or read-only runtime endpoints."""
    from safe2.evidence.nexus import collect, collect_runtime

    try:
        if target.startswith(("http://", "https://")):
            result = collect_runtime(target, timeout=timeout)
        else:
            path = Path(target)
            if not path.is_dir():
                raise click.ClickException(
                    f"NEXUS path does not exist or is not a directory: {target}"
                )
            result = collect(path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(result, output)
    if strict and result["summary"].get("failed", 0):
        raise click.ClickException("NEXUS runtime evidence collection was incomplete")


@evidence.command("skillspector")
@click.argument("target")
@click.option("--llm/--no-llm", default=False)
@click.option("--output", "-o", default=None)
@click.option("--timeout", default=300.0, type=click.FloatRange(min=1.0))
@click.option("--executable", default="skillspector", show_default=True,
              help="Trusted SkillSpector executable, including a separate environment's absolute path.")
def skillspector_evidence(target: str, llm: bool, output: str | None, timeout: float, executable: str):
    """Collect SkillSpector JSON while retaining provider attribution."""
    from safe2.evidence.skillspector import collect

    try:
        result = collect(target, no_llm=not llm, timeout=timeout, executable=executable)
    except (RuntimeError, TypeError, OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(result, output)


@evidence.command("manifest")
@click.argument("artifacts", nargs=-1, required=True, type=click.Path(path_type=Path, dir_okay=False, exists=True))
@click.option("--subject-id", required=True, help="Stable identifier for the assessed system or environment.")
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.option("--max-bytes", default=20_000_000, type=click.IntRange(1, 100_000_000), show_default=True)
@click.option("--strict", is_flag=True, help="Exit 1 when any artifact is invalid or unsupported.")
def evidence_manifest(
    artifacts: tuple[Path, ...], subject_id: str, output: Path, max_bytes: int, strict: bool
) -> None:
    """Bind heterogeneous JSON evidence into one hashed run manifest."""
    from safe2.evidence.manifest import create_manifest

    try:
        result = create_manifest(artifacts, subject_id=subject_id, max_bytes=max_bytes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(result, str(output))
    if strict and result["summary"]["invalid"]:
        raise SystemExit(1)
