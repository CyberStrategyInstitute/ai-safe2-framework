"""
tests/test_mcp_adapter_authz.py
NEXUS MCP adapter tool-call authorization (adapters/mcp/authz.py, adapter.py).

The table mirrors opa/nexus-authz.rego. When an OPA binary is available
(OPA_BIN, or `opa` on PATH) every row is also evaluated by the Rego and the
two decisions must agree field for field, except the three documented fail-closed
divergences (AUTHZ-DIV-1..3), which are pinned so they flip when the
policy is corrected. Without OPA the parity tests skip; they are not counted as
passing.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

NEXUS = Path(__file__).resolve().parents[3]
ADAPTER_DIR = NEXUS / "adapters" / "mcp"
POLICY = NEXUS / "opa" / "nexus-authz.rego"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ADAPTER_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


authz = _load("nexus_mcp_adapter_authz", "authz.py")
adapter = _load("nexus_mcp_adapter", "adapter.py")

BASE = {
    "agent_id": "did:web:x:clients:a",
    "tool_name": "agency_check",
    "vcc_capabilities": ["agency_check", "describe_ruleset"],
    "vcc_mandate_required": [],
    "mandate_id": None,
    "delegation_depth": 0,
    "context_compartment": "TASK_CONTEXT",
    "requested_new_capabilities": [],
    "parent_vcc_capabilities": ["agency_check", "describe_ruleset"],
    "performative": "tool_call",
    "persistence_scope": "request",
}
FAR = 4102444800 * 10**9  # 2100-01-01
DATA = {
    "mandates": {"active": {
        "mandate-ok": {"agent_id": "did:web:x:clients:a", "tools": ["agency_check"], "expires_at_ns": FAR},
        "mandate-other": {"agent_id": "did:web:x:clients:other", "tools": ["agency_check"], "expires_at_ns": FAR},
        "mandate-tool": {"agent_id": "did:web:x:clients:a", "tools": ["describe_ruleset"], "expires_at_ns": FAR},
        "mandate-old": {"agent_id": "did:web:x:clients:a", "tools": ["agency_check"], "expires_at_ns": 1},
        "mandate-bare": {},
        "mandate-noexp": {"agent_id": "did:web:x:clients:a", "tools": ["agency_check"]},
    }},
    "revocation": {"agents": {
        "did:web:x:clients:bad": {"status": "revoked"},
        "did:web:x:clients:brake": {"status": "hard_brake"},
    }},
    "approvals": {"config_change": {"did:web:x:clients:a": {"h-approved": True}}},
    "aim": {"agents": {"did:web:x:clients:t2": {"act_tier": 2}}},
}
_DROP = object()

# (name, patch, expected allow). First block: Agency Check test/authz-table.ts.
TABLE = [
    ("baseline allow", {}, True),
    ("tool not granted", {"tool_name": "get_receipt"}, False),
    ("mandate required, none", {"vcc_mandate_required": ["agency_check"]}, False),
    ("mandate required, valid", {"vcc_mandate_required": ["agency_check"], "mandate_id": "mandate-ok"}, True),
    ("depth 4 allowed", {"delegation_depth": 4}, True),
    ("depth 5 denied", {"delegation_depth": 5}, False),
    ("revoked agent", {"agent_id": "did:web:x:clients:bad"}, False),
    ("hard brake agent", {"agent_id": "did:web:x:clients:brake"}, False),
    ("bad compartment", {"context_compartment": "ROOT"}, False),
    ("credential compartment is valid", {"context_compartment": "CREDENTIAL_SURFACE"}, True),
    ("scope widening", {"requested_new_capabilities": ["credential:vault"]}, False),
    ("narrowing is fine", {"requested_new_capabilities": ["describe_ruleset"]}, True),
    ("durable memory write without mandate", {"performative": "memory_write", "persistence_scope": "durable"}, False),
    ("request-scoped memory write", {"performative": "memory_write", "persistence_scope": "request"}, True),
    ("memory_zone PERMANENT maps to durable",
     {"performative": "memory_write", "persistence_scope": _DROP, "memory_zone": "PERMANENT"}, False),
    # Upstream rules the Agency Check port predates.
    ("declared request cannot downgrade PERMANENT",
     {"performative": "memory_write", "memory_zone": "PERMANENT", "persistence_scope": "request"}, False),
    ("unknown scope label fails closed", {"performative": "memory_write", "persistence_scope": "bogus"}, False),
    ("undeclared memory write is swarm_shared", {"performative": "memory_write", "persistence_scope": _DROP}, False),
    ("durable write with valid mandate",
     {"performative": "memory_write", "memory_zone": "PERMANENT", "mandate_id": "mandate-ok"}, True),
    ("TASK_CONTEXT cannot call credential: tool",
     {"tool_name": "credential:vault", "vcc_capabilities": ["credential:vault"]}, False),
    ("CREDENTIAL_SURFACE may call credential: tool",
     {"tool_name": "credential:vault", "vcc_capabilities": ["credential:vault"],
      "context_compartment": "CREDENTIAL_SURFACE"}, True),
    ("unapproved config change", {"performative": "config_change", "change_hash": "h-other"}, False),
    ("approved config change", {"performative": "config_change", "change_hash": "h-approved"}, True),
    ("registered ACT-2 claiming ACT-3",
     {"agent_id": "did:web:x:clients:t2", "act_tier": 3}, False),
    ("registered ACT-2 claiming ACT-1 keeps ACT-2",
     {"agent_id": "did:web:x:clients:t2", "act_tier": 1}, True),
    ("missing depth denied", {"delegation_depth": _DROP}, False),
    ("missing capabilities denied", {"vcc_capabilities": _DROP}, False),
]

# Rows where this port fails closed and the current Rego allows.
DIVERGENT = [
    ("AUTHZ-DIV-1 null depth", {"delegation_depth": None}),
    ("AUTHZ-DIV-1 false depth", {"delegation_depth": False}),
    ("AUTHZ-DIV-2 config change without change_hash", {"performative": "config_change"}),
    *[(f"AUTHZ-DIV-4 mandate {m}", {"vcc_mandate_required": ["agency_check"], "mandate_id": m})
      for m in ("mandate-other", "mandate-tool", "mandate-old", "mandate-bare", "mandate-noexp")],
    ("AUTHZ-DIV-3 missing parent VCC",
     {"parent_vcc_capabilities": _DROP, "requested_new_capabilities": ["agency_check"]}),
]


def _input(patch: dict) -> dict:
    doc = dict(BASE)
    for key, value in patch.items():
        if value is _DROP:
            doc.pop(key, None)
        else:
            doc[key] = value
    return doc


def _comparable(decision: dict) -> dict:
    return {k: v for k, v in decision.items() if k != "decision_timestamp"}


class TestAuthzTable:

    @pytest.mark.parametrize("name,patch,expected", TABLE, ids=[r[0] for r in TABLE])
    def test_expected_allow(self, name, patch, expected):
        decision = authz.authorize_tool_call(_input(patch), DATA)
        assert decision["allow"] is expected
        if expected:
            assert decision["deny_reason"] == ""
        else:
            assert decision["deny_reason"], "a refusal must say why"

    @pytest.mark.parametrize("name,patch", DIVERGENT, ids=[r[0] for r in DIVERGENT])
    def test_divergences_fail_closed(self, name, patch):
        assert authz.authorize_tool_call(_input(patch), DATA)["allow"] is False

    def test_decision_shape_matches_policy(self):
        d = authz.authorize_tool_call(BASE, DATA, now_ns=1)
        assert set(d) == {
            "allow", "mandate_required", "deny_reason", "policy_version", "framework_version",
            "decision_timestamp", "agent_id", "tool_name", "delegation_depth",
            "persistence_scope", "effective_act_tier"}
        assert d["policy_version"] == "nexus-authz-v0.3-v31"
        assert d["effective_act_tier"] == 4  # no registry, no claim: most demanding tier

    def test_reasons_are_joined_and_sorted(self):
        d = authz.authorize_tool_call(_input({"tool_name": "nope", "delegation_depth": 9}), DATA)
        assert d["deny_reason"] == "delegation depth missing or above 4; tool not in VCC capabilities"

    def test_registry_required_denies_unregistered_agent(self):
        data = {**DATA, "aim": {"required": True, "agents": {}}}
        d = authz.authorize_tool_call(BASE, data)
        assert d["allow"] is False
        assert "registry required" in d["deny_reason"]


def _opa_binary() -> str | None:
    return os.environ.get("OPA_BIN") or shutil.which("opa")


def _rego(opa: str, doc: dict, tmp_path: Path) -> dict:
    (tmp_path / "input.json").write_text(json.dumps(doc))
    (tmp_path / "data.json").write_text(json.dumps({"nexus": DATA}))
    out = subprocess.run(
        [opa, "eval", "-f", "json", "-d", str(POLICY), "-d", str(tmp_path / "data.json"),
         "-i", str(tmp_path / "input.json"), "data.nexus.authz.authorize_tool_call"],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)["result"][0]["expressions"][0]["value"]


@pytest.fixture(scope="module")
def opa():
    binary = _opa_binary()
    if not binary:
        pytest.skip("NOT ASSESSED: no opa binary (set OPA_BIN); parity is not claimed")
    return binary


class TestRegoParity:

    @pytest.mark.parametrize("name,patch,expected", TABLE, ids=[r[0] for r in TABLE])
    def test_port_matches_rego(self, opa, tmp_path, name, patch, expected):
        doc = _input(patch)
        assert _comparable(authz.authorize_tool_call(doc, DATA)) == _comparable(_rego(opa, doc, tmp_path))

    @pytest.mark.parametrize("name,patch", DIVERGENT, ids=[r[0] for r in DIVERGENT])
    def test_known_rego_defect_still_present(self, opa, tmp_path, name, patch):
        # When this fails, the Rego was fixed: move the row into TABLE and
        # delete the divergence note in adapters/mcp/authz.py.
        assert _rego(opa, _input(patch), tmp_path)["allow"] is True


class TestNexusContext:

    def test_absent_meta_gives_defaults(self):
        ctx = authz.parse_nexus_context(None)
        assert (ctx.delegation_depth, ctx.context_compartment, ctx.requested_capabilities) == (0, "TASK_CONTEXT", ())

    def test_valid_meta(self):
        ctx = authz.parse_nexus_context({
            "progressToken": 7,
            "nexusDelegationDepth": 2,
            "nexusContextCompartment": "AGENT_STATE",
            "nexusMandateId": "mandate-0001",
            "nexusCaelEnvelopeHash": "a" * 64,
            "nexusRequestedCapabilities": ["agency_check"],
        })
        assert ctx.delegation_depth == 2
        assert ctx.mandate_id == "mandate-0001"
        assert ctx.requested_capabilities == ("agency_check",)

    @pytest.mark.parametrize("meta,field", [
        ([], "_meta"),
        ({"nexusDelegationDeph": 1}, "nexusDelegationDeph"),
        ({"nexusDelegationDepth": True}, "nexusDelegationDepth"),
        ({"nexusDelegationDepth": -1}, "nexusDelegationDepth"),
        ({"nexusDelegationDepth": 65}, "nexusDelegationDepth"),
        ({"nexusCaelEnvelopeHash": "A" * 64}, "nexusCaelEnvelopeHash"),
        ({"nexusCaelEnvelopeHash": "a" * 64 + "\n"}, "nexusCaelEnvelopeHash"),
        ({"nexusMandateId": "short"}, "nexusMandateId"),
        ({"nexusSenderDID": "not-a-did"}, "nexusSenderDID"),
        ({"nexusContextCompartment": "X" * 33}, "nexusContextCompartment"),
        ({"nexusRequestedCapabilities": ["Bad Tool"]}, "nexusRequestedCapabilities"),
        ({"nexusRequestedCapabilities": ["a"] * 17}, "nexusRequestedCapabilities"),
    ])
    def test_malformed_meta_rejected(self, meta, field):
        with pytest.raises(authz.NexusContextError) as exc:
            authz.parse_nexus_context(meta)
        assert exc.value.field == field


def _call(name="agency_check", meta=None):
    params = {"name": name, "arguments": {}}
    if meta is not None:
        params["_meta"] = meta
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}


class TestAdapterAuthorizeToolCall:

    principal = adapter.Principal(id="did:web:x:clients:a", attestation=adapter.AttestationStrength.BEARER)
    grant = adapter.CapabilityGrant(tools=frozenset({"agency_check", "describe_ruleset"}))

    def _run(self, body, **kw):
        kw.setdefault("policy_data", DATA)
        return adapter.MCPAdapter().authorize_tool_call(self.principal, self.grant, body, **kw)

    def test_allow_carries_policy_evidence(self):
        r = self._run(_call())
        assert r.decision is adapter.Decision.ALLOW
        assert r.evidence["policy_version"] == "nexus-authz-v0.3-v31"
        assert r.evidence["agent_id"] == "did:web:x:clients:a"

    def test_missing_revocation_snapshot_halts(self):
        for data in (None, {}, {"revocation": None}, {"revocation": {"agents": None}}):
            assert self._run(_call(), policy_data=data).decision is adapter.Decision.HALT

    def test_revoked_principal_rejected(self):
        principal = adapter.Principal(id="did:web:x:clients:bad", attestation=adapter.AttestationStrength.BEARER)
        r = adapter.MCPAdapter().authorize_tool_call(principal, self.grant, _call(), policy_data=DATA)
        assert r.decision is adapter.Decision.REJECT
        assert "revoked" in r.reason

    def test_ungranted_tool_rejected(self):
        assert self._run(_call("get_receipt")).decision is adapter.Decision.REJECT

    def test_not_a_tool_call_rejected(self):
        assert self._run({"method": "tools/list"}).decision is adapter.Decision.REJECT
        assert self._run({"method": "tools/call", "params": {}}).decision is adapter.Decision.REJECT

    def test_malformed_meta_rejected_with_field(self):
        r = self._run(_call(meta={"nexusDelegationDepth": "2"}))
        assert r.decision is adapter.Decision.REJECT
        assert r.findings == ["malformed:nexusDelegationDepth"]

    def test_meta_cannot_widen(self):
        r = self._run(_call(meta={"nexusRequestedCapabilities": ["credential:vault"]}))
        assert r.decision is adapter.Decision.REJECT

    def test_declared_depth_cannot_hide_verified_chain(self):
        principal = adapter.Principal(
            id="did:web:x:clients:a", attestation=adapter.AttestationStrength.BEARER,
            delegation_chain=tuple(f"did:web:x:p{i}" for i in range(5)))
        r = adapter.MCPAdapter().authorize_tool_call(
            principal, self.grant, _call(meta={"nexusDelegationDepth": 0}), policy_data=DATA)
        assert r.decision is adapter.Decision.REJECT
        assert r.evidence["delegation_depth"] == 5

    def test_sender_did_is_not_identity(self):
        r = self._run(_call(meta={"nexusSenderDID": "did:web:x:clients:bad"}))
        assert r.decision is adapter.Decision.ALLOW
        assert r.evidence["agent_id"] == "did:web:x:clients:a"

    @pytest.mark.parametrize("compartment", ["CREDENTIAL_SURFACE", "AGENT_STATE", "ROOT"])
    def test_asserted_compartment_cannot_bypass_credential_deny(self, compartment):
        grant = adapter.CapabilityGrant(tools=frozenset({"credential:vault"}))
        body = _call("credential:vault", meta={"nexusContextCompartment": compartment})
        r = adapter.MCPAdapter().authorize_tool_call(self.principal, grant, body, policy_data=DATA)
        assert r.decision is adapter.Decision.REJECT
        assert r.findings == ["malformed:nexusContextCompartment"]

    def test_asserted_compartment_cannot_bypass_for_delegated_caller(self):
        principal = adapter.Principal(
            id="did:web:x:clients:a", attestation=adapter.AttestationStrength.BEARER,
            delegation_chain=("did:web:x:p0",))
        grant = adapter.CapabilityGrant(tools=frozenset({"credential:vault"}))
        body = _call("credential:vault", meta={"nexusContextCompartment": "CREDENTIAL_SURFACE"})
        r = adapter.MCPAdapter().authorize_tool_call(principal, grant, body, policy_data=DATA)
        assert r.decision is adapter.Decision.REJECT

    def test_credential_tool_denied_in_default_compartment(self):
        grant = adapter.CapabilityGrant(tools=frozenset({"credential:vault"}))
        r = adapter.MCPAdapter().authorize_tool_call(
            self.principal, grant, _call("credential:vault"), policy_data=DATA)
        assert r.decision is adapter.Decision.REJECT
        assert "TASK_CONTEXT cannot access credential: tools" in r.reason

    def test_deployment_established_compartment_allows_credential_tool(self):
        grant = adapter.CapabilityGrant(tools=frozenset({"credential:vault"}))
        body = _call("credential:vault", meta={"nexusContextCompartment": "CREDENTIAL_SURFACE"})
        r = adapter.MCPAdapter().authorize_tool_call(
            self.principal, grant, body, policy_data=DATA, context_compartment="CREDENTIAL_SURFACE")
        assert r.decision is adapter.Decision.ALLOW

    @pytest.mark.parametrize("mandate", ["mandate-other", "mandate-tool", "mandate-old", "mandate-bare", "mandate-noexp", "mandate-missing"])
    def test_unbound_mandate_does_not_satisfy_gated_tool(self, mandate):
        r = self._run(_call(meta={"nexusMandateId": mandate}), mandate_required_tools=frozenset({"agency_check"}))
        assert r.decision is adapter.Decision.REJECT
        assert "tool requires an active mandate" in r.reason

    def test_bound_mandate_satisfies_gated_tool(self):
        r = self._run(_call(meta={"nexusMandateId": "mandate-ok"}), mandate_required_tools=frozenset({"agency_check"}))
        assert r.decision is adapter.Decision.ALLOW

    def test_other_principals_mandate_cannot_be_reused(self):
        principal = adapter.Principal(id="did:web:x:clients:thief", attestation=adapter.AttestationStrength.BEARER)
        r = adapter.MCPAdapter().authorize_tool_call(
            principal, self.grant, _call(meta={"nexusMandateId": "mandate-ok"}), policy_data=DATA,
            mandate_required_tools=frozenset({"agency_check"}))
        assert r.decision is adapter.Decision.REJECT

    def test_other_enforcement_steps_still_fail_closed(self):
        a = adapter.MCPAdapter()
        with pytest.raises(NotImplementedError):
            a.check_capability(self.principal, self.grant, _call())
        with pytest.raises(NotImplementedError):
            a.establish_trust(object(), "ACT-2")
        with pytest.raises(NotImplementedError):
            a.sanitize_return_path(self.principal, {})
