"""Real small pytest runs and fresh-report anti-staleness checks."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from safe2.challenge.integrity import canonical_bytes
from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence import pytest_capture


def run(tmp_path):
    return pytest_capture.capture_pytest(python=Path(sys.executable), cwd=tmp_path,
        targets=("test_specimen.py",), task_id="t", revision="r", environment="e", call_id="c")


@pytest.mark.parametrize("source,status", [
    ("def test_ok():\n    assert True\n", "supported"),
    ("def test_fail():\n    assert False\n", "contradicted"),
    ("import pytest\ndef test_skip():\n    pytest.skip('synthetic')\n", "unverifiable"),
    ("# no tests\n", "contradicted"),  # pytest exit 5 remains failure evidence.
])
def test_live_runner(source, status, tmp_path):
    (tmp_path / "test_specimen.py").write_text(source, encoding="utf-8")
    result = run(tmp_path)
    assert result["all_tests_passed_claim"]["status"] == status
    assert result["completion_verified"] is False
    assert result["process_sha256"] == hashlib.sha256(canonical_bytes(result["process_report"])).hexdigest()
    assert result["test_report_sha256"] == hashlib.sha256(canonical_bytes(result["test_report"])).hexdigest()
    assert result["test_report"]["exit_code"] == result["process_report"]["process_observation"]["process_exit_code"]
    assert validate_artifact("pytest-capture-v1", result) == []
    checked = pytest_capture.verify_pytest_capture(result)
    assert checked["internally_consistent"] is True
    assert checked["all_tests_passed_claim"]["status"] == status


def fake_process(status="completed", code=0):
    return {"schema_version": "safe2.tool-result.v1", "task_id": "t", "revision": "r",
            "environment": "e", "source_ref": "synthetic", "call_id": "c", "tool": "pytest",
            "outcome": ("unknown" if status != "completed" else "succeeded" if code == 0 else "failed"), "process_observation": {
                "collector": "safe2.local-process.v1", "capture_status": status,
                "process_exit_code": code, "duration_ms": 1, "command_sha256": "0" * 64,
                "stdout_sha256": "0" * 64, "stderr_sha256": "0" * 64,
                "output_complete": status == "completed", "raw_output_retained": False}}


def test_old_report_not_reused(tmp_path, monkeypatch):
    (tmp_path / "test_specimen.py").write_text("# fixture", encoding="utf-8")
    (tmp_path / "results.xml").write_text('<testsuite><testcase name="old"/></testsuite>', encoding="utf-8")
    monkeypatch.setattr(pytest_capture, "capture_process", lambda *a, **kw: fake_process())
    result = run(tmp_path)
    assert result["test_report"] is None
    assert result["all_tests_passed_claim"]["reason"] == "fresh_junit_missing_or_invalid"
    assert pytest_capture.verify_pytest_capture(result)["internally_consistent"] is True


def test_incomplete_process_does_not_promote_xml(tmp_path, monkeypatch):
    (tmp_path / "test_specimen.py").write_text("# fixture", encoding="utf-8")
    def incomplete(command, **kwargs):
        Path(command[-1].split("=", 1)[1]).write_text('<testsuite><testcase name="ok"/></testsuite>', encoding="utf-8")
        return fake_process("output_limit")
    monkeypatch.setattr(pytest_capture, "capture_process", incomplete)
    result = run(tmp_path)
    assert result["test_report"] is None
    assert result["all_tests_passed_claim"]["reason"] == "process_capture_incomplete"
    assert pytest_capture.verify_pytest_capture(result)["internally_consistent"] is True


def test_report_uses_observed_exit_not_claimed_success(tmp_path, monkeypatch):
    (tmp_path / "test_specimen.py").write_text("# fixture", encoding="utf-8")
    paths = []
    def produce(command, **kwargs):
        target = Path(command[-1].split("=", 1)[1])
        paths.append(target)
        assert not target.exists()
        target.write_text('<testsuite><testcase name="ok"/></testsuite>', encoding="utf-8")
        return fake_process(code=1)
    monkeypatch.setattr(pytest_capture, "capture_process", produce)
    first, second = run(tmp_path), run(tmp_path)
    assert first["test_report"]["exit_code"] == second["test_report"]["exit_code"] == 1
    assert first["all_tests_passed_claim"]["status"] == "contradicted"
    assert paths[0] != paths[1]
    assert all(not path.exists() for path in paths)


def test_existing_cli_output_prevents_execution(tmp_path, monkeypatch):
    def forbidden(**kwargs):
        pytest.fail("Existing output must prevent execution")
    monkeypatch.setattr(pytest_capture, "capture_pytest", forbidden)
    output = tmp_path / "capture.json"
    output.write_text("existing", encoding="utf-8")
    result = CliRunner().invoke(cli, ["feedback", "capture-pytest", "--execute", "--python", sys.executable,
        "--cwd", str(tmp_path), "--task-id", "t", "--revision", "r", "--environment", "e",
        "--call-id", "c", "--output", str(output), "test_specimen.py"])
    assert result.exit_code != 0
    assert output.read_text() == "existing"


def test_outside_target_rejected(tmp_path):
    with pytest.raises(ValueError):
        pytest_capture.capture_pytest(python=Path(sys.executable), cwd=tmp_path, targets=("../",),
            task_id="t", revision="r", environment="e", call_id="c")


@pytest.fixture
def capture(tmp_path, monkeypatch):
    (tmp_path / "test_specimen.py").write_text("# fixture", encoding="utf-8")
    def produce(command, **kwargs):
        Path(command[-1].split("=", 1)[1]).write_text('<testsuite><testcase name="ok"/></testsuite>', encoding="utf-8")
        return fake_process()
    monkeypatch.setattr(pytest_capture, "capture_process", produce)
    return run(tmp_path)


@pytest.mark.parametrize("change,reason", [
    ("digest", "capture_digest_mismatch"),
    ("claim", "capture_claim_mismatch"),
    ("exit", "capture_report_binding_mismatch"),
    ("task", "capture_report_binding_mismatch"),
    ("tool", "capture_process_missing_or_wrong_tool"),
    ("observation", "capture_process_inconsistent"),
    ("provenance", "capture_report_binding_mismatch"),
])
def test_verifier_rejects_inconsistency(capture, change, reason):
    if change == "digest":
        capture["test_report_sha256"] = "0" * 64
    elif change == "claim":
        capture["all_tests_passed_claim"]["status"] = "contradicted"
    elif change == "exit":
        capture["test_report"]["exit_code"] = 1
    elif change == "task":
        capture["test_report"]["task_id"] = "other"
    elif change == "tool":
        capture["process_report"]["tool"] = "other"
    elif change == "observation":
        capture["process_report"]["outcome"] = "failed"
    else:
        del capture["test_report"]["import_provenance"]
    if change != "digest":
        for key in ("process", "test"):
            digest_key = "process_sha256" if key == "process" else "test_report_sha256"
            capture[digest_key] = hashlib.sha256(
                canonical_bytes(capture[f"{key}_report"])).hexdigest()
    result = pytest_capture.verify_pytest_capture(capture)
    assert result["internally_consistent"] is False
    assert result["reason"] == reason


def test_verify_cli_read_only_and_exit_semantics(capture, tmp_path):
    source = tmp_path / "capture.json"
    source.write_text(json.dumps(capture), encoding="utf-8")
    result = CliRunner().invoke(cli, ["feedback", "verify-pytest", str(source)])
    assert result.exit_code == 0
    assert json.loads(result.output)["execution_verified"] is False
    capture["all_tests_passed_claim"]["status"] = "contradicted"
    source.write_text(json.dumps(capture), encoding="utf-8")
    assert CliRunner().invoke(cli, ["feedback", "verify-pytest", str(source)]).exit_code == 1


@pytest.mark.parametrize("invalid", [None, [], {}, {"schema_version": "wrong"}])
def test_invalid_capture_fails_closed(invalid):
    assert pytest_capture.verify_pytest_capture(invalid)["internally_consistent"] is False


def test_consistent_failure_is_not_passing_gate(capture, tmp_path):
    capture["test_report"]["counts"].update(passed=0, failed=1)
    capture["test_report_sha256"] = hashlib.sha256(canonical_bytes(capture["test_report"])).hexdigest()
    capture["all_tests_passed_claim"] = {"status": "contradicted", "reason": "test_report_records_failure"}
    source = tmp_path / "failed.json"
    source.write_text(json.dumps(capture), encoding="utf-8")
    checked = CliRunner().invoke(cli, ["feedback", "verify-pytest", str(source)])
    assert checked.exit_code == 0
    assert json.loads(checked.output)["all_tests_passed_claim"]["status"] == "contradicted"
