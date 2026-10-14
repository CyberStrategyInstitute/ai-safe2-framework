"""Behavioral regressions for the supplied GitHub CodeQL alert collection."""

import importlib.util
import asyncio
import json
import logging
import re
from pathlib import Path
import sys
from unittest.mock import AsyncMock, Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hermes(monkeypatch, tmp_path):
    directory = ROOT / "examples/hermes-sovereign-runtime/gateway"
    monkeypatch.syspath_prepend(str(directory))
    monkeypatch.delitem(sys.modules, "provider_adapters", raising=False)
    module = load_module("hermes_alert_tests", "examples/hermes-sovereign-runtime/gateway/gateway.py")
    monkeypatch.setattr(module, "AUDIT_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(module, "is_kill_switch_active", lambda: False)
    return module


@pytest.fixture
def openclaw(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples/openclaw/gateway"))
    monkeypatch.delitem(sys.modules, "provider_adapters", raising=False)
    return load_module("openclaw_alert_tests", "examples/openclaw/gateway/gateway.py")


def test_hermes_upstream_exception_is_private(hermes, monkeypatch, caplog):
    sentinel = "password=sentinel-secret\nFORGED"
    forward = Mock(side_effect=hermes.requests.exceptions.ConnectionError(sentinel))
    monkeypatch.setattr(hermes.requests, "request", forward)
    with caplog.at_level(logging.ERROR):
        response = hermes.app.test_client().post("/v1/messages", json={"messages": []})
    assert response.status_code == 502
    assert "sentinel-secret" not in response.get_data(as_text=True)
    assert "sentinel-secret" not in caplog.text


@pytest.mark.parametrize("route", ["/v1/messages", "/v1/chat/completions"])
def test_hermes_supported_routes_do_not_follow_redirects(hermes, monkeypatch, route):
    upstream = Mock(status_code=200, headers={}, content=b'{"ok":true}')
    forward = Mock(return_value=upstream)
    monkeypatch.setattr(hermes.requests, "request", forward)
    response = hermes.app.test_client().post(route, json={"messages": []})
    assert response.status_code == 200
    assert forward.call_args.kwargs["allow_redirects"] is False
    assert forward.call_args.kwargs["url"] == "https://api.anthropic.com/v1/messages"


def test_hermes_invalid_provider_configuration_does_not_fallback(hermes, monkeypatch):
    monkeypatch.setattr(hermes, "CONFIG", {"provider": {"base_url": "https://user:secret@host"}})
    forward = Mock()
    monkeypatch.setattr(hermes.requests, "request", forward)
    response = hermes.app.test_client().post("/v1/messages", json={"messages": []})
    assert response.status_code == 500
    forward.assert_not_called()
    assert "secret" not in response.get_data(as_text=True)


def test_provider_paths_and_operator_local_destinations(monkeypatch):
    adapter = load_module("hermes_provider_tests", "examples/hermes-sovereign-runtime/gateway/provider_adapters.py")
    for path in ["//evil.test", "/v1/messages?target=x", "/arbitrary", "/v1/messages%2f.."]:
        with pytest.raises(ValueError):
            adapter.get_upstream_url(path, {})
    for base in ["file:///etc", "https://user:secret@host", "https://host/?x=y", "https://host/#x", "https://host\n"]:
        with pytest.raises(ValueError):
            adapter.get_upstream_url("/v1/messages", {"provider": {"base_url": base}})
    assert adapter.get_upstream_url("/v1/messages", {"provider": {"active": "ollama"}}) == "http://localhost:11434/api/chat"
    assert adapter.get_upstream_url("/v1/messages", {"provider": {"active": "openai", "base_url": "https://self-hosted.test/prefix/"}}) == "https://self-hosted.test/prefix/v1/chat/completions"


def test_hermes_kill_reason_is_single_line_log_and_original_audit(hermes, monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(hermes, "CONFIG", {"gateway": {"kill_switch_file": str(tmp_path / "kill")}})
    reason = "operator\r\nFORGED\x1b[31m\u2028entry"
    with caplog.at_level(logging.CRITICAL):
        hermes.activate_kill_switch(reason)
    message = caplog.records[-1].getMessage()
    assert "\n" not in message and "\r" not in message and "\x1b" not in message and "\u2028" not in message
    assert json.loads(hermes.AUDIT_PATH.read_text())["reason"] == reason


def test_openclaw_heartbeat_and_safe_mode_public_details(openclaw, monkeypatch):
    sentinel = "password=sentinel-secret\nFORGED"
    monkeypatch.setattr(openclaw, "_heartbeat_monitor", Mock(validate=Mock(return_value=(False, sentinel))))
    monkeypatch.setattr(openclaw, "_audit_log", Mock(verify_chain=Mock(return_value=(False, 2, sentinel))))
    client = openclaw.app.test_client()
    assert "sentinel-secret" not in client.get("/health").get_data(as_text=True)
    assert "sentinel-secret" not in client.get("/audit/verify-chain").get_data(as_text=True)
    monkeypatch.setattr(openclaw, "_safe_mode_reason", sentinel)
    with openclaw.app.test_request_context():
        response, status = openclaw._safe_mode_response()
    assert status == 503 and "sentinel-secret" not in response.get_data(as_text=True)


def test_openclaw_audit_error_does_not_include_file_contents(openclaw, tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = openclaw.ImmutableAuditLog(path, "test-key")
    path.write_text("not-json password=sentinel-secret")
    valid, count, detail = audit.verify_chain()
    assert valid is False and count == 0
    assert "sentinel-secret" not in detail
    assert "Expecting value" not in detail


def test_openclaw_log_identity_is_single_line_and_audit_retains_it(openclaw, tmp_path, caplog):
    audit = openclaw.ImmutableAuditLog(tmp_path / "audit.jsonl", "test-key")
    identity = "user\nFORGED\r\x1b[31m\u2028line"
    with caplog.at_level(logging.INFO):
        audit.append(user_id=identity, request_hash="abc", risk_score=0, risk_vectors={}, hitl_tier="AUTO", blocked=False, reason=None)
    message = caplog.records[-1].getMessage()
    assert all(char not in message for char in ["\n", "\r", "\x1b", "\u2028"])
    assert json.loads(audit.log_path.read_text())["user_id"] == identity


def test_scanner_reports_do_not_reflect_secret_configuration(tmp_path, capsys):
    scanner_module = load_module("scanner_alert_tests", "examples/openclaw/scanner.py")
    (tmp_path / "openclaw.json").write_text(json.dumps({"logging": {"redactSensitive": "sentinel-secret"}, "tools": {"exec": {"enabled": "sentinel-secret"}}, "api_key": "sk-sentinel-secret"}))
    scanner = scanner_module.OpenClawScanner(str(tmp_path))
    scanner._check_configuration()
    scanner._check_logging_config()
    scanner._check_tool_permissions()
    report = scanner._generate_report()
    assert "sentinel-secret" not in capsys.readouterr().out
    assert "sentinel-secret" not in json.dumps(report)
    assert report["findings"]["critical"]


def test_hermes_filter_settings_do_not_reflect_arbitrary_values(hermes):
    assert hermes._filter_setting(True) == "enabled"
    assert hermes._filter_setting(False) == "disabled"
    assert hermes._filter_setting(None) == "unknown"
    assert hermes._filter_setting("password=sentinel-secret") == "unknown"


def test_nexus_tool_log_is_single_line_and_receipt_preserved(monkeypatch, caplog):
    monkeypatch.syspath_prepend(str(ROOT / "NEXUS/sdk/python"))
    monkeypatch.syspath_prepend(str(ROOT / "NEXUS/docker/gateway"))
    nexus = load_module("nexus_gateway_alert_tests", "NEXUS/docker/gateway/gateway.py")
    identity = "did:agent\r\nFORGED"
    tool = "read_file\x1b[31m\u2028FORGED"
    receipt = Mock(receipt_id="receipt", receipt_hash="hash", timestamp="time")
    verdict = Mock(decision="allow", reasoning="allowed", nor_fingerprint="fingerprint")
    monkeypatch.setattr(nexus, "_guardian", Mock(evaluate=Mock(return_value=verdict)))
    exporter = Mock()
    monkeypatch.setattr(nexus, "_nor_exporter", exporter)
    monkeypatch.setattr(nexus, "build_tool_call_step", Mock(return_value=Mock(step_id="step")))
    monkeypatch.setattr(nexus, "build_tool_call_nor", Mock(return_value=receipt))
    monkeypatch.setattr(nexus, "nor_to_otel_attributes", Mock(return_value={"ocsf.class_uid": 6002}))
    request = Mock(json=AsyncMock(return_value={"agent_did": identity, "tool_name": tool}))
    with caplog.at_level(logging.INFO):
        result = asyncio.run(nexus.evaluate_tool_call(request))
    assert result["decision"] == "allow" and result["nor_receipt"]["receipt_id"] == "receipt"
    exporter.export.assert_called_once_with(receipt)
    message = caplog.records[-1].getMessage()
    assert all(char not in message for char in ["\n", "\r", "\x1b", "\u2028"])
    encoded_tool = re.search(r'tool=("(?:[^"\\]|\\.)*")', message).group(1)
    assert json.loads(encoded_tool) == tool


def test_openclaw_provider_error_keeps_status_without_exception_detail(openclaw, monkeypatch, caplog):
    sentinel = "password=sentinel-secret\nFORGED"
    monkeypatch.setattr(openclaw, "_ADAPTERS_AVAILABLE", True)
    monkeypatch.setattr(openclaw, "get_adapter", Mock(side_effect=ValueError(sentinel)))
    monkeypatch.setattr(openclaw, "calculate_composite_risk", Mock(return_value=(0, {}, False, False)))
    monkeypatch.setattr(openclaw, "_hitl", Mock(tier_for_score=Mock(return_value=openclaw.HITLTier.AUTO), enforce=Mock(return_value=None)))
    monkeypatch.setattr(openclaw, "_audit_log", Mock())
    with caplog.at_level(logging.WARNING):
        response = openclaw.app.test_client().post("/v1/messages", json={"messages": []})
    assert response.status_code == 500
    assert "sentinel-secret" not in response.get_data(as_text=True)
    assert "sentinel-secret" not in caplog.text


def test_openclaw_hitl_logs_preserve_approval_without_control_characters(openclaw, caplog):
    circuit = openclaw.HITLCircuitBreaker({}, openclaw.ChallengeStore())
    identity = "user\nFORGED\x1b[31m"
    token = circuit._issue_token(identity)
    with caplog.at_level(logging.WARNING):
        result = circuit.enforce(tier=openclaw.HITLTier.HIGH, request_hash="hash", user_id=identity,
                                 risk_score=7.5, req_headers={"X-HITL-Token": token,
                                 "X-HITL-Reason": "Authorized test reason\nFORGED"})
    assert result is None
    assert all(char not in caplog.records[-1].getMessage() for char in ["\n", "\r", "\x1b"])


ENCODER_COPIES = [
    "examples/openclaw/gateway/safe2_log_fields.py",
    "examples/hermes-sovereign-runtime/gateway/safe2_log_fields.py",
    "NEXUS/docker/gateway/safe2_log_fields.py",
]


def test_log_field_encoder_copies_are_identical():
    # The CodeQL barrier model trusts every copy, so they must stay byte-identical.
    contents = {path: (ROOT / path).read_bytes() for path in ENCODER_COPIES}
    assert len(set(contents.values())) == 1, sorted(contents)


@pytest.mark.parametrize("hostile", [
    "a\nFORGED", "a\r\nFORGED", "a\x85FORGED", "a\u2028FORGED", "a\u2029FORGED",
    "a\x1b[31mFORGED", "a\x00FORGED", "caf\u00e9",
])
def test_log_field_encoder_is_single_line_ascii_and_reversible(hostile):
    encoder = load_module("safe2_log_fields_tests", ENCODER_COPIES[0])
    encoded = encoder.encode_log_field(hostile)
    assert encoded.isascii() and encoded.isprintable()
    assert json.loads(encoded) == hostile


def test_log_field_encoder_bounds_length():
    encoder = load_module("safe2_log_fields_bound_tests", ENCODER_COPIES[0])
    encoded = json.loads(encoder.encode_log_field("x" * 10_000))
    assert encoded == "x" * encoder.MAX_LOG_FIELD_CHARS + "...[truncated]"


def test_openclaw_chain_break_location_reaches_operator_log_not_response(openclaw, monkeypatch, tmp_path, caplog):
    audit = openclaw.ImmutableAuditLog(tmp_path / "audit.jsonl", "test-key")
    for score in (1, 2):
        audit.append(user_id="u", request_hash="h", risk_score=score, risk_vectors={}, hitl_tier="AUTO", blocked=False, reason=None)
    lines = audit.log_path.read_text().splitlines()
    tampered = json.loads(lines[1])
    tampered["risk_score"] = 0
    audit.log_path.write_text(lines[0] + "\n" + json.dumps(tampered) + "\n")
    monkeypatch.setattr(openclaw, "_audit_log", audit)
    with caplog.at_level(logging.CRITICAL):
        body = openclaw.app.test_client().get("/audit/verify-chain").get_json()
    assert body["chain_valid"] is False and body["detail"] == "Audit chain validation failed"
    assert "seq=" in caplog.records[-1].getMessage()
