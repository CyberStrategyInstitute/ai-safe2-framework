"""Remote Guardian failover (2026-10-06): found by the behavioral nexus-score check.

With guardian_url set and httpx not installed, _invoke_remote silently fell back to
the default inline policy, so the operator's remote policy was bypassed and
FAIL_CLOSED never engaged. A client that cannot reach its Guardian must apply its
configured fail mode.
"""
import builtins

import pytest

from nexus_sdk.guardian import GuardianVerdict, NEXUSGuardianClient, build_tool_call_step


@pytest.fixture
def no_httpx(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "httpx":
            raise ImportError("httpx not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def step():
    return build_tool_call_step("did:nexus:agent:a", "spiffe://nexus.local/a", "search", {"q": "x"}, act_tier=1)


def test_missing_http_client_fails_closed(no_httpx):
    client = NEXUSGuardianClient(guardian_url="https://guardian.example/rpc",
                                 fail_mode=NEXUSGuardianClient.FAIL_CLOSED)
    v = client.evaluate(step())
    assert v.decision == GuardianVerdict.DENY
    assert "GUARDIAN_UNAVAILABLE_FAIL_CLOSED" in v.reason_codes
    assert not client.is_available


def test_missing_http_client_honours_explicit_fail_open(no_httpx):
    client = NEXUSGuardianClient(guardian_url="https://guardian.example/rpc",
                                 fail_mode=NEXUSGuardianClient.FAIL_OPEN)
    v = client.evaluate(step())
    assert v.decision == GuardianVerdict.ALLOW
    assert "GUARDIAN_UNAVAILABLE_FAIL_OPEN" in v.reason_codes


def test_unreachable_guardian_fails_closed():
    client = NEXUSGuardianClient(guardian_url="http://127.0.0.1:9/unreachable",
                                 fail_mode=NEXUSGuardianClient.FAIL_CLOSED)
    assert client.evaluate(step()).decision == GuardianVerdict.DENY
