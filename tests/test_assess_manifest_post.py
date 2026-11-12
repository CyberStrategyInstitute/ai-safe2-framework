"""`--post` against a loopback stub shaped like the hosted MCP endpoint."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from assess_manifest_support import (
    TARVIN_KEY,
    SUCCESS,
    StubServer,
    build_golden_project,
    bundle_text,
    init_project,
    isolate_home,
)
from click.testing import CliRunner

from safe2.cli import cli
from safe2.manifest import post as post_module
from safe2.manifest.post import PostError, build_body, post_manifest

ARGS = ["--manifest", "--scan-content", "--inspect-config", "--no-wsl", "--post"]


@pytest.fixture(autouse=True)
def direct_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep proxies out of the way so the stub is reached directly."""
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    isolate_home(monkeypatch, tmp_path / "home")
    root = tmp_path / "project"
    build_golden_project(root)
    init_project(root)
    monkeypatch.setenv("SAFE2_MCP_PRO_KEY", TARVIN_KEY)
    return root


def run(project: Path, tmp_path: Path, stub: StubServer, monkeypatch, *extra: str):
    monkeypatch.setattr(post_module, "ENDPOINT", stub.url)
    out = tmp_path / "bundle"
    result = CliRunner().invoke(cli, ["assess", str(project), *ARGS, *extra, "--output-dir", str(out)])
    return result, out


def assert_key_nowhere(result, out: Path) -> None:
    everything = result.output + bundle_text(out)
    assert TARVIN_KEY not in everything and "SENTINELTARVINKEY" not in everything


