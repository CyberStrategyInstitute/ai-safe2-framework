"""JUnit import must count evidence and reject ambiguous success representations."""

import json

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.junit import import_junit
from safe2.evidence.test_result import evaluate_test_report


def convert(xml, exit_code=0):
    return import_junit(xml.encode(), task_id="t", revision="r", environment="e", exit_code=exit_code)


def test_counts_come_from_cases():
    report = convert('<testsuites><testsuite tests="4" failures="1" errors="1" skipped="1">'
        '<testcase name="pass"/><testcase name="fail"><failure>private text</failure></testcase>'
        '<testcase name="error"><error/></testcase><testcase name="skip"><skipped/></testcase>'
        '</testsuite></testsuites>', exit_code=1)
    assert report["counts"] == {"total": 4, "passed": 1, "failed": 1, "errors": 1, "skipped": 1}
    assert "private text" not in json.dumps(report)
    assert validate_artifact("test-result-v1", report) == []
    assert evaluate_test_report(json.dumps(report).encode(), task_id="t", revision="r", environment="e")[0] == "contradicted"


def test_nested_suite_totals_not_double_counted():
    report = convert('<testsuites tests="1"><testsuite tests="1"><testsuite tests="1">'
                     '<testcase name="one"/></testsuite></testsuite></testsuites>')
    assert report["counts"]["total"] == 1


@pytest.mark.parametrize("xml", [
    '<testsuite tests="1"/>',
    '<testsuite><testcase name="one"><failure/><error/></testcase></testsuite>',
    '<testsuite><testcase name="one"/><testcase name="one"/></testsuite>',
    '<testsuite><testcase name="one" status="notrun"/></testsuite>',
    '<testsuite><testcase name="one"><rerunFailure/></testcase></testsuite>',
    '<testsuite disabled="1"><testcase name="one"/></testsuite>',
    '<testsuite><testcase/></testsuite>',
    '<testsuite><properties><testcase name="hidden"/></properties></testsuite>',
    '<testsuite><system-out><testcase name="hidden"/></system-out></testsuite>',
    '<testsuite failures="-1"/>',
    '<testsuite tests="999999999999999999999999999999999"/>',
    '<other/>', 'not XML',
    '<!DOCTYPE testsuite [<!ENTITY x "expanded">]><testsuite>&x;</testsuite>',
])
def test_unsupported_ambiguous_reports_rejected(xml):
    with pytest.raises(ValueError):
        convert(xml)


def test_empty_and_skips_do_not_become_verified_pass():
    for xml in ['<testsuite/>', '<testsuite><testcase name="skip"><skipped/></testcase></testsuite>']:
        report = convert(xml)
        assert evaluate_test_report(json.dumps(report).encode(), task_id="t", revision="r", environment="e")[0] == "unverifiable"


def test_size_and_encoding_bounds():
    with pytest.raises(ValueError):
        convert("x" * 1_000_001)
    with pytest.raises(ValueError):
        import_junit('<testsuite/>'.encode('utf-16'), task_id="t", revision="r", environment="e", exit_code=0)


def test_depth_bound():
    with pytest.raises(ValueError):
        convert('<testsuite>' * 34 + '</testsuite>' * 34)


def test_cli_import_success_not_test_success(tmp_path):
    source = tmp_path / "junit.xml"
    source.write_text('<testsuite><testcase name="bad"><failure/></testcase></testsuite>', encoding="utf-8")
    output = tmp_path / "result.json"
    args = ["feedback", "import-junit", str(source), "--task-id", "t", "--revision", "r",
            "--environment", "e", "--exit-code", "1", "--output", str(output)]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    assert json.loads(result.output)["counts"]["failed"] == 1
    original = output.read_bytes()
    assert runner.invoke(cli, args).exit_code != 0
    assert output.read_bytes() == original
