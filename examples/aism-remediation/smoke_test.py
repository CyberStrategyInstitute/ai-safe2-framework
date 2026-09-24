"""Executable synthetic acceptance fixture for CLI 0.8 remediation planning."""

from __future__ import annotations

import hashlib
import json
import tempfile
from importlib.resources import files
from pathlib import Path

from safe2.aism.remediation import build, render_markdown
from safe2.evidence.scope import build as build_scope
from safe2.evidence.system_identity import ingest as ingest_identity


def encoded(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def main() -> None:
    data = files("safe2.data")
    identity = ingest_identity(data.joinpath("system-identity-source-demo.json").read_bytes())
    identity_data = encoded(identity)
    with tempfile.TemporaryDirectory(prefix="safe2-aism-remediation-") as temporary:
        root = Path(temporary)
        (root / "safe2").mkdir()
        (root / "safe2" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        scope = build_scope(
            data.joinpath("assessment-scope-source-demo.json").read_bytes(), identity_data, root
        )
        scope_data = encoded(scope)

        evidence = [
            {
                "grade": "E5",
                "category": category,
                "source": f"fixture-{category}",
                "artifact_id": f"fixture-{category}",
                "observed_at": "2026-09-21T00:00:00Z",
                "collector": "synthetic-example",
                "verification": "independently_verified",
            }
            for category in ("documentary", "operational", "attestation")
        ]
        assessment = {
            "schema_version": "1.0",
            "subject": {
                "id": "demo-agent-system",
                "name": "Synthetic governed agent",
                "kind": "implementation",
                "target_score": 3.5,
            },
            "cells": {
                f"P{pillar}.D{dimension}": {
                    "metrics": {"coverage": "H", "robustness": "H", "sovereignty_assurance": "H"},
                    "evidence": evidence,
                }
                for pillar in range(1, 6)
                for dimension in range(1, 7)
            },
            "facts": [{"id": "FACT-1", "statement": "The synthetic completion test passed."}],
            "assumptions": [
                {
                    "id": "ASSUMPTION-1",
                    "statement": "The fixture boundary is complete.",
                    "effect_if_false": "The result returns to review.",
                }
            ],
            "conflicts": [],
            "unknowns": [],
            "alternatives": [],
            "history": [],
            "recommendation": {
                "summary": "Submit the internally consistent fixture for human review."
            },
        }
        assessment_data = encoded(assessment)
        source = {
            "schema_version": "safe2.aism-remediation-source.v1",
            "plan_id": "synthetic-plan",
            "subject_id": "demo-agent-system",
            "decision_owner": "Example human owner",
            "bindings": {
                "assessment_sha256": hashlib.sha256(assessment_data).hexdigest(),
                "system_identity_sha256": hashlib.sha256(identity_data).hexdigest(),
                "assessment_scope_sha256": hashlib.sha256(scope_data).hexdigest(),
            },
            "assumptions": [],
            "alternatives": [
                {
                    "id": "ALT-1",
                    "name": "Repeat the fixture",
                    "pros": ["Adds another observation"],
                    "cons": ["Does not add production evidence"],
                    "reason_not_selected": "The current purpose is contract verification.",
                }
            ],
            "actions": [
                {
                    "id": "ACTION-1",
                    "sequence": 1,
                    "title": "Verify the synthetic contract",
                    "description": "Run and retain the bounded fixture result.",
                    "status": "completed",
                    "priority": "low",
                    "owner": "Example human owner",
                    "control_refs": ["P2.T3.1"],
                    "aism_cells": ["P2.D3"],
                    "evidence_refs": ["FACT-1"],
                    "assumption_refs": ["ASSUMPTION-1"],
                    "dependencies": [],
                    "alternative_refs": ["ALT-1"],
                    "impacts": [
                        {"perspective": "ciso", "statement": "Shows the decision boundary."},
                        {
                            "perspective": "engineering",
                            "statement": "Exercises the machine contract.",
                        },
                        {
                            "perspective": "governance",
                            "statement": "Keeps authorization human-owned.",
                        },
                        {
                            "perspective": "agent",
                            "statement": "Provides deterministic result fields.",
                        },
                    ],
                    "why": "The release needs a reproducible installed workflow.",
                    "why_not": "The fixture must not be treated as production evidence.",
                    "exit_criteria": ["The canonical plan validates and the card renders."],
                    "completion_evidence_refs": ["FACT-1"],
                    "residual_risk": "Synthetic evidence does not establish deployment behavior.",
                    "residual_risk_ref": None,
                }
            ],
            "accepted_residual_risks": [],
        }
        plan = build(encoded(source), assessment_data, identity_data, scope_data)
        card = render_markdown(plan)
        if "Remediation authorized: **false**" not in card:
            raise SystemExit("human authority boundary missing")
        print(
            json.dumps(
                {
                    "gate": plan["decision"]["gate"],
                    "remediation_authorized": plan["decision"]["remediation_authorized"],
                    "conformance_claim": plan["decision"]["conformance_claim"],
                }
            )
        )


if __name__ == "__main__":
    main()