def test_success_posts_one_request_with_the_documented_shape(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.reply_success(SUCCESS)
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 0, result.output
    assert len(stub.requests) == 1  # one POST, no initialize, no session
    request = stub.requests[0]
    assert request["path"] == "/pro/mcp"
    assert request["headers"]["authorization"] == f"Bearer {TARVIN_KEY}"
    assert request["headers"]["content-type"] == "application/json"
    assert "mcp-session-id" not in request["headers"]
    message = json.loads(request["body"])
    assert message["jsonrpc"] == "2.0" and message["method"] == "tools/call"
    assert message["params"]["name"] == post_module.TOOL_NAME
    manifest = json.loads((out / "aisafe2-project-manifest-1.json").read_text(encoding="utf-8"))
    assert message["params"]["arguments"] == {"manifest": manifest}
    assert manifest["generator"]["name"] == "safe2 assess --manifest"
    assert "ACT tier: ACT-4" in result.output
    assert "Missing controls: 2" in result.output and "MCP-4" in result.output and "CP.9" in result.output
    assert "Snapshot: snap_abc123" in result.output
    assert "UNSIGNED" in result.output and "signed: false" in result.output
    assert_key_nowhere(result, out)


def test_success_in_json_format_carries_the_structured_summary(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.reply_success(SUCCESS)
        result, out = run(project, tmp_path, stub, monkeypatch, "--format", "json")
    payload = json.loads(result.output)
    assert payload["post"]["status"] == "ok" and payload["post"]["sent"] is True
    assert payload["post"]["result"]["snapshot_id"] == "snap_abc123"
    assert "UNSIGNED" in payload["post"]["unsigned_notice"]
    assert_key_nowhere(result, out)


def test_server_sent_events_framing_is_understood(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.content_type = "text/event-stream"
        envelope = {"jsonrpc": "2.0", "id": 1, "result": {"structuredContent": SUCCESS, "isError": False, "content": []}}
        stub.body = f"event: message\ndata: {json.dumps(envelope)}\n\n".encode()
        result, _ = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 0, result.output
    assert "Snapshot: snap_abc123" in result.output


def test_server_access_required_prints_the_url_exits_nonzero_and_does_not_retry(
    project: Path, tmp_path: Path, monkeypatch
) -> None:
    with StubServer() as stub:
        stub.reply_error(
            "pro_required",
            "Tarvin access is required.",
            upgrade_url="https://mcp.agency-check.app/account",
        )
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1
    assert "Tarvin access is required" in result.output
    assert "Upgrade: https://mcp.agency-check.app/account" in result.output
    assert len(stub.requests) == 1
    assert (out / "aisafe2-project-manifest-1.json").is_file()  # the local manifest is kept
    assert_key_nowhere(result, out)


def test_invalid_manifest_prints_schema_paths_exits_nonzero_and_does_not_retry(project: Path, tmp_path: Path, monkeypatch) -> None:
    issues = [{"path": "/agents/0/mandate_configured", "message": "is required"}, {"path": "/project/name", "message": "too short"}]
    with StubServer() as stub:
        stub.reply_error("invalid_manifest", "The manifest does not match aisafe2-project-manifest/1.", issues=issues)
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1
    assert "rejected the manifest as invalid" in result.output
    assert "/agents/0/mandate_configured: is required" in result.output and "/project/name: too short" in result.output
    assert len(stub.requests) == 1
    assert_key_nowhere(result, out)


def test_not_applied_is_reported_clearly_and_is_not_a_failure(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.reply_success({**SUCCESS, "applied": False, "reason": "model_supplied_manifest_conflicts_with_cli_manifest"})
        result, _ = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 0
    assert "NOT APPLIED" in result.output and "model_supplied_manifest_conflicts_with_cli_manifest" in result.output


@pytest.mark.parametrize("status", [401, 403])
def test_rejected_key_is_reported_without_echoing_it_and_without_retry(project: Path, tmp_path: Path, monkeypatch, status: int) -> None:
    with StubServer() as stub:
        stub.status = status
        stub.body = json.dumps({"error": f"echoing {TARVIN_KEY}"}).encode()  # a hostile server may echo the key back
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1
    assert f"rejected the API key (HTTP {status})" in result.output
    assert len(stub.requests) == 1
    assert_key_nowhere(result, out)


@pytest.mark.parametrize("status", [400, 404, 429, 500, 503])
def test_other_http_errors_are_never_retried(project: Path, tmp_path: Path, monkeypatch, status: int) -> None:
    with StubServer() as stub:
        stub.status = status
        stub.body = b"{}"
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1
    assert f"HTTP status: {status}" in result.output
    assert len(stub.requests) == 1
    assert_key_nowhere(result, out)


def test_redirects_are_not_followed_so_the_key_never_travels_to_another_url(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.status = 307
        stub.headers = {"Location": stub.url.replace("/pro/mcp", "/elsewhere")}
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1
    assert len(stub.requests) == 1 and stub.requests[0]["path"] == "/pro/mcp"
    assert_key_nowhere(result, out)


def test_hostile_server_text_is_sanitized_before_printing(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.reply_error("invalid_manifest", "x", issues=[{"path": "/a\x1b[31mred", "message": "bad\x07\x00text"}])
        result, _ = run(project, tmp_path, stub, monkeypatch)
    assert "\x1b" not in result.output and "\x07" not in result.output and "\x00" not in result.output


def test_null_or_wrong_typed_response_fields_do_not_crash_the_summary(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.reply_success({**SUCCESS, "gaps": None, "name": None, "snapshot_id": 5})
        result, _ = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 0, result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "Missing controls: 0" in result.output


def test_a_garbage_response_is_a_failure_not_a_success(project: Path, tmp_path: Path, monkeypatch) -> None:
    with StubServer() as stub:
        stub.body = b"<html>not json</html>"
        result, out = run(project, tmp_path, stub, monkeypatch)
    assert result.exit_code == 1 and "bad_response" in result.output
    assert_key_nowhere(result, out)


def test_connect_errors_retry_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()  # nothing is listening now
    sleeps: list[float] = []
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    outcome = post_manifest({"manifest_version": "x"}, key=TARVIN_KEY, endpoint=f"http://127.0.0.1:{port}/pro/mcp", sleep=sleeps.append)
    assert outcome.status == "network_error" and outcome.attempts == 2
    assert sleeps == [post_module.CONNECT_RETRY_DELAY_SECONDS]
    assert TARVIN_KEY not in repr(outcome)


def test_a_request_timeout_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    calls: list[int] = []

    def slow(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ReadTimeout("slow", request=request)

    outcome = post_manifest(
        {"manifest_version": "x"}, key=TARVIN_KEY, endpoint="https://example.test/pro/mcp",
        transport=httpx.MockTransport(slow), sleep=lambda _: None,
    )
    assert outcome.status == "network_error" and outcome.attempts == 1 and len(calls) == 1


def test_plain_http_to_a_non_loopback_host_is_refused_before_any_request() -> None:
    with pytest.raises(PostError, match="https"):
        post_manifest({"manifest_version": "x"}, key=TARVIN_KEY, endpoint="http://example.com/pro/mcp")


def test_an_oversized_request_is_refused_locally() -> None:
    with pytest.raises(PostError, match="accepts at most"):
        build_body({"filler": "a" * 1_100_000})


def test_the_default_endpoint_is_the_hosted_https_url() -> None:
    assert post_module.ENDPOINT == "https://mcp.agency-check.app/pro/mcp"
    assert post_module.KEY_ENV == "SAFE2_MCP_PRO_KEY"
