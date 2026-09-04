from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from safe2.aism.card import render_html, render_markdown
from safe2.aism.model import load_model
from safe2.aism.scoring import assess
from safe2.cli import cli
from safe2.commands.example import inventory
from safe2.evidence.nexus import CHECKS, collect
from safe2.evidence.skillspector import collect as collect_skillspector

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = REPO_ROOT / "examples" / "aism-decision-card" / "assessment.json"


def test_model_preserves_aism_weights_and_approved_uas_status():
    model = load_model()
    assert sum(pillar["weight"] for pillar in model["pillars"]) == 1
    assert sum(dimension["weight"] for dimension in model["dimensions"]) == 1
    assert model["framework"]["core_control_count"] == 161
    assert model["framework"]["cross_pillar_controls"] == "CP.1-CP.10"
    assert model["framework"]["regulatory_profiles"] == ["UAS-1.0"]


def test_example_holds_on_critical_conflict_and_renders_card():
    result = assess(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    assert result["score"]["completeness"] == 1
    assert result["decision"]["disposition"] == "HOLD"
    assert result["score"]["raw"] > result["score"]["evidence_adjusted"]
    card = render_markdown(result)
    assert "Decision Card" in card
    assert "Facts (2)" in card
    assert "Conflicts (1)" in card
    assert "FACT-001" in card
    assert "ASSUMPTION-001" in card
    assert "CONFLICT-001" in card
    assert "UNKNOWN-001" in card
    assert "## History" in card
    assert "method:" in card
    assert "Recommended path" in card
    html = render_html(result)
    assert "<!doctype html>" in html
    assert "Evidence" in html
    assert "History" in html
    assert "Material event" in html
    assert "Basis" in html
    assert "Limitations" in html


def test_init_template_is_explicitly_unscored(tmp_path):
    output = tmp_path / "assessment.json"
    invocation = CliRunner().invoke(cli, ["aism", "init", str(output)])
    assert invocation.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["cells"]) == 30
    assert all(value is None for value in payload["cells"].values())
    result = assess(payload)
    assert result["score"]["raw"] is None
    assert result["score"]["completeness"] == 0
    assert result["decision"]["disposition"] == "HOLD"


def test_missing_cells_are_not_passes():
    result = assess(
        {
            "schema_version": "1.0",
            "subject": {"id": "incomplete", "name": "Incomplete", "kind": "implementation"},
            "cells": {},
        }
    )
    assert result["score"]["raw"] is None
    assert result["score"]["completeness"] == 0
    assert result["decision"]["disposition"] == "HOLD"
    assert all(cell["status"] == "NOT_ASSESSED" for cell in result["cells"])


def test_normative_30_cell_hhh_rubric_scores_five():
    cells = {
        f"P{pillar}.D{dimension}": {
            "metrics": {"coverage": "H", "robustness": "H", "sovereignty_assurance": "H"},
            "evidence": [
                {
                    "grade": "E5",
                    "category": category,
                    "source": f"evidence-{category}",
                    "artifact_id": f"artifact-{category}",
                    "observed_at": "2026-09-03T12:00:00Z",
                    "collector": "independent-lab",
                    "verification": "independently_verified",
                }
                for category in ("documentary", "operational", "attestation")
            ],
        }
        for pillar in range(1, 6)
        for dimension in range(1, 7)
    }
    result = assess(
        {
            "schema_version": "1.0",
            "subject": {
                "id": "verified-system",
                "name": "Verified System",
                "kind": "implementation",
                "target_score": 4.5,
            },
            "cells": cells,
            "facts": [{"id": "FACT-1", "statement": "Independent evidence was reviewed."}],
            "recommendation": {"summary": "Proceed within the assessed scope."},
        }
    )
    assert result["score"]["raw"] == 5
    assert result["score"]["evidence_adjusted"] == 5
    assert result["score"]["evidence_confidence"] == 1
    assert result["score"]["maturity"]["name"] == "Sovereignty"
    assert result["decision"]["disposition"] == "PROCEED"


def test_probability_requires_attributed_range():
    payload = {
        "schema_version": "1.0",
        "subject": {"id": "guess", "name": "Guess", "kind": "implementation"},
        "cells": {},
        "alternatives": [{"name": "guess", "outcome_estimate": {"mode": "evidence_informed"}}],
    }
    try:
        assess(payload)
    except ValueError as exc:
        assert "missing outcome" in str(exc)
    else:
        raise AssertionError("unattributed probability should be rejected")


def test_schema_rejects_malformed_input_with_stable_error():
    try:
        assess({"schema_version": "1.0", "subject": "bad", "cells": {}})
    except ValueError as exc:
        assert "schema validation failed" in str(exc)
    else:
        raise AssertionError("malformed assessment should be rejected")


