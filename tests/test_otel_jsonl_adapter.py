from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from safe2.adapters.otel_jsonl import export_metadata, translate
from safe2.cli import cli
from safe2.contracts import validate_artifact


def attr(key: str, kind: str, value: object) -> dict:
    return {"key": key, "value": {kind: value}}


def trace_document() -> dict:
    return {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "secret-trace-id",
                                "name": "secret operation name",
                                "status": {"code": "STATUS_CODE_ERROR"},
                                "attributes": [
                                    attr("gen_ai.operation.name", "stringValue", "invoke_agent"),
                                    attr("gen_ai.provider.name", "stringValue", "openai"),
                                    attr("gen_ai.response.model", "stringValue", "model-x"),
                                    attr("gen_ai.usage.input_tokens", "intValue", "100"),
                                    attr("gen_ai.usage.output_tokens", "intValue", "25"),
                                    attr("gen_ai.input.messages", "stringValue", "TOP SECRET"),
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(value) for value in values) + "\n", encoding="utf-8")


def test_translate_otel_traces_without_content_or_identifiers(tmp_path: Path) -> None:
    source = tmp_path / "traces.jsonl"
    write_jsonl(source, [trace_document()])
    result = translate(source, "1.44.0", observed_at="2026-10-03T00:00:00Z")
    assert not validate_artifact("adapter-evidence-v1", result)
    assert result["status"] == "complete"
    assert result["payload"]["usage"] == {"spans": 1, "input_tokens": 100, "output_tokens": 25}
    rendered = json.dumps(result)
    assert "TOP SECRET" not in rendered
    assert "secret-trace-id" not in rendered
    assert "secret operation name" not in rendered


def test_invalid_token_pair_is_visible_partial_coverage(tmp_path: Path) -> None:
    document = trace_document()
    attributes = document["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
    attributes[:] = [attr("gen_ai.usage.input_tokens", "intValue", "100")]
    source = tmp_path / "partial.jsonl"
    write_jsonl(source, [document])
    result = translate(source, "1.44.0")
    assert result["status"] == "partial"
    assert result["coverage"]["gaps"] == ["invalid_or_incomplete_token_pair=1"]


def test_rejects_mixed_or_non_trace_signal_files(tmp_path: Path) -> None:
    source = tmp_path / "logs.jsonl"
    write_jsonl(source, [{"resourceLogs": []}])
    result = CliRunner().invoke(
        cli,
        [
            "adapter",
            "otel-jsonl",
            str(source),
            "--otel-version",
            "1",
            "--output",
            str(tmp_path / "out.json"),
        ],
    )
    assert result.exit_code != 0
    assert "only TracesData" in result.output


def test_rejects_duplicate_keys_nonfinite_values_and_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    for index, body in enumerate(
        [
            b'{"resourceSpans":[],"resourceSpans":[]}\n',
            b'{"resourceSpans":[],"invalid":NaN}\n',
        ]
    ):
        source = tmp_path / f"bad-{index}.jsonl"
        source.write_bytes(body)
        result = runner.invoke(
            cli,
            [
                "adapter",
                "otel-jsonl",
                str(source),
                "--otel-version",
                "1",
                "--output",
                str(tmp_path / f"bad-{index}.json"),
            ],
        )
        assert result.exit_code != 0

    source = tmp_path / "good.jsonl"
    output = tmp_path / "existing.json"
    write_jsonl(source, [trace_document()])
    output.write_text("preserve", encoding="utf-8")
    result = runner.invoke(
        cli,
        [
            "adapter",
            "otel-jsonl",
            str(source),
            "--otel-version",
            "1",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code != 0
    assert output.read_text(encoding="utf-8") == "preserve"


def test_metadata_export_excludes_claims_payload_and_provenance_path(tmp_path: Path) -> None:
    source = tmp_path / "traces.jsonl"
    write_jsonl(source, [trace_document()])
    evidence = translate(source, "1.44.0")
    evidence["payload"]["private"] = "DO NOT EXPORT"
    exported = export_metadata(evidence)
    rendered = json.dumps(exported)
    assert "DO NOT EXPORT" not in rendered
    assert source.name not in rendered
    assert evidence["provenance"]["source_sha256"] in rendered


def test_cli_import_descriptor_conformance_and_export(tmp_path: Path) -> None:
    source = tmp_path / "traces.jsonl"
    evidence = tmp_path / "evidence.json"
    definition = tmp_path / "descriptor.json"
    report = tmp_path / "report.json"
    exported = tmp_path / "export.jsonl"
    write_jsonl(source, [trace_document()])
    runner = CliRunner()
    assert (
        runner.invoke(
            cli,
            [
                "adapter",
                "otel-jsonl",
                str(source),
                "--otel-version",
                "1.44.0",
                "--output",
                str(evidence),
            ],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            cli,
            ["adapter", "otel-descriptor", "--otel-version", "1.44.0", "--output", str(definition)],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            cli, ["adapter", "conformance", str(definition), str(evidence), "--output", str(report)]
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            cli, ["adapter", "otel-export", str(evidence), "--output", str(exported)]
        ).exit_code
        == 0
    )
    exported_lines = exported.read_text(encoding="utf-8").splitlines()
    assert len(exported_lines) == 1
    assert "resourceLogs" in json.loads(exported_lines[0])
