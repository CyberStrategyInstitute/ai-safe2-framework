from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from safe2.cli import cli
from safe2.discovery.card import render_environment_html, render_environment_markdown
from safe2.discovery.integrity import seal_inventory
from safe2.discovery.posture import assess_posture


def _assessed(root: Path):
    discovery = {
        "schema_version": "safe2.discovery.v1",
        "collected_at": "2026-09-04T00:00:00+00:00",
        "scope": {"type": "local", "root": str(root)},
        "summary": {
            "harnesses_detected": 1,
            "execution_environments": 1,
            "shells_detected": 1,
            "assessment_status": "inventory_only",
            "explicit_targets": 0,
            "targets_completed": 0,
            "targets_failed": 0,
        },
        "harnesses": [
            {"id": "codex", "commands": [{"command": "codex"}], "evidence": []}
        ],
        "targets": [],
        "asset_inventory": {"assets": [], "counts": {}, "truncated": False},
        "limitations": [],
    }
    discovery["posture"] = assess_posture(discovery)
    return seal_inventory(discovery)


def test_environment_card_has_decision_quality_sections(tmp_path: Path):
    markdown = render_environment_markdown(_assessed(tmp_path))
    for heading in (
        "At a glance",
        "Decision basis",
        "Evidence conflicts",
        "Prioritized paths forward",
        "Impacts",
        "Alternatives",
        "Recommended path",
        "History",
        "Coverage and limitations",
    ):
        assert heading in markdown
    assert "NOT ESTIMABLE" in markdown
    assert "Validate, prioritize, then remediate" in markdown
    assert "Human owner not assigned" in markdown


def test_environment_card_escapes_untrusted_scope(tmp_path: Path):
    discovery = _assessed(tmp_path)
    discovery["scope"]["root"] = "bad | scope\n<script>alert(1)</script>"
    markdown = render_environment_markdown(discovery)
    html = render_environment_html(discovery)
    assert "bad \\| scope &lt;script&gt;alert\\(1\\)&lt;/script&gt;" in markdown
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_doctor_writes_markdown_and_html_cards(tmp_path: Path):
    runner = CliRunner()
    for card_format, suffix in (("markdown", "md"), ("html", "html")):
        output = tmp_path / f"card.{suffix}"
        result = runner.invoke(
            cli,
            [
                "doctor",
                str(tmp_path),
                "--no-wsl",
                "--assess",
                "--card-format",
                card_format,
                "--card-output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.is_file()
        assert "Environment Decision Card" in output.read_text(encoding="utf-8")


def test_environment_card_includes_policy_decision(tmp_path: Path):
    discovery = _assessed(tmp_path)
    discovery["policy_decision"] = {
        "policy_id": "production-default",
        "disposition": "HOLD",
        "violations": [],
        "unmet_prerequisites": [
            {"rule": "require_baseline", "reason": "No baseline was supplied."}
        ],
    }
    markdown = render_environment_markdown(discovery)
    html = render_environment_html(discovery)
    assert "Policy decision: **HOLD**" in markdown
    assert "Unmet prerequisite `require_baseline`" in markdown
    assert "production-default" in html
    assert "Unmet prerequisite" in html
    assert "No baseline was supplied." in html
    assert "configuration_inspection_requested" in html


def test_doctor_card_requires_assessment_and_output(tmp_path: Path):
    runner = CliRunner()
    missing_assess = runner.invoke(
        cli,
        [
            "doctor",
            str(tmp_path),
            "--no-wsl",
            "--card-format",
            "markdown",
            "--card-output",
            str(tmp_path / "card.md"),
        ],
    )
    assert missing_assess.exit_code != 0
    assert "requires --assess" in missing_assess.output
    missing_output = runner.invoke(
        cli, ["doctor", str(tmp_path), "--no-wsl", "--assess", "--card-format", "html"]
    )
    assert missing_output.exit_code != 0
    assert "must be supplied together" in missing_output.output