def test_compare_rejects_malformed_input_without_traceback(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text('{"schema_version":"1.0","subject":{},"cells":{}}', encoding="utf-8")
    result = CliRunner().invoke(cli, ["aism", "compare", str(malformed), str(malformed)])
    assert result.exit_code == 1
    assert "schema validation failed" in result.output
    assert "Traceback" not in result.output


def test_unverified_self_report_cannot_earn_proceed():
    cells = {
        f"P{pillar}.D{dimension}": {
            "metrics": {"coverage": "H", "robustness": "H", "sovereignty_assurance": "H"},
            "evidence": [
                {"grade": "E5", "category": category, "source": f"self-report-{category}"}
                for category in ("documentary", "operational", "attestation")
            ],
        }
        for pillar in range(1, 6)
        for dimension in range(1, 7)
    }
    result = assess(
        {
            "schema_version": "1.0",
            "subject": {"id": "self", "name": "Self Report", "kind": "implementation"},
            "cells": cells,
            "facts": [{"id": "SELF-1", "statement": "Evidence was supplied by the subject."}],
            "recommendation": {"summary": "Requested approval."},
        }
    )
    assert result["score"]["raw"] == 5
    assert result["score"]["evidence_adjusted"] < 3.5
    assert result["decision"]["disposition"] == "PROCEED_WITH_RESTRICTIONS"


def test_markdown_escapes_agent_controlled_table_content():
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    payload["impacts"][0]["statement"] = "break | table\n<script>alert(1)</script>"
    card = render_markdown(assess(payload))
    assert "break \\| table &lt;script&gt;alert(1)&lt;/script&gt;" in card


def test_aism_cli_json_and_markdown(tmp_path):
    runner = CliRunner()
    json_out = tmp_path / "decision.json"
    md_out = tmp_path / "card.md"
    result = runner.invoke(
        cli, ["aism", "score", str(EXAMPLE), "--format", "json", "--output", str(json_out)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(json_out.read_text(encoding="utf-8"))["decision"]["disposition"] == "HOLD"
    result = runner.invoke(
        cli, ["aism", "score", str(EXAMPLE), "--format", "markdown", "--output", str(md_out)]
    )
    assert result.exit_code == 0, result.output
    assert "AISM Decision Card" in md_out.read_text(encoding="utf-8")


def test_nexus_collector_is_attributed_and_does_not_claim_conformance():
    result = collect(REPO_ROOT / "NEXUS")
    assert result["summary"]["observed"] == len(CHECKS)
    assert result["summary"]["missing"] == 0
    assert result["conformance_claim"] is False
    assert all(item["sha256"] for item in result["observations"])
    assert all(item["control_refs"] for item in result["observations"])


def test_uas_profile_has_exactly_27_requirements():
    profile = json.loads(
        (REPO_ROOT / "00-cross-pillar" / "unbiased-ai" / "uas-profile-v1.json").read_text(
            encoding="utf-8"
        )
    )
    requirements = [
        requirement for layer in profile["layers"] for requirement in layer["requirements"]
    ]
    assert len(requirements) == 27
    assert len(set(requirements)) == 27
    assert profile["profile"]["adds_to_core_control_count"] is False
    assert profile["profile"]["adds_cross_pillar_control"] is False


def test_skillspector_adapter_preserves_attribution(monkeypatch, tmp_path):
    monkeypatch.setattr("safe2.evidence.skillspector.shutil.which", lambda _: "skillspector")
    monkeypatch.setattr(
        "safe2.evidence.skillspector.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout=json.dumps({"risk_score": 72, "recommendation": "DO_NOT_INSTALL"}),
            stderr="",
        ),
    )
    target = tmp_path / "candidate-skill"
    target.mkdir()
    (target / "SKILL.md").write_text("# Candidate", encoding="utf-8")
    result = collect_skillspector(str(target))
    assert result["provider"]["name"] == "NVIDIA SkillSpector"
    assert result["source_result"]["risk_score"] == 72
    assert result["source_exit_code"] == 1
    assert result["conformance_claim"] is False
    assert "no NVIDIA endorsement" in result["attribution"]
    assert result["provider"]["license"] == "Apache-2.0"
    assert len(result["target"]["sha256"]) == 64


def test_examples_inventory_and_executable_verification(monkeypatch):
    rows = inventory(REPO_ROOT)
    card = next(row for row in rows if row["id"] == "aism-decision-card")
    assert card["manifest"] is True
    monkeypatch.chdir(REPO_ROOT)
    result = CliRunner().invoke(cli, ["example", "verify", "aism-decision-card"])
    assert result.exit_code == 0, result.output
    assert '"status": "verified"' in result.output

    monkeypatch.chdir(REPO_ROOT / "examples" / "aism-decision-card")
    nested = CliRunner().invoke(cli, ["example", "verify", "aism-decision-card"])
    assert nested.exit_code == 0, nested.output


def test_aism_ingest_preserves_evidence_without_inventing_scores(tmp_path, monkeypatch):
    bundle = collect(REPO_ROOT / "NEXUS")
    bundle_path = tmp_path / "nexus.json"
    output = tmp_path / "assessment.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.chdir(REPO_ROOT)
    result = CliRunner().invoke(
        cli,
        [
            "aism",
            "ingest",
            str(bundle_path),
            "--subject-id",
            "nexus-local",
            "--subject-name",
            "NEXUS Local",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assessment = json.loads(output.read_text(encoding="utf-8"))
    assert all(value is None for value in assessment["cells"].values())
    assert assessment["topics"]["evidence_imports"][0]["human_confirmation_required"] is True
    assert assess(assessment)["decision"]["disposition"] == "HOLD"
