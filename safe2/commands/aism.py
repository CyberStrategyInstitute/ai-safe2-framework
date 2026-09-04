"""AISM scoring, comparison, and human Decision Card commands."""

from __future__ import annotations

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
    """Import NEXUS or SkillSpector bundles without inventing AISM ratings."""
    bundles = [_load(path) for path in evidence_bundles]
    assessment = create_assessment(bundles, subject_id=subject_id, subject_name=subject_name)
    Path(output).write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
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
