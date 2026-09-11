"""Live harmless child processes plus adversarial capture/receipt boundary checks."""

import hashlib
import io
import json
import sys
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from safe2.bounded_process import BoundedResult, run_bounded
from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence import process_capture
from safe2.evidence.tool_result import evaluate_tool_report


def capture(tmp_path, script="print('hello')", **kwargs):
    return process_capture.capture_process((sys.executable, "-I", "-c", script), cwd=tmp_path,
        task_id="t1", revision="r1", environment="local", call_id="c1", tool="python", **kwargs)


def test_live_success_observed_not_test_success(tmp_path):
    report = capture(tmp_path)
    assert report["outcome"] == "succeeded"
    assert report["process_observation"]["process_exit_code"] == 0
    assert report["process_observation"]["output_complete"] is True
    assert report["process_observation"]["raw_output_retained"] is False
    assert "hello" not in json.dumps(report)
    assert validate_artifact("tool-result-v1", report) == []


def test_live_nonzero_is_not_success(tmp_path):
    report = capture(tmp_path, "raise SystemExit(3)")
    assert report["outcome"] == "failed"
    assert report["process_observation"]["process_exit_code"] == 3


def test_live_timeout_is_failed_attempt(tmp_path):
    report = capture(tmp_path, "import time; time.sleep(3)", timeout=1)
    assert report["outcome"] == "failed"
    assert report["process_observation"]["capture_status"] == "timeout"
    assert report["process_observation"]["stdout_sha256"] is None


def test_live_output_limit_is_unknown(tmp_path):
    report = capture(tmp_path, "print('x' * 100000)", max_bytes=100)
    assert report["outcome"] == "unknown"
    assert report["process_observation"]["capture_status"] == "output_limit"
    assert report["process_observation"]["output_complete"] is False


def test_live_environment_secret_not_forwarded(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFE2_TEST_SECRET", "synthetic-value")
    report = capture(tmp_path, "import os,sys; sys.stdout.write(os.getenv('SAFE2_TEST_SECRET','absent'))")
    assert report["process_observation"]["stdout_sha256"] == hashlib.sha256(b"absent").hexdigest()


def test_live_missing_executable_reports_unavailable(tmp_path):
    report = process_capture.capture_process((str(tmp_path / "absent.exe"),), cwd=tmp_path,
        task_id="t1", revision="r1", environment="local", call_id="c1", tool="missing")
    assert report["outcome"] == "unavailable"


def test_incomplete_pipe_drain_is_not_success(tmp_path, monkeypatch):
    monkeypatch.setattr(process_capture, "run_bounded", lambda *a, **kw: BoundedResult(0, b"", b"", False, False))
    report = capture(tmp_path)
    assert report["outcome"] == "unknown"
    assert report["process_observation"]["capture_status"] == "drain_incomplete"


def test_reader_error_is_not_complete_capture(monkeypatch):
    class BrokenStream:
        def read(self, size):
            raise OSError("synthetic pipe error")
    process = SimpleNamespace(stdout=BrokenStream(), stderr=io.BytesIO(), returncode=0,
                              wait=lambda **kw: None, kill=lambda: None)
    monkeypatch.setattr("safe2.bounded_process.subprocess.Popen", lambda *a, **kw: process)
    assert run_bounded(["unused"], timeout=1, max_bytes=100).output_complete is False


def test_invalid_identifiers_never_execute(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Must validate before launching")
    monkeypatch.setattr(process_capture, "run_bounded", forbidden)
    with pytest.raises(ValueError):
        process_capture.capture_process((sys.executable,), cwd=tmp_path, task_id="bad id",
            revision="r", environment="env", call_id="c", tool="t")


@pytest.mark.parametrize("command", [(), ("python",)])
def test_explicit_executable_required(tmp_path, command):
    with pytest.raises(ValueError):
        process_capture.capture_process(command, cwd=tmp_path, task_id="t",
            revision="r", environment="env", call_id="c", tool="t")


def arguments(tmp_path):
    return ["feedback", "capture-process", "--execute", "--cwd", str(tmp_path),
            "--task-id", "t1", "--revision", "r1", "--environment", "local", "--call-id", "c1",
            "--tool", "python", "--output", str(tmp_path / "capture.json"), "--",
            sys.executable, "-I", "-c", "raise SystemExit(3)"]


def test_cli_failure_keeps_report_and_nonzero_exit(tmp_path):
    result = CliRunner().invoke(cli, arguments(tmp_path))
    assert result.exit_code == 1
    assert json.loads(result.output)["outcome"] == "failed"
    assert json.loads((tmp_path / "capture.json").read_text())["process_observation"]["process_exit_code"] == 3


def test_existing_output_prevents_execution(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Existing output must prevent launch")
    monkeypatch.setattr(process_capture, "capture_process", forbidden)
    output = tmp_path / "capture.json"
    output.write_bytes(b"existing")
    assert CliRunner().invoke(cli, arguments(tmp_path)).exit_code != 0
    assert output.read_bytes() == b"existing"


def test_explicit_execute_flag_required(tmp_path):
    args = arguments(tmp_path)
    args.remove("--execute")
    assert CliRunner().invoke(cli, args).exit_code != 0
    assert not (tmp_path / "capture.json").exists()


def test_imported_contradictory_process_metadata_rejected(tmp_path):
    report = capture(tmp_path, "raise SystemExit(3)")
    report["outcome"] = "succeeded"
    status, reason, _ = evaluate_tool_report(json.dumps(report).encode(), task_id="t1", revision="r1",
        environment="local", call_id="c1", tool="python", claimed_outcome="succeeded")
    assert status == "unverifiable"
    assert reason == "tool_report_inconsistent_observation"
