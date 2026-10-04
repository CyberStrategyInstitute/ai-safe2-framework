"""AISM scoring, comparison, and human Decision Card commands."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import click

from safe2.aism.card import render_html, render_markdown
from safe2.aism.ingest import create_assessment
from safe2.aism.scoring import assess


def _load(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise click.ClickException(f"Could not read assessment input: {exc}") from exc


@click.group()
def aism():
    """Score AISM evidence and produce decision-quality human outputs."""


@aism.command("init")
@click.argument("output", default="aism-assessment.json")
def init_assessment(output: str):
    """Create an explicit, unscored AISM assessment template."""
    cells = {
        f"P{pillar}.D{dimension}": None
        for pillar in range(1, 6)
        for dimension in range(1, 7)
    }
    template = {
        "schema_version": "1.0",
        "subject": {
            "id": "replace-me",
            "name": "Replace Me",
            "kind": "environment",
            "act_tier": "ACT-2",
            "target_score": 3.5,
        },
        "cells": cells,
        "facts": [],
        "assumptions": [],
        "conflicts": [],
        "unknowns": [],
        "alternatives": [],
        "history": [],
        "recommendation": {},
    }
    Path(output).write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    click.echo(f"AISM assessment template: {output}")


@aism.command("ingest")
@click.argument("evidence_bundles", nargs=-1, required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--subject-id", required=True)
@click.option("--subject-name", required=True)
@click.option("--output", "-o", required=True)
def ingest_evidence(evidence_bundles: tuple[str, ...], subject_id: str, subject_name: str, output: str):
    """Import NEXUS, SkillSpector or Challenge evidence without inventing AISM ratings."""
    from safe2.challenge.io import read_json, write_json

    try:
        bundles = [read_json(path) for path in evidence_bundles]
        assessment = create_assessment(bundles, subject_id=subject_id, subject_name=subject_name)
        write_json(output, assessment)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        raise click.ClickException(
            "Evidence ingestion failed. Check the input contracts and use a new local output file."
        ) from exc
    click.echo(f"AISM unscored evidence assessment: {output}")


@aism.command("score")
@click.argument("assessment", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format", "fmt", type=click.Choice(["json", "markdown", "html"]), default="markdown"
)
@click.option("--output", default=None)
def score_assessment(assessment: str, fmt: str, output: str | None):
    """Score evidence while preserving facts, assumptions, conflicts, and unknowns."""
    try:
        result = assess(_load(assessment))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if fmt == "json":
        body = json.dumps(result, indent=2) + "\n"
    elif fmt == "html":
        body = render_html(result)
    else:
        body = render_markdown(result)
    if output:
        Path(output).write_text(body, encoding="utf-8")
        click.echo(f"AISM {fmt} output: {output}")
    else:
        click.echo(body, nl=False)


@aism.command("compare")
@click.argument("previous", type=click.Path(exists=True, dir_okay=False))
@click.argument("current", type=click.Path(exists=True, dir_okay=False))
def compare_assessments(previous: str, current: str):
    """Compare two assessments without hiding incomplete coverage."""
    try:
        old = assess(_load(previous))
        new = assess(_load(current))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    old_score, new_score = old["score"]["raw"], new["score"]["raw"]
    delta = None if old_score is None or new_score is None else round(new_score - old_score, 2)
    click.echo(
        json.dumps(
            {
                "previous": {"score": old_score, "decision": old["decision"]["disposition"]},
                "current": {"score": new_score, "decision": new["decision"]["disposition"]},
                "delta": delta,
                "coverage_delta": round(
                    new["score"]["completeness"] - old["score"]["completeness"], 3
                ),
            },
            indent=2,
        )
    )


@aism.command("remediation-init")
@click.argument("assessment", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--assessment-scope",
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
)
@click.option("--decision-owner", required=True)
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
def init_remediation(
    assessment: Path,
    system_identity: Path,
    assessment_scope: Path,
    decision_owner: str,
    output: Path,
) -> None:
    """Create a hash-bound, unpopulated remediation source template."""
    from safe2.challenge.io import parse_json, read_bytes, write_json
    from safe2.contracts import validate_artifact

    try:
        assessment_data = read_bytes(assessment, limit=1_000_000)
        identity_data = read_bytes(system_identity, limit=5_000_000)
        scope_data = read_bytes(assessment_scope, limit=20_000_000)
        assessment_value = parse_json(assessment_data)
        identity_value = parse_json(identity_data)
        scope_value = parse_json(scope_data)
        if validate_artifact("aism-assessment-v1", assessment_value):
            raise ValueError("Assessment violates its evidence contract")
        if validate_artifact("system-identity-manifest-v1", identity_value):
            raise ValueError("System identity violates its evidence contract")
        if validate_artifact("assessment-scope-manifest-v1", scope_value):
            raise ValueError("Assessment scope violates its evidence contract")
        subject_id = assessment_value["subject"]["id"]
        if identity_value["subject"]["subject_id"] != subject_id:
            raise ValueError("System identity subject does not match assessment")
        if scope_value["subject"]["subject_id"] != subject_id:
            raise ValueError("Assessment scope subject does not match assessment")
        if (
            scope_value["subject"]["system_fingerprint_sha256"]
            != identity_value["system_fingerprint_sha256"]
        ):
            raise ValueError("Assessment scope is not bound to the system identity")
        template = {
            "schema_version": "safe2.aism-remediation-source.v1",
            "plan_id": f"{subject_id}-remediation",
            "subject_id": subject_id,
            "decision_owner": decision_owner,
            "bindings": {
                "assessment_sha256": hashlib.sha256(assessment_data).hexdigest(),
                "system_identity_sha256": hashlib.sha256(identity_data).hexdigest(),
                "assessment_scope_sha256": hashlib.sha256(scope_data).hexdigest(),
            },
            "assumptions": [],
            "alternatives": [],
            "actions": [],
            "accepted_residual_risks": [],
        }
        write_json(output, template)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise click.ClickException(
            "Remediation initialization failed: inputs must be safe, readable assessment artifacts."
        ) from exc
    click.echo(f"AISM remediation source template: {output}")


@aism.command("plan")
@click.argument("source", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.argument("assessment", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--system-identity", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--assessment-scope",
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
)
@click.option("--previous", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--card", required=True, type=click.Path(path_type=Path))
@click.option(
    "--strict", is_flag=True, help="Exit 1 unless the plan is ready for a human decision."
)
@click.pass_context
def plan_remediation(
    ctx: click.Context,
    source: Path,
    assessment: Path,
    system_identity: Path,
    assessment_scope: Path,
    previous: Path | None,
    output: Path,
    card: Path,
    strict: bool,
) -> None:
    """Build an evidence-bound remediation plan and human decision card."""
    from safe2.aism.remediation import build, render_markdown
    from safe2.challenge.io import read_bytes, safe_path, write_json, write_text

    try:
        destinations = [safe_path(output), safe_path(card)]
        if len(set(destinations)) != 2 or any(path.exists() for path in destinations):
            raise ValueError("Outputs must be distinct and new")
        result = build(
            read_bytes(source, limit=1_000_000),
            read_bytes(assessment, limit=1_000_000),
            read_bytes(system_identity, limit=5_000_000),
            read_bytes(assessment_scope, limit=20_000_000),
            read_bytes(previous, limit=20_000_000) if previous else None,
        )
        write_json(output, result)
        created_output = destinations[0].lstat()
        try:
            write_text(card, render_markdown(result))
        except (OSError, ValueError):
            try:
                current = destinations[0].lstat()
                if (current.st_dev, current.st_ino) == (
                    created_output.st_dev,
                    created_output.st_ino,
                ):
                    destinations[0].unlink()
            except FileNotFoundError:
                pass
            raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise click.ClickException(
            "AISM remediation planning failed: invalid bindings, traceability, dependencies, or unsafe files."
        ) from exc
    click.echo(
        json.dumps(
            {
                "output": str(output),
                "card": str(card),
                "gate": result["decision"]["gate"],
                "remediation_authorized": False,
                "conformance_claim": False,
            }
        )
    )
    if strict and result["decision"]["gate"] != "ready_for_human_decision":
        ctx.exit(1)
