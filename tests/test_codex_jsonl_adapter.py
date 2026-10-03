from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.adapters.codex_jsonl import descriptor, translate
from safe2.cli import cli
from safe2.contracts import validate_artifact


def write_trace(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def sample_rows() -> list[dict]:
    return [
        {"type": "item.started", "item": {"type": "command_execution", "command": "SECRET"}},
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "SECRET",
                "aggregated_output": "TOKEN",
                "status": "completed",
            },
        },
        {"type": "turn.completed", "usage": {"input_tokens": 120, "output_tokens": 30}},
    ]


def test_translation_is_schema_valid_and_does_not_retain_content(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace(trace, sample_rows())
    result = translate(trace, "1.2.3", observed_at="2026-10-03T00:00:00Z")
    assert not validate_artifact("adapter-evidence-v1", result)
    assert result["status"] == "complete"
    assert result["payload"]["usage"] == {"events": 1, "input_tokens": 120, "output_tokens": 30}
    assert result["payload"]["content_retained"] is False
    rendered = json.dumps(result)
    assert "SECRET" not in rendered
    assert "TOKEN" not in rendered
    assert str(trace.parent) not in rendered


def test_unknown_shapes_are_visible_as_partial_coverage(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace(trace, [{"type": "future.event", "prompt": "do not retain"}])
    result = translate(trace, "1.2.3")
    assert result["status"] == "partial"
    assert result["coverage"]["gaps"] == ["unmodeled:future.event=1"]
    assert "do not retain" not in json.dumps(result)
    assert not any(claim["name"] == "input_tokens" for claim in result["claims"])


def test_cli_outputs_descriptor_evidence_and_refuses_overwrite(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    evidence = tmp_path / "evidence.json"
    definition = tmp_path / "descriptor.json"
    write_trace(trace, sample_rows())
    runner = CliRunner()
    created = runner.invoke(
        cli,
        [
            "adapter",
            "codex-jsonl",
            str(trace),
            "--codex-version",
            "1.2.3",
            "--output",
            str(evidence),
        ],
    )
    assert created.exit_code == 0, created.output
    described = runner.invoke(
        cli,
        ["adapter", "codex-descriptor", "--codex-version", "1.2.3", "--output", str(definition)],
    )
    assert described.exit_code == 0, described.output
    assert json.loads(definition.read_text(encoding="utf-8")) == descriptor("1.2.3")
    conformance = tmp_path / "conformance.json"
    checked = runner.invoke(
        cli,
        ["adapter", "conformance", str(definition), str(evidence), "--output", str(conformance)],
    )
    assert checked.exit_code == 0, checked.output
    assert json.loads(conformance.read_text(encoding="utf-8"))["status"] == "passed"
    again = runner.invoke(
        cli,
        [
            "adapter",
            "codex-jsonl",
            str(trace),
            "--codex-version",
            "1.2.3",
            "--output",
            str(evidence),
        ],
    )
    assert again.exit_code != 0


def test_malformed_duplicate_nonfinite_and_blank_lines_are_rejected(tmp_path: Path) -> None:
    cases = [
        b'{"type":"a","type":"b"}\n',
        b'{"type":"turn.completed","usage":{"input_tokens":NaN,"output_tokens":1}}\n',
        b"{not-json}\n",
        b"\n",
    ]
    for index, body in enumerate(cases):
        trace = tmp_path / f"bad-{index}.jsonl"
        trace.write_bytes(body)
        result = CliRunner().invoke(
            cli,
            [
                "adapter",
                "codex-jsonl",
                str(trace),
                "--codex-version",
                "1",
                "--output",
                str(tmp_path / f"out-{index}.json"),
            ],
        )
        assert result.exit_code != 0


def test_negative_and_boolean_usage_are_not_treated_as_tokens(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace(
        trace, [{"type": "turn.completed", "usage": {"input_tokens": True, "output_tokens": -1}}]
    )
    result = translate(trace, "1")
    assert result["status"] == "partial"
    assert result["payload"]["usage"]["events"] == 0
