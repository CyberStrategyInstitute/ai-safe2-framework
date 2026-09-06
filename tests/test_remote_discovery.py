from __future__ import annotations

import subprocess

import pytest

from safe2.discovery.posix import MAX_PROBE_BYTES, PROBE_SCRIPT, _parse_probe, probe_ssh, probe_wsl

PROBE_OUTPUT = b"""safe2-probe-v1
os\tLinux
release\t6.8.0
harness\tcodex\tcommand\t/usr/local/bin/codex
harness\tcodex\tconfiguration\t/home/test/.codex
harness\thermes\tconfiguration\t/home/test/.hermes
shell\tbash\t/usr/bin/bash
"""


def _successful_runner(command, **kwargs):
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is False
    if command[-2:] == ["sh", "-s"]:
        assert kwargs["input"] == PROBE_SCRIPT.encode("utf-8")
    else:
        assert PROBE_SCRIPT in command
    return subprocess.CompletedProcess(command, 0, stdout=PROBE_OUTPUT, stderr=b"")


def test_parse_posix_probe_groups_multiple_indicators():
    result = _parse_probe(PROBE_OUTPUT)
    assert result["status"] == "completed"
    assert result["system"] == "Linux"
    codex = next(row for row in result["harnesses"] if row["id"] == "codex")
    assert len(codex["indicators"]) == 2


def test_explicit_wsl_probe_uses_fixed_script(monkeypatch):
    monkeypatch.setattr("safe2.discovery.posix.shutil.which", lambda name: "wsl.exe")
    result = probe_wsl("Ubuntu-24.04", runner=_successful_runner)
    assert result["id"] == "wsl:Ubuntu-24.04"
    assert result["status"] == "completed"
    assert len(result["harnesses"]) == 2


def test_explicit_ssh_probe_is_noninteractive(monkeypatch):
    observed = {}

    def runner(command, **kwargs):
        observed["command"] = command
        return _successful_runner(command, **kwargs)

    monkeypatch.setattr("safe2.discovery.posix.shutil.which", lambda name: "ssh")
    result = probe_ssh("audit@example.internal", port=2222, runner=runner)
    assert result["status"] == "completed"
    assert "BatchMode=yes" in observed["command"]
    assert "StrictHostKeyChecking=yes" in observed["command"]
    assert observed["command"][observed["command"].index("--") + 1] == "audit@example.internal"
    assert observed["command"][-2:] == ["sh", "-s"]


@pytest.mark.parametrize("target", ["-oProxyCommand=bad", "host;whoami", "host name", "$(bad)"])
def test_ssh_target_rejects_shell_and_option_injection(target):
    with pytest.raises(ValueError, match="invalid SSH target"):
        probe_ssh(target)


def test_invalid_probe_is_not_reported_as_empty_success():
    result = _parse_probe(b"login banner only\n")
    assert result["status"] == "failed"
    assert result["error_type"] == "invalid_probe_response"


def test_probe_output_is_bounded_and_unknown_harnesses_are_ignored():
    oversized = _parse_probe(b"x" * (MAX_PROBE_BYTES + 1))
    assert oversized["status"] == "failed"
    assert oversized["error_type"] == "probe_output_limit"
    injected = _parse_probe(
        b"safe2-probe-v1\nharness\tunknown-agent\tcommand\t/tmp/tool\n"
    )
    assert injected["status"] == "completed"
    assert injected["harnesses"] == []
