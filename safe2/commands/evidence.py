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


@evidence.command("truth")
@click.argument("policy", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.argument("artifacts", nargs=-1, required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--card", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Exit 1 unless evidence is ready for a human decision.")
@click.pass_context
def operational_truth(ctx: click.Context, policy: Path, artifacts: tuple[Path, ...], output: Path, card: Path, strict: bool) -> None:
    """Correlate task evidence across one or more agent harnesses."""
    from safe2.challenge.io import read_bytes, safe_path, write_json, write_text
    from safe2.evidence.operational_truth import build
    from safe2.evidence.operational_truth_card import render

    try:
        destinations = [safe_path(output), safe_path(card)]
        if len(set(destinations)) != 2 or any(path.exists() for path in destinations):
            raise ValueError("Outputs must be distinct and new")
        if len(artifacts) > 100:
            raise ValueError("At most 100 evidence artifacts are accepted")
        result = build(
            read_bytes(policy, limit=1_000_000),
            [read_bytes(path, limit=5_000_000) for path in artifacts],
        )
        write_json(output, result)
        try:
            write_text(card, render(result))
        except (OSError, ValueError):
            output.unlink(missing_ok=True)
            raise
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Operational-truth synthesis failed: invalid, conflicting, duplicate, or unsafe evidence"
        ) from exc
    click.echo(json.dumps({
        "output": str(output), "card": str(card), "gate": result["gate"],
        "completion_verified": False, "billing_verified": False,
        "conformance_claim": False,
    }))
    if strict and result["gate"] != "ready_for_human_decision":
        ctx.exit(1)


@evidence.command("changes")
@click.argument("root", type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--baseline", type=click.Path(path_type=Path, exists=True, dir_okay=False),
              help="Prior change-monitor JSON. Omit for the first explicit baseline run.")
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--max-files", default=10_000, type=click.IntRange(1, 10_000), show_default=True,
              help="Maximum filesystem entries traversed in the explicit root.")
@click.option("--max-file-bytes", default=1_000_000, type=click.IntRange(1, 1_000_000), show_default=True)
@click.option("--strict", is_flag=True, help="Exit 1 on hold or reject after preserving the report.")
@click.pass_context
def changed_agent_inputs(ctx: click.Context, root: Path, baseline: Path | None, output: Path,
                         max_files: int, max_file_bytes: int, strict: bool) -> None:
    """One-shot local/CI check for changed skills and agent configuration."""
    from safe2.challenge.io import parse_json, read_bytes, safe_path, write_json
    from safe2.evidence.change_monitor import monitor

    try:
        destination = safe_path(output)
        if destination.exists():
            raise ValueError("Output must be new")
        previous = parse_json(read_bytes(baseline, limit=5_000_000)) if baseline else None
        result = monitor(root, previous, max_files=max_files, max_file_bytes=max_file_bytes)
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Agent-input monitoring failed: invalid baseline, unsafe path, or incomplete bounded coverage"
        ) from exc
    click.echo(json.dumps({
        "output": str(output), "summary": result["summary"], "decision": result["decision"],
        "telemetry": "none", "content_exported": False, "conformance_claim": False,
    }))
    if strict and result["decision"] != "approve":
        ctx.exit(1)


@evidence.command("readiness")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--assessment-scope", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--change-attribution", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--card", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Exit 1 unless evidence is ready for a human decision.")
@click.pass_context
def readiness_evidence(ctx: click.Context, source: Path, system_identity: Path, assessment_scope: Path, change_attribution: Path, output: Path, card: Path, strict: bool) -> None:
    """Create agent JSON and a human technical release-readiness card."""
    from safe2.challenge.io import read_bytes, safe_path, write_json, write_text
    from safe2.evidence.readiness import build
    from safe2.evidence.readiness_card import render
    try:
        destinations = [safe_path(output), safe_path(card)]
        if len(set(destinations)) != 2 or any(path.exists() for path in destinations): raise ValueError("Outputs must be distinct and new")
        result = build(read_bytes(source, limit=5_000_000), read_bytes(system_identity, limit=1_000_000), read_bytes(assessment_scope, limit=5_000_000), read_bytes(change_attribution, limit=5_000_000))
        write_json(output, result); write_text(card, render(result))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Release-readiness synthesis failed: invalid, mismatched, ambiguous, or unsafe evidence") from exc
    click.echo(json.dumps({"output": str(output), "card": str(card), "status": result["gate"]["status"], "release_authorized": False, "conformance_claim": False}))
    if strict and result["gate"]["status"] != "ready_for_human_decision": ctx.exit(1)


