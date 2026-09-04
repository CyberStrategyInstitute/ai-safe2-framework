"""Conservative evidence-bundle ingestion for AISM assessments."""

from __future__ import annotations

from typing import Any


def _cell_ids() -> dict[str, None]:
    return {f"P{pillar}.D{dimension}": None for pillar in range(1, 6) for dimension in range(1, 7)}


def _suggestions(bundle: dict[str, Any]) -> list[str]:
    suggestions: set[str] = set()
    for observation in bundle.get("observations", []):
        for reference in observation.get("control_refs", []):
            if isinstance(reference, str) and len(reference) >= 2 and reference[0] == "P":
                pillar = reference[1]
                if pillar in "12345":
                    suggestions.add(f"P{pillar}.D3")
    provider = bundle.get("provider", {}).get("name", "")
    if "SkillSpector" in provider:
        suggestions.update(("P1.D3", "P2.D6", "P4.D3"))
    return sorted(suggestions)


def create_assessment(bundles: list[dict], *, subject_id: str, subject_name: str) -> dict:
    """Create an unscored assessment; never infer maturity ratings from scanner output."""
    imports = []
    facts = []
    for index, bundle in enumerate(bundles, start=1):
        provider = bundle.get("provider", {})
        provider_name = provider.get("name", "Unknown evidence provider")
        imports.append(
            {
                "provider": provider,
                "collected_at": bundle.get("collected_at"),
                "target": bundle.get("target"),
                "summary": bundle.get("summary"),
                "conformance_claim": bundle.get("conformance_claim", False),
                "candidate_cells": _suggestions(bundle),
                "human_confirmation_required": True,
                "source_bundle": bundle,
            }
        )
        facts.append(
            {
                "id": f"IMPORTED-{index:03d}",
                "statement": (
                    f"Evidence bundle from {provider_name} was imported for human mapping; "
                    "no AISM rating was inferred."
                ),
            }
        )
    return {
        "schema_version": "1.0",
        "subject": {
            "id": subject_id,
            "name": subject_name,
            "kind": "implementation",
            "target_score": 3.5,
        },
        "cells": _cell_ids(),
        "topics": {"evidence_imports": imports},
        "facts": facts,
        "assumptions": [],
        "conflicts": [],
        "unknowns": [
            {
                "id": "MAPPING-REQUIRED",
                "question": "Which imported observations satisfy each AISM metric and evidence grade?",
                "severity": "HIGH",
            }
        ],
        "impacts": [],
        "alternatives": [],
        "history": [],
        "recommendation": {
            "summary": "Complete human evidence mapping and metric ratings before a deployment decision.",
            "basis": ["Scanner and runtime evidence cannot establish AISM maturity without review."],
        },
    }
