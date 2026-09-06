from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.evidence.nexus import CHECKS, collect, collect_runtime
from safe2.evidence.skillspector import collect as collect_skillspector


def test_nexus_static_rejects_symlink_and_bounds_expected_files(tmp_path: Path):
    first_relative = next(iter(CHECKS.values()))[0]
    external = tmp_path / "outside.rego"
    external.write_text("DO_NOT_READ", encoding="utf-8")
    linked = tmp_path / "root" / first_relative
    linked.parent.mkdir(parents=True)
    try:
        linked.symlink_to(external)
    except OSError:
        return
    result = collect(tmp_path / "root", max_file_bytes=1)
    observation = result["observations"][0]
    assert observation["status"] == "failed"
    assert observation["error_type"] == "symlink_or_outside_root"
    assert observation["sha256"] is None

    linked.unlink()
    linked.write_text("larger than one byte", encoding="utf-8")
    result = collect(tmp_path / "root", max_file_bytes=1)
    observation = result["observations"][0]
    assert observation["status"] == "failed"
    assert observation["error_type"] == "size_limit"


def test_nexus_runtime_rejects_credential_and_query_urls_without_network():
    with pytest.raises(ValueError, match="credentials or query"):
        collect_runtime("https://user:secret@example.test?n=secret")


def test_nexus_runtime_bounds_response_body(monkeypatch):
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"field":"' + b"x" * 100 + b'"}',
            request=request,
        )

    def client_factory(**kwargs):
        return real_client(
            base_url=kwargs["base_url"],
            timeout=kwargs["timeout"],
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("safe2.evidence.nexus.httpx.Client", client_factory)
    result = collect_runtime("https://nexus.example", max_response_bytes=10)
    assert result["summary"]["observed"] == 0
    assert result["summary"]["failed"] == 3
    assert all(row["response_size_limit_exceeded"] for row in result["observations"])
    assert all(row["observed_fields"] == [] for row in result["observations"])
    assert all(row["evidence_grade"] == "E0" for row in result["observations"])
    assert all(row["validation"] == "size-limit-exceeded" for row in result["observations"])


def test_skillspector_rejects_non_object_json_cleanly(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("safe2.evidence.skillspector.shutil.which", lambda _: "skillspector")
    monkeypatch.setattr(
        "safe2.evidence.skillspector.run_bounded",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=b"[]", stderr=b"", exceeded=False
        ),
    )
    target = tmp_path / "skill"
    target.mkdir()
    with pytest.raises(TypeError, match="must be an object"):
        collect_skillspector(str(target))
    result = CliRunner().invoke(cli, ["evidence", "skillspector", str(target)])
    assert result.exit_code == 1
    assert "must be an object" in result.output
    assert "Traceback" not in result.output