@evidence.command("attribute")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--baseline-scope", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--current-scope", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True, help="Exit 1 after writing when attribution remains unknown.")
@click.pass_context
def attribute_evidence(ctx: click.Context, source: Path, system_identity: Path, baseline_scope: Path, current_scope: Path, output: Path, strict: bool) -> None:
    """Attribute findings between a trusted baseline and current revision."""
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.attribution import build

    try:
        result = build(read_bytes(source, limit=5_000_000), read_bytes(system_identity, limit=1_000_000), read_bytes(baseline_scope, limit=5_000_000), read_bytes(current_scope, limit=5_000_000))
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Change attribution failed: invalid, mismatched, ambiguous, or unsafe evidence") from exc
    click.echo(json.dumps({"output": str(output), "summary": result["summary"], "change_verified": False, "conformance_claim": False}))
    if strict and result["summary"]["unknown"]:
        ctx.exit(1)


@evidence.command("scope")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--project-root", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--max-entries", default=10_000, type=click.IntRange(1, 10_000), show_default=True)
@click.option("--strict", is_flag=True, help="Exit 1 after writing when scope gaps or conflicts remain.")
@click.pass_context
def scope_evidence(
    ctx: click.Context,
    source: Path,
    project_root: Path,
    system_identity: Path,
    output: Path,
    max_entries: int,
    strict: bool,
) -> None:
    """Inventory declared deployment scope without reading file contents."""
    from safe2.challenge.io import read_bytes, write_json
    from safe2.evidence.scope import build

    try:
        result = build(
            read_bytes(source, limit=1_000_000),
            read_bytes(system_identity, limit=1_000_000),
            project_root,
            max_entries=max_entries,
        )
        write_json(output, result)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException(
            "Assessment scope failed: invalid declaration, identity, project root, or unsafe/unavailable I/O"
        ) from exc
    click.echo(json.dumps({
        "output": str(output),
        "summary": result["summary"],
        "scope_verified": False,
        "content_inspected": False,
        "conformance_claim": False,
    }))
    summary = result["summary"]
    if strict and any((
        summary["unsafe_links"], summary["conflicts"], summary["truncated"],
        summary["partial"], summary["unclassified"], not summary["included"],
    )):
        ctx.exit(1)


@evidence.command("diagnose")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--card", type=click.Path(path_type=Path), help="Optional human-readable Markdown card.")
@click.option("--strict", is_flag=True, help="Exit 1 unless one strong/moderate primary candidate is ranked.")
@click.pass_context
def diagnose_evidence(
    ctx: click.Context, source: Path, system_identity: Path, output: Path,
    card: Path | None, strict: bool,
) -> None:
    """Rank attributed failure locations against a system identity."""
    from safe2.challenge.io import read_bytes, safe_path, write_json, write_text
    from safe2.evidence.diagnosis import diagnose
    from safe2.evidence.diagnosis_card import render

    try:
        destinations = [safe_path(output)] + ([safe_path(card)] if card else [])
        if len(set(destinations)) != len(destinations) or any(path.exists() for path in destinations):
            raise ValueError("Output destinations must be distinct and must not already exist")
        result = diagnose(
            read_bytes(source, limit=1_000_000),
            read_bytes(system_identity, limit=1_000_000),
        )
        write_json(output, result)
        if card:
            write_text(card, render(result))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        raise click.ClickException("Failure diagnosis failed: invalid evidence or unsafe/unavailable I/O") from exc
    click.echo(json.dumps({
        "output": str(output), "card": str(card) if card else None,
        "diagnosis_status": result["diagnosis_status"],
        "primary_candidate_id": result["primary_candidate_id"],
        "root_cause_verified": False, "probability_estimate": False,
        "conformance_claim": False,
    }))
    top_level = result["candidates"][0]["evidence_assessment"]["level"]
    if strict and (result["diagnosis_status"] != "ranked_candidate" or top_level not in {"strong", "moderate"}):
        ctx.exit(1)


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
