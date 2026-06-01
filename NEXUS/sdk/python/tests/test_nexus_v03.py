"""
tests/test_nexus_v03.py
NEXUS-A2A v0.3 Test Suite

Covers all new v0.3 modules. All 67 v0.2 tests continue in test_nexus_complete.py.
Together: 67 (v0.2) + tests in this file = 150+ total.

Run all: pytest tests/ -v
Run v0.3 only: pytest tests/test_nexus_v03.py -v

No external dependencies required. All stub modes exercised.
No em dashes in specification text.

Module coverage:
    TestGuardianCore            - GuardianPolicy, verdict contract, rule hierarchy
    TestGuardianStepContext     - StepContext construction, JSON-RPC serialization
    TestGuardianNEXUSIdentity   - NEXUSAgentContext vs ACS bare string identity
    TestGuardianMemoryHooks     - Memory provenance extension on memory hooks
    TestGuardianFailover        - NEXUSGuardianClient failover modes
    TestGuardianReasoningChain  - Reasoning chain non-repudiation (P2)
    TestNORCore                 - NEXUSOutputReceipt construction, signing, hash
    TestNOROTelExport           - OTel attribute mapping, OCSF classification
    TestNORInMemoryExporter     - InMemoryNORExporter test utility
    TestNORFactory              - build_tool_call_nor, build_memory_nor factories
    TestAgBOMCore               - Component creation, CycloneDX format
    TestAgBOMHashChain          - Version hash chain integrity
    TestAgBOMMCPDiscovery       - MCP server discovery workflow
    TestAgBOMFormats            - CycloneDX, SPDX, NEXUS-native formats
    TestACSBridgeCore           - NEXUSACSBridge request construction
    TestACSBridgeVerdictParsing - Guardian verdict parsing
    TestACSBridgeMemoryHooks    - Memory hook with provenance context
    TestACSBridgeMessageHook    - steps/message interception
    TestMemoryVaccineACSExport  - ACS context export from MemoryVaccine
    TestIntegrationStack        - End-to-end: CAEL -> Guardian -> NOR -> OTel
    TestSAFE2v03Compliance      - v0.3 SAFE2 control alignment
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from nexus_sdk.cael import (
    CAELEnvelope, CAELSender, CAELDelegation, CAELToolCall,
    JouleWorkCost, OPAReceipt, Performative, ContextCompartment,
)
from nexus_sdk.memory import MemoryVaccine, MemoryZone, MemoryWriteResult
from nexus_sdk.guardian import (
    GuardianPolicy, GuardianVerdict, GuardianVerdictResult,
    GuardianStepContext, NEXUSAgentContext, NEXUSMemoryProvenance,
    StepMethod, NEXUSGuardianClient,
    build_tool_call_step, build_memory_store_step,
)
from nexus_sdk.otel import (
    NEXUSOutputReceipt, InMemoryNORExporter,
    OCSFEventClass, nor_to_otel_attributes,
    build_tool_call_nor, build_memory_nor,
)
from nexus_sdk.agbom import (
    AgBOMManager, AgBOMComponent, AgBOMComponentType, AgBOMVersion,
)
from nexus_sdk.bridges import (
    NEXUSACSBridge, NEXUSMCPBridge, ProtocolBridgeFactory,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

AGENT_DID = "did:web:nexus.local:agents:test-agent-001"
SPIFFE_ID = "spiffe://nexus.local/agents/orchestrator/csi/test/principal"
TARGET_DID = "did:web:nexus.local:agents:target-001"
VCC_ID = "urn:uuid:550e8400-e29b-41d4-a716-446655440000"
PARENT_DID = "did:web:nexus.local:agents:orchestrator-001"


@pytest.fixture
def agent_ctx():
    return NEXUSAgentContext(
        agent_did=AGENT_DID,
        spiffe_id=SPIFFE_ID,
        maturity_level="associate",
        agent_class="orchestrator",
        act_tier=2,
    )


@pytest.fixture
def guardian():
    return GuardianPolicy()


@pytest.fixture
def guardian_client():
    return NEXUSGuardianClient(inline_policy=GuardianPolicy())


@pytest.fixture
def vaccine():
    return MemoryVaccine(
        agent_did=AGENT_DID,
        purpose_declaration="Orchestrate cybersecurity analysis tasks",
        use_stub_embeddings=True,
    )


@pytest.fixture
def agbom():
    return AgBOMManager(agent_did=AGENT_DID, session_id="sess-test-001")


@pytest.fixture
def acs_bridge():
    return NEXUSACSBridge()


@pytest.fixture
def nor_exporter():
    return InMemoryNORExporter()


@pytest.fixture
def sample_tool_call_dict():
    tc = CAELToolCall(
        tool_name="github.fetch_repo_metadata",
        arguments={"owner": "csi", "repo": "nexus-a2a"},
        requested_by_did=AGENT_DID,
        context_compartment=ContextCompartment.TASK_CONTEXT,
        vcc_id=VCC_ID,
        delegation_depth=1,
    )
    tc.joulework = JouleWorkCost.compute(1200)
    tc.opa_auth = OPAReceipt(decision="allow")
    return tc.to_dict()


@pytest.fixture
def sample_cael_dict():
    env = CAELEnvelope(
        sender=CAELSender(agent_did=AGENT_DID, spiffe_id=SPIFFE_ID),
        recipient_did=TARGET_DID,
        performative=Performative.DELEGATE,
        goal="Research phase 1",
    )
    env.delegation = CAELDelegation(vcc_id=VCC_ID, delegation_depth=1)
    env.sign()
    return env.to_dict()


# ── Guardian Core ─────────────────────────────────────────────────────────────

class TestGuardianCore:
    """GuardianPolicy rule hierarchy and verdict contract."""

    def test_allow_clean_tool_call(self, guardian, agent_ctx):
        ctx = build_tool_call_step(
            agent_did=AGENT_DID,
            spiffe_id=SPIFFE_ID,
            tool_name="search:web",
            tool_arguments={"query": "AI governance frameworks"},
            vcc_id=VCC_ID,
            vcc_capabilities=["search:web"],
            parent_vcc_capabilities=["search:web", "email:read"],
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.ALLOW
        assert verdict.allowed is True

    def test_deny_revoked_agent(self, agent_ctx):
        policy = GuardianPolicy(revoked_dids=[AGENT_DID])
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        verdict = policy.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "REVOKED_AGENT" in verdict.reason_codes

    def test_deny_scope_overflow(self, guardian, agent_ctx):
        """Catch scope widening that OPA scope categories cannot detect."""
        ctx = build_tool_call_step(
            agent_did=AGENT_DID,
            spiffe_id=SPIFFE_ID,
            tool_name="email:send",
            tool_arguments={"to": "attacker@evil.com"},
            vcc_capabilities=["email:read", "email:send"],
            parent_vcc_capabilities=["email:read"],  # email:send not in parent
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "SCOPE_OVERFLOW" in verdict.reason_codes

    def test_deny_delegation_depth_exceeded(self, guardian):
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "search:web", {},
            delegation_depth=5,  # exceeds max 4
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "DELEGATION_DEPTH_EXCEEDED" in verdict.reason_codes

    def test_deny_path_traversal_in_arguments(self, guardian):
        """Catch argument-level attack that VCC scope cannot prevent."""
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="filesystem:read",
            tool_arguments={"path": "/etc/passwd"},
            vcc_capabilities=["filesystem:read"],
            parent_vcc_capabilities=["filesystem:read"],
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "BLOCKED_ARGUMENT_PATTERN" in verdict.reason_codes

    def test_deny_imds_endpoint_in_arguments(self, guardian):
        """Catch SSRF attempt targeting AWS IMDS metadata endpoint."""
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="http:fetch",
            tool_arguments={"url": "http://169.254.169.254/latest/meta-data/"},
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY

    def test_deny_credential_tool_in_task_context(self, guardian):
        """credential: namespace blocked regardless of VCC scope."""
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="credential:aws_key",
            tool_arguments={"key_id": "AKIA..."},
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "CONTEXT_VIOLATION" in verdict.reason_codes

    def test_deny_act3_agent_without_reasoning(self):
        """ACT-3 agents must provide reasoning before tool execution (HEAR Doctrine)."""
        policy = GuardianPolicy(require_reasoning_for_act_tiers=[3, 4])
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="payment:transfer",
            tool_arguments={"amount": 10000},
            act_tier=3,
            reasoning=None,  # Missing reasoning
        )
        verdict = policy.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "REASONING_REQUIRED" in verdict.reason_codes

    def test_allow_act3_agent_with_reasoning(self):
        """ACT-3 agent with reasoning chain passes the HEAR Doctrine check."""
        policy = GuardianPolicy(require_reasoning_for_act_tiers=[3, 4])
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="payment:transfer",
            tool_arguments={"amount": 10000},
            act_tier=3,
            reasoning="Transfer approved by mandate-id:mand_abc123 for invoice INV-2026-001",
        )
        verdict = policy.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.ALLOW

    def test_allow_verdict_has_nor_fingerprint(self, guardian):
        """Allow verdicts must include NOR fingerprint for audit chain inclusion."""
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {"q": "test"})
        verdict = guardian.evaluate(ctx)
        assert verdict.nor_fingerprint is not None
        assert len(verdict.nor_fingerprint) == 64  # SHA-256 hex

    def test_deny_permanent_memory_without_mandate(self, guardian):
        """PERMANENT_MEMORY write requires mandate_id (HEAR Doctrine)."""
        prov = NEXUSMemoryProvenance(
            source_did=AGENT_DID,
            zone="PERMANENT_MEMORY",
            mandate_id=None,  # Missing mandate
        )
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID,
            memory_content=["User's permanent preference"],
            provenance=prov,
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "NO_MANDATE" in verdict.reason_codes

    def test_deny_memory_drift_exceeds_guardian_threshold(self, guardian):
        """Guardian enforces tighter drift threshold (0.25) than Vaccine (0.30)."""
        prov = NEXUSMemoryProvenance(
            source_did=AGENT_DID,
            zone="CROSS_SESSION_MEMORY",
            drift_score=0.27,  # Above Guardian's 0.25, but below Vaccine's 0.30
        )
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID,
            memory_content=["Slightly drifted content"],
            provenance=prov,
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY
        assert "MEMORY_DRIFT_EXCEEDED" in verdict.reason_codes

    def test_allow_memory_within_guardian_threshold(self, guardian):
        prov = NEXUSMemoryProvenance(
            source_did=AGENT_DID,
            zone="CROSS_SESSION_MEMORY",
            drift_score=0.10,  # Well within threshold
        )
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID,
            memory_content=["Normal operational memory"],
            provenance=prov,
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.ALLOW

    def test_custom_blocked_patterns(self):
        """Custom blocked patterns are enforced."""
        policy = GuardianPolicy(blocked_argument_patterns=["CUSTOM_BLOCKED_TERM"])
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "tool:call",
            {"param": "contains CUSTOM_BLOCKED_TERM in value"},
        )
        verdict = policy.evaluate(ctx)
        assert verdict.decision == GuardianVerdict.DENY


# ── Guardian Step Context ─────────────────────────────────────────────────────

class TestGuardianStepContext:
    """StepContext construction and JSON-RPC serialization."""

    def test_step_context_auto_generates_step_id(self, agent_ctx):
        ctx = GuardianStepContext(
            method=StepMethod.TOOL_CALL_REQUEST,
            agent=agent_ctx,
        )
        assert ctx.step_id.startswith("step_")
        assert len(ctx.step_id) > 8

    def test_step_context_serializes_to_jsonrpc_params(self, agent_ctx):
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            "github.search", {"q": "test"},
            vcc_id=VCC_ID,
        )
        params = ctx.to_jsonrpc_params()
        assert "stepId" in params
        assert "agent" in params
        assert "action" in params
        assert params["action"]["method"] == "github.search"

    def test_nexus_extension_block_present_in_params(self, agent_ctx):
        """NEXUS extension block must be present and parseable by ACS Guardians."""
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "tool:call", {},
            vcc_id=VCC_ID, delegation_depth=2,
        )
        params = ctx.to_jsonrpc_params()
        assert "nexus" in params
        assert params["nexus"]["delegationDepth"] == 2
        assert params["nexus"]["vccId"] == VCC_ID

    def test_agent_id_field_for_acs_compatibility(self, agent_ctx):
        """ACS Guardians use agent.id field; NEXUS sets it to the DID."""
        params = GuardianStepContext(
            method=StepMethod.TOOL_CALL_REQUEST,
            agent=agent_ctx,
        ).to_jsonrpc_params()
        assert params["agent"]["id"] == AGENT_DID

    def test_reasoning_hash_computed_when_reasoning_provided(self):
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "payment:execute", {},
            reasoning="Approved: mandate mand_xyz, invoice INV-001",
        )
        assert ctx.reasoning_hash is not None
        assert len(ctx.reasoning_hash) == 64  # SHA-256

    def test_reasoning_absent_when_not_provided(self):
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        assert ctx.reasoning is None
        assert ctx.reasoning_hash is None

    def test_all_step_methods_enumerable(self):
        """All AOS step methods must be valid enum values."""
        aos_methods = [
            StepMethod.AGENT_TRIGGER, StepMethod.KNOWLEDGE_RETRIEVAL,
            StepMethod.MEMORY_STORE, StepMethod.MEMORY_CONTEXT_RETRIEVAL,
            StepMethod.MESSAGE, StepMethod.TOOL_CALL_REQUEST,
            StepMethod.TOOL_CALL_RESULT, StepMethod.MCP_PROTOCOL,
        ]
        assert len(aos_methods) == 8
        # NEXUS extensions
        nexus_methods = [StepMethod.NEXUS_DELEGATE, StepMethod.NEXUS_SWARM_JOIN,
                         StepMethod.NEXUS_CONFIG_CHANGE]
        assert len(nexus_methods) == 3


# ── Guardian NEXUS Identity ───────────────────────────────────────────────────

class TestGuardianNEXUSIdentity:
    """NEXUSAgentContext vs ACS bare string - the critical security distinction."""

    def test_nexus_agent_context_has_spiffe_id(self, agent_ctx):
        assert agent_ctx.spiffe_id.startswith("spiffe://")

    def test_nexus_agent_context_has_act_tier(self, agent_ctx):
        assert agent_ctx.act_tier == 2

    def test_nexus_agent_context_id_property_returns_did(self, agent_ctx):
        """ACS compatibility: agent.id must equal agent_did."""
        assert agent_ctx.id == AGENT_DID

    def test_nexus_agent_context_serializes_both_id_and_did(self, agent_ctx):
        d = agent_ctx.to_dict()
        assert d["id"] == AGENT_DID       # ACS compatibility
        assert d["agent_did"] == AGENT_DID  # NEXUS field

    def test_aim_digest_optional_but_supported(self):
        ctx = NEXUSAgentContext(
            agent_did=AGENT_DID,
            spiffe_id=SPIFFE_ID,
            aim_digest="sha256:abc123def456",
        )
        assert ctx.aim_digest == "sha256:abc123def456"
        assert ctx.to_dict()["aim_digest"] == "sha256:abc123def456"


# ── Guardian Memory Hooks ─────────────────────────────────────────────────────

class TestGuardianMemoryHooks:
    """Memory provenance extension enables policy enforcement ACS cannot do alone."""

    def test_memory_provenance_populated_in_step_context(self):
        prov = NEXUSMemoryProvenance(
            source_did=AGENT_DID,
            zone="CROSS_SESSION_MEMORY",
            drift_score=0.12,
            embedding_hash="sha256:abc",
            session_id="sess-001",
        )
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID,
            memory_content=["test memory"],
            provenance=prov,
        )
        assert ctx.nexus_provenance is not None
        assert ctx.nexus_provenance.drift_score == 0.12
        assert ctx.nexus_provenance.zone == "CROSS_SESSION_MEMORY"

    def test_memory_provenance_in_jsonrpc_params(self):
        prov = NEXUSMemoryProvenance(
            source_did=AGENT_DID,
            zone="CROSS_SESSION_MEMORY",
            drift_score=0.10,
        )
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID, ["content"], provenance=prov
        )
        params = ctx.to_jsonrpc_params()
        assert "nexus" in params
        assert "memoryProvenance" in params["nexus"]
        assert params["nexus"]["memoryProvenance"]["drift_score"] == 0.10

    def test_memory_content_list_in_params(self):
        ctx = build_memory_store_step(
            AGENT_DID, SPIFFE_ID, ["entry1", "entry2"]
        )
        params = ctx.to_jsonrpc_params()
        assert params["memory"] == ["entry1", "entry2"]


# ── Guardian Failover ─────────────────────────────────────────────────────────

class TestGuardianFailover:
    """NEXUSGuardianClient failover modes (P2 gap closure)."""

    def test_inline_client_uses_policy(self, guardian_client):
        """Inline client evaluates using provided policy, no network required."""
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        verdict = guardian_client.evaluate(ctx)
        assert verdict.decision in {GuardianVerdict.ALLOW, GuardianVerdict.DENY}

    def test_fail_closed_denies_when_unavailable(self):
        """FAIL_CLOSED mode must deny all actions when Guardian unreachable."""
        client = NEXUSGuardianClient(
            guardian_url="http://nonexistent.guardian:9999",
            fail_mode=NEXUSGuardianClient.FAIL_CLOSED,
        )
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        verdict = client._handle_guardian_unavailable(ctx, "connection refused")
        assert verdict.decision == GuardianVerdict.DENY
        assert "GUARDIAN_UNAVAILABLE_FAIL_CLOSED" in verdict.reason_codes

    def test_fail_open_allows_when_unavailable(self):
        """FAIL_OPEN mode allows actions when Guardian unreachable (document in AIM)."""
        client = NEXUSGuardianClient(fail_mode=NEXUSGuardianClient.FAIL_OPEN)
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        verdict = client._handle_guardian_unavailable(ctx, "timeout")
        assert verdict.decision == GuardianVerdict.ALLOW
        assert "GUARDIAN_UNAVAILABLE_FAIL_OPEN" in verdict.reason_codes

    def test_inline_client_ping_returns_true(self):
        """Inline client (no URL) always reports available."""
        client = NEXUSGuardianClient(inline_policy=GuardianPolicy())
        assert client.ping() is True
        assert client.is_available is True

    def test_three_fail_modes_are_defined(self):
        assert NEXUSGuardianClient.FAIL_CLOSED == "fail_closed"
        assert NEXUSGuardianClient.FAIL_OPEN == "fail_open"
        assert NEXUSGuardianClient.FAIL_MANDATE_ONLY == "fail_mandate_only"


# ── Guardian Reasoning Chain Non-Repudiation ─────────────────────────────────

class TestGuardianReasoningChain:
    """Reasoning chain hashed into NOR fingerprint for forensic non-repudiation."""

    def test_reasoning_hash_included_in_nor_fingerprint(self, guardian):
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="payment:execute",
            tool_arguments={"amount": 5000},
            act_tier=2,
            reasoning="Mandate mand_abc123 authorizes this transfer for Q1 budget",
        )
        verdict = guardian.evaluate(ctx)
        # NOR fingerprint computed from reasoning_hash -> traceable to reasoning
        assert verdict.nor_fingerprint is not None

    def test_different_reasoning_chains_produce_different_fingerprints(self, guardian):
        """Each unique reasoning chain produces a unique NOR fingerprint."""
        ctx1 = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "tool:call", {},
            reasoning="Reasoning chain A",
        )
        ctx2 = build_tool_call_step(
            AGENT_DID, SPIFFE_ID, "tool:call", {},
            reasoning="Reasoning chain B",
        )
        v1 = guardian.evaluate(ctx1)
        v2 = guardian.evaluate(ctx2)
        assert v1.nor_fingerprint != v2.nor_fingerprint

    def test_verdict_to_dict_includes_required_fields(self, guardian):
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "search:web", {})
        verdict = guardian.evaluate(ctx)
        d = verdict.to_dict()
        assert "decision" in d
        assert "stepId" in d
        assert "timestamp" in d
        assert "policyVersion" in d


# ── NOR Core ──────────────────────────────────────────────────────────────────

class TestNORCore:
    """NEXUSOutputReceipt construction, signing, and hash integrity."""

    def test_nor_auto_generates_receipt_id(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "search:web", "allow")
        assert nor.receipt_id.startswith("nor_")

    def test_nor_signing_produces_signature(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "search:web", "allow")
        nor.sign()
        assert nor.signature is not None
        assert nor.receipt_hash is not None

    def test_nor_receipt_hash_is_sha256(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
        nor.compute_receipt_hash()
        assert len(nor.receipt_hash) == 64

    def test_nor_to_dict_excludes_none_fields(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "search:web", "allow")
        d = nor.to_dict()
        assert None not in d.values()

    def test_nor_tool_call_fields_populated(self):
        nor = build_tool_call_nor(
            AGENT_DID, SPIFFE_ID, "github:search", "allow",
            vcc_id=VCC_ID, delegation_depth=1,
            joulework_cost=42, session_id="sess-001",
        )
        assert nor.action_type == "tool_call"
        assert nor.action_detail == "github:search"
        assert nor.vcc_id == VCC_ID
        assert nor.joulework_cost == 42

    def test_nor_deny_outcome_preserved(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "credential:key", "deny")
        assert nor.outcome == "deny"

    def test_nor_memory_factory(self):
        nor = build_memory_nor(
            AGENT_DID, SPIFFE_ID, "CROSS_SESSION_MEMORY", "allow", drift_score=0.08
        )
        assert nor.action_type == "memory_write"
        assert "drift=0.080" in nor.action_detail


# ── NOR OTel Export ───────────────────────────────────────────────────────────

class TestNOROTelExport:
    """OpenTelemetry attribute mapping and OCSF classification."""

    def test_otel_attributes_use_nexus_nor_prefix(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "search:web", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert "nexus.nor.agent_did" in attrs
        assert "nexus.nor.action_type" in attrs
        assert "nexus.nor.outcome" in attrs

    def test_tool_call_maps_to_api_activity_ocsf_class(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "api:call", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["ocsf.class_uid"] == OCSFEventClass.API_ACTIVITY.value

    def test_deny_outcome_maps_to_policy_violation_ocsf(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "credential:key", "deny")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["ocsf.class_uid"] == OCSFEventClass.POLICY_VIOLATION.value

    def test_deny_sets_high_severity(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "deny")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["ocsf.severity_id"] == 4  # High

    def test_allow_sets_informational_severity(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["ocsf.severity_id"] == 1  # Informational

    def test_span_name_includes_action_type(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["span.name"] == "nexus.tool_call"

    def test_memory_write_maps_to_data_activity_ocsf(self):
        nor = build_memory_nor(AGENT_DID, SPIFFE_ID, "CROSS_SESSION_MEMORY", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor)
        assert attrs["ocsf.class_uid"] == OCSFEventClass.DATA_ACTIVITY.value

    def test_explicit_ocsf_class_overrides_auto_detection(self):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
        nor.sign()
        attrs = nor_to_otel_attributes(nor, OCSFEventClass.INCIDENT_FINDING)
        assert attrs["ocsf.class_uid"] == OCSFEventClass.INCIDENT_FINDING.value

    def test_ocsf_event_classes_cover_required_types(self):
        expected = {
            OCSFEventClass.AUTHENTICATION_ACTIVITY,
            OCSFEventClass.AUTHORIZATION_ACTIVITY,
            OCSFEventClass.DATA_ACTIVITY,
            OCSFEventClass.API_ACTIVITY,
            OCSFEventClass.DETECTION_FINDING,
            OCSFEventClass.INCIDENT_FINDING,
            OCSFEventClass.POLICY_VIOLATION,
        }
        assert len(expected) == 7


# ── NOR InMemory Exporter ─────────────────────────────────────────────────────

class TestNORInMemoryExporter:
    """InMemoryNORExporter test utility API."""

    def test_export_appends_span(self, nor_exporter):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "search:web", "allow")
        nor_exporter.export(nor)
        assert len(nor_exporter.spans) == 1

    def test_multiple_exports_accumulate(self, nor_exporter):
        for _ in range(5):
            nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
            nor_exporter.export(nor)
        assert len(nor_exporter.spans) == 5

    def test_get_spans_for_agent_filters_correctly(self, nor_exporter):
        other_did = "did:web:nexus.local:agents:other-agent"
        nor_exporter.export(build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:a", "allow"))
        nor_exporter.export(build_tool_call_nor(other_did, None, "tool:b", "allow"))
        spans = nor_exporter.get_spans_for_agent(AGENT_DID)
        assert len(spans) == 1

    def test_get_denied_actions_filters_correctly(self, nor_exporter):
        nor_exporter.export(build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:ok", "allow"))
        nor_exporter.export(build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:bad", "deny"))
        denied = nor_exporter.get_denied_actions()
        assert len(denied) == 1

    def test_get_policy_violations(self, nor_exporter):
        nor_exporter.export(build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:a", "deny"))
        violations = nor_exporter.get_policy_violations()
        assert len(violations) == 1

    def test_clear_resets_state(self, nor_exporter):
        nor_exporter.export(build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:a", "allow"))
        nor_exporter.clear()
        assert len(nor_exporter.spans) == 0
        assert len(nor_exporter.receipts) == 0

    def test_export_auto_signs_nor(self, nor_exporter):
        nor = build_tool_call_nor(AGENT_DID, SPIFFE_ID, "tool:call", "allow")
        assert nor.signature is None
        nor_exporter.export(nor)
        assert nor.signature is not None


# ── AgBOM Core ────────────────────────────────────────────────────────────────

class TestAgBOMCore:
    """AgBOMComponent and AgBOMManager core operations."""

    def test_agbom_manager_initializes_empty(self, agbom):
        assert agbom.component_count == 0
        assert agbom.current_version == 0

    def test_add_component_increments_version(self, agbom):
        comp = AgBOMComponent(name="test-tool", component_type=AgBOMComponentType.TOOL)
        agbom.add_component(comp)
        assert agbom.current_version == 1

    def test_add_multiple_components_each_creates_version(self, agbom):
        for i in range(3):
            comp = AgBOMComponent(
                name=f"tool-{i}",
                component_type=AgBOMComponentType.TOOL,
            )
            agbom.add_component(comp)
        assert agbom.current_version == 3
        assert agbom.component_count == 3

    def test_remove_component_creates_new_version(self, agbom):
        comp = AgBOMComponent(name="tool-to-remove", component_type=AgBOMComponentType.TOOL)
        version = agbom.add_component(comp)
        agbom.remove_component(comp.bom_ref)
        assert agbom.current_version == 2
        assert agbom.component_count == 0

    def test_remove_nonexistent_component_returns_none(self, agbom):
        result = agbom.remove_component("nonexistent-bom-ref")
        assert result is None

    def test_component_bom_ref_auto_generated(self):
        comp = AgBOMComponent(name="auto-ref", component_type=AgBOMComponentType.TOOL)
        assert comp.bom_ref.startswith("comp-")

    def test_component_types_cover_required_categories(self):
        required = {
            AgBOMComponentType.TOOL, AgBOMComponentType.MODEL,
            AgBOMComponentType.MCP_SERVER, AgBOMComponentType.KNOWLEDGE_BASE,
            AgBOMComponentType.TRUST_ANCHOR, AgBOMComponentType.DELEGATION_PEER,
        }
        for t in required:
            comp = AgBOMComponent(name=f"test-{t.value}", component_type=t)
            assert comp.component_type == t


# ── AgBOM Hash Chain ──────────────────────────────────────────────────────────

class TestAgBOMHashChain:
    """Version hash chain integrity - the key supply chain security property."""

    def test_first_version_has_no_parent_hash(self, agbom):
        comp = AgBOMComponent(name="tool-1", component_type=AgBOMComponentType.TOOL)
        version = agbom.add_component(comp)
        assert version.parent_hash is None

    def test_second_version_parent_hash_equals_first_version_hash(self, agbom):
        comp1 = AgBOMComponent(name="tool-1", component_type=AgBOMComponentType.TOOL)
        comp2 = AgBOMComponent(name="tool-2", component_type=AgBOMComponentType.TOOL)
        v1 = agbom.add_component(comp1)
        v2 = agbom.add_component(comp2)
        assert v2.parent_hash == v1.version_hash

    def test_all_versions_have_hash_and_signature(self, agbom):
        for i in range(3):
            comp = AgBOMComponent(name=f"t{i}", component_type=AgBOMComponentType.TOOL)
            agbom.add_component(comp)
        is_valid, violations = agbom.verify_chain_integrity()
        assert is_valid is True
        assert violations == []

    def test_latest_version_hash_accessible(self, agbom):
        comp = AgBOMComponent(name="tool", component_type=AgBOMComponentType.TOOL)
        agbom.add_component(comp)
        assert agbom.latest_version_hash is not None
        assert len(agbom.latest_version_hash) == 64  # SHA-256

    def test_chain_verify_returns_violations_list(self, agbom):
        """Chain integrity returns (bool, list) always, even on empty AgBOM."""
        is_valid, violations = agbom.verify_chain_integrity()
        assert isinstance(is_valid, bool)
        assert isinstance(violations, list)

    def test_chain_integrity_holds_across_additions_and_removals(self, agbom):
        comp = AgBOMComponent(name="temporary", component_type=AgBOMComponentType.TOOL)
        agbom.add_component(comp)
        agbom.remove_component(comp.bom_ref)
        is_valid, violations = agbom.verify_chain_integrity()
        assert is_valid is True


# ── AgBOM MCP Discovery ───────────────────────────────────────────────────────

class TestAgBOMMCPDiscovery:
    """MCP server discovery workflow - the primary production use case."""

    def test_discover_mcp_server_creates_version(self, agbom):
        version = agbom.discover_mcp_server(
            server_name="github-mcp-server",
            server_url="https://github.mcp.csi.gov",
            tool_manifest_digest="sha256:abc123",
        )
        assert agbom.current_version == 1
        assert len(agbom.get_mcp_servers()) == 1

    def test_mcp_server_component_type_is_mcp_server(self, agbom):
        agbom.discover_mcp_server("test-server", "https://test.mcp")
        servers = agbom.get_mcp_servers()
        assert all(s.component_type == AgBOMComponentType.MCP_SERVER for s in servers)

    def test_mcp_server_purl_format(self, agbom):
        agbom.discover_mcp_server("my-server", "https://server.mcp", version="1.2.3")
        servers = agbom.get_mcp_servers()
        assert servers[0].purl == "pkg:mcp/my-server@1.2.3"

    def test_unsigned_server_detected_as_supply_chain_risk(self, agbom):
        agbom.discover_mcp_server("unsigned-server", "https://risky.mcp", signed=False)
        unsigned = agbom.get_unsigned_components()
        assert len(unsigned) == 1

    def test_signed_server_not_in_unsigned_list(self, agbom):
        agbom.discover_mcp_server("nca-signed-server", "https://trusted.mcp", signed=True)
        unsigned = agbom.get_unsigned_components()
        assert len(unsigned) == 0

    def test_multiple_mcp_server_discovery(self, agbom):
        for i in range(3):
            agbom.discover_mcp_server(f"server-{i}", f"https://server-{i}.mcp")
        assert len(agbom.get_mcp_servers()) == 3
        assert agbom.current_version == 3


# ── AgBOM Formats ─────────────────────────────────────────────────────────────

class TestAgBOMFormats:
    """CycloneDX, SPDX, and NEXUS-native output formats."""

    def test_cyclonedx_format_has_correct_bom_format(self, agbom):
        agbom.discover_mcp_server("test", "https://test.mcp")
        cdx = agbom.to_cyclonedx()
        assert cdx["bomFormat"] == "CycloneDX"
        assert cdx["specVersion"] == "1.6"

    def test_cyclonedx_components_list_populated(self, agbom):
        agbom.discover_mcp_server("server1", "https://s1.mcp")
        agbom.discover_mcp_server("server2", "https://s2.mcp")
        cdx = agbom.to_cyclonedx()
        assert len(cdx["components"]) == 2

    def test_cyclonedx_is_json_serializable(self, agbom):
        agbom.discover_mcp_server("test", "https://test.mcp")
        cdx = agbom.to_cyclonedx()
        json_str = json.dumps(cdx)
        assert json_str is not None

    def test_spdx_summary_starts_with_spdx_version(self, agbom):
        agbom.discover_mcp_server("test", "https://test.mcp")
        spdx = agbom.to_spdx_summary()
        assert spdx.startswith("SPDXVersion: SPDX-2.3")

    def test_nexus_native_format_includes_chain_hash(self, agbom):
        agbom.discover_mcp_server("test", "https://test.mcp")
        native = agbom.to_dict()
        assert native["latest_version_hash"] is not None
        assert native["agbom_format"] == "nexus-agbom/0.3"

    def test_nexus_native_format_includes_unsigned_count(self, agbom):
        agbom.discover_mcp_server("signed", "https://s.mcp", signed=True)
        agbom.discover_mcp_server("unsigned", "https://u.mcp", signed=False)
        native = agbom.to_dict()
        assert native["unsigned_mcp_server_count"] == 1


# ── ACS Bridge Core ───────────────────────────────────────────────────────────

class TestACSBridgeCore:
    """NEXUSACSBridge request construction and ACS compatibility."""

    def test_tool_call_request_is_jsonrpc_20(self, acs_bridge, sample_tool_call_dict):
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        assert req["jsonrpc"] == "2.0"

    def test_tool_call_method_is_steps_tool_call_request(self, acs_bridge, sample_tool_call_dict):
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        assert req["method"] == "steps/toolCallRequest"

    def test_tool_call_params_has_agent_id(self, acs_bridge, sample_tool_call_dict):
        """ACS compatibility: params.agent.id must be present."""
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        assert "agent" in req["params"]
        assert "id" in req["params"]["agent"]

    def test_tool_call_params_has_nexus_extension(self, acs_bridge, sample_tool_call_dict):
        """NEXUS extension block must be present and contain delegation context."""
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        assert "nexus" in req["params"]
        assert "delegationDepth" in req["params"]["nexus"]

    def test_tool_call_action_contains_method_and_arguments(self, acs_bridge, sample_tool_call_dict):
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        action = req["params"]["action"]
        assert action["method"] == "github.fetch_repo_metadata"
        assert action["arguments"]["owner"] == "csi"

    def test_reasoning_included_when_provided(self, acs_bridge, sample_tool_call_dict):
        reasoning = "Mandate mand_001 authorizes this read operation"
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict, reasoning=reasoning)
        assert req["params"]["reasoning"] == reasoning

    def test_request_is_json_serializable(self, acs_bridge, sample_tool_call_dict):
        req = acs_bridge.build_tool_call_request(sample_tool_call_dict)
        json.dumps(req)  # Must not raise


# ── ACS Bridge Verdict Parsing ────────────────────────────────────────────────

class TestACSBridgeVerdictParsing:
    """Guardian verdict parsing: all three outcomes + error handling."""

    def test_parse_allow_verdict(self, acs_bridge):
        response = {
            "jsonrpc": "2.0",
            "id": "step_001",
            "result": {"decision": "allow", "reasoning": "Policy passed"},
        }
        parsed = acs_bridge.parse_verdict(response)
        assert parsed["allowed"] is True
        assert parsed["decision"] == "allow"

    def test_parse_deny_verdict(self, acs_bridge):
        response = {
            "jsonrpc": "2.0",
            "id": "step_002",
            "result": {
                "decision": "deny",
                "reasoning": "Path traversal detected",
                "reasonCode": ["BLOCKED_ARGUMENT_PATTERN"],
            },
        }
        parsed = acs_bridge.parse_verdict(response)
        assert parsed["allowed"] is False
        assert parsed["decision"] == "deny"
        assert "BLOCKED_ARGUMENT_PATTERN" in parsed["reason_codes"]

    def test_parse_modify_verdict(self, acs_bridge):
        response = {
            "jsonrpc": "2.0",
            "id": "step_003",
            "result": {
                "decision": "modify",
                "modifiedRequest": {"tool_name": "search:web", "arguments": {"q": "[sanitized]"}},
            },
        }
        parsed = acs_bridge.parse_verdict(response)
        assert parsed["decision"] == "modify"
        assert parsed["modified_request"] is not None

    def test_parse_error_response_returns_deny(self, acs_bridge):
        response = {
            "jsonrpc": "2.0",
            "id": "step_004",
            "error": {"code": -32603, "message": "Internal Guardian error"},
        }
        parsed = acs_bridge.parse_verdict(response)
        assert parsed["allowed"] is False
        assert parsed["decision"] == "deny"
        assert "GUARDIAN_ERROR" in parsed["reason_codes"]

    def test_step_id_preserved_in_parsed_verdict(self, acs_bridge):
        response = {
            "jsonrpc": "2.0",
            "id": "step_sentinel",
            "result": {"decision": "allow"},
        }
        parsed = acs_bridge.parse_verdict(response)
        assert parsed["step_id"] == "step_sentinel"


# ── ACS Bridge Memory Hooks ───────────────────────────────────────────────────

class TestACSBridgeMemoryHooks:
    """Memory store requests with NEXUS provenance context."""

    def test_memory_store_method_is_steps_memory_store(self, acs_bridge):
        req = acs_bridge.build_memory_store_request(
            ["test content"], AGENT_DID
        )
        assert req["method"] == "steps/memoryStore"

    def test_memory_content_in_params(self, acs_bridge):
        content = ["memory entry 1", "memory entry 2"]
        req = acs_bridge.build_memory_store_request(content, AGENT_DID)
        assert req["params"]["memory"] == content

    def test_provenance_dict_in_nexus_extension(self, acs_bridge):
        prov = {"zone": "CROSS_SESSION_MEMORY", "drift_score": 0.08, "source_did": AGENT_DID}
        req = acs_bridge.build_memory_store_request(["content"], AGENT_DID, prov)
        assert "nexus" in req["params"]
        assert req["params"]["nexus"]["memoryProvenance"]["drift_score"] == 0.08

    def test_message_request_builds_correctly(self, acs_bridge, sample_cael_dict):
        req = acs_bridge.build_message_request(sample_cael_dict, direction="input")
        assert req["method"] == "steps/message"
        assert "input" in req["params"]["action"]["method"]


# ── Memory Vaccine ACS Export ─────────────────────────────────────────────────

class TestMemoryVaccineACSExport:
    """MemoryVaccine.to_acs_guardian_context() integration."""

    def test_acs_context_export_contains_required_fields(self, vaccine):
        result = vaccine.validate_write(
            "Normal operational content",
            MemoryZone.CROSS_SESSION,
            AGENT_DID,
        )
        ctx = vaccine.to_acs_guardian_context(
            "Normal operational content", MemoryZone.CROSS_SESSION, AGENT_DID, result
        )
        assert "source_did" in ctx
        assert "zone" in ctx

    def test_acs_context_includes_drift_score_when_allowed(self, vaccine):
        result = vaccine.validate_write("content", MemoryZone.CROSS_SESSION, AGENT_DID)
        ctx = vaccine.to_acs_guardian_context("content", MemoryZone.CROSS_SESSION, AGENT_DID, result)
        if result.allowed:
            assert "drift_score" in ctx

    def test_validate_write_with_guardian_returns_tuple(self, vaccine):
        decision, guardian_ctx = vaccine.validate_write_with_guardian(
            "Test memory content",
            MemoryZone.CROSS_SESSION,
            AGENT_DID,
        )
        assert decision is not None
        assert isinstance(guardian_ctx, dict)
        assert "zone" in guardian_ctx

    def test_acs_context_zone_matches_request_zone(self, vaccine):
        _, ctx = vaccine.validate_write_with_guardian(
            "content", MemoryZone.PERMANENT, AGENT_DID, mandate_id="mand_001"
        )
        assert ctx["zone"] == MemoryZone.PERMANENT.value


# ── Integration Stack ─────────────────────────────────────────────────────────

class TestIntegrationStack:
    """End-to-end: CAEL -> Guardian -> NOR -> OTel. No network required."""

    def test_full_tool_call_pipeline(self):
        """
        Complete pipeline for a tool call:
        1. Build CAEL tool call
        2. Evaluate with Guardian (inline)
        3. Build NOR from verdict
        4. Export NOR to OTel (in-memory)
        5. Assert audit trail completeness
        """
        # Step 1: CAEL tool call
        tc = CAELToolCall(
            tool_name="github:search",
            arguments={"query": "nexus-a2a security"},
            requested_by_did=AGENT_DID,
            context_compartment=ContextCompartment.TASK_CONTEXT,
            vcc_id=VCC_ID,
        )
        tc.joulework = JouleWorkCost.compute(800)

        # Step 2: Guardian evaluation
        guardian = GuardianPolicy()
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name=tc.tool_name,
            tool_arguments=tc.arguments,
            vcc_id=VCC_ID,
            vcc_capabilities=["github:search"],
            parent_vcc_capabilities=["github:search", "github:read"],
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.allowed is True

        # Step 3: Build NOR
        nor = build_tool_call_nor(
            AGENT_DID, SPIFFE_ID, tc.tool_name,
            outcome=verdict.decision.value,
            vcc_id=VCC_ID,
            guardian_step_id=ctx.step_id,
            guardian_nor_fingerprint=verdict.nor_fingerprint,
            joulework_cost=tc.joulework.estimated_cost_jw if tc.joulework else None,
        )

        # Step 4: OTel export
        exporter = InMemoryNORExporter()
        attrs = exporter.export(nor)

        # Step 5: Audit completeness assertions
        assert len(exporter.spans) == 1
        assert attrs["nexus.nor.agent_did"] == AGENT_DID
        assert attrs["nexus.nor.outcome"] == "allow"
        assert attrs["nexus.nor.guardian.step_id"] == ctx.step_id
        assert attrs["nexus.nor.guardian.fingerprint"] == verdict.nor_fingerprint

    def test_full_memory_write_pipeline(self):
        """
        Memory write pipeline:
        1. MemoryVaccine validates + generates Guardian context
        2. ACS bridge builds Guardian request
        3. Inline Guardian evaluates
        4. NOR records the outcome
        """
        vaccine = MemoryVaccine(
            agent_did=AGENT_DID,
            purpose_declaration="Orchestrate cybersecurity research",
            use_stub_embeddings=True,
        )
        decision, guardian_ctx = vaccine.validate_write_with_guardian(
            "Competitor launched new AI governance product",
            MemoryZone.CROSS_SESSION,
            AGENT_DID,
        )
        assert decision.allowed is True
        assert guardian_ctx["zone"] == MemoryZone.CROSS_SESSION.value

        # ACS bridge builds Guardian request with provenance
        bridge = NEXUSACSBridge()
        req = bridge.build_memory_store_request(
            ["Competitor launched new AI governance product"],
            AGENT_DID,
            guardian_ctx,
        )
        assert req["params"]["nexus"]["memoryProvenance"]["source_did"] == AGENT_DID

        # NOR records the outcome
        nor = build_memory_nor(
            AGENT_DID, SPIFFE_ID,
            zone=guardian_ctx["zone"],
            outcome="allow",
            drift_score=guardian_ctx.get("drift_score"),
        )
        exporter = InMemoryNORExporter()
        exporter.export(nor)
        assert len(exporter.spans) == 1

    def test_mcp_server_discovery_triggers_agbom_update(self):
        """
        MCP server discovery creates AgBOM version + NOR audit event.
        Production: publish AgBOM to ANS on each version.
        """
        agbom = AgBOMManager(AGENT_DID)
        exporter = InMemoryNORExporter()

        # Discover an MCP server
        version = agbom.discover_mcp_server(
            "new-api-server", "https://api.mcp.example.com",
            tool_manifest_digest="sha256:def456",
        )

        # Record the discovery as a NOR audit event
        nor = build_tool_call_nor(
            AGENT_DID, SPIFFE_ID,
            tool_name="agbom:mcp_server_discovered",
            outcome="allow",
            session_id="sess-discovery",
        )
        attrs = exporter.export(nor)

        assert agbom.current_version == 1
        assert version.signature is not None
        assert len(exporter.spans) == 1

    def test_acs_bridge_factory_accessible(self):
        bridge = ProtocolBridgeFactory.get_bridge("acs")
        assert isinstance(bridge, NEXUSACSBridge)

    def test_acs_bridge_auto_detected_from_guardian_url(self):
        protocol = ProtocolBridgeFactory.detect_protocol(
            {"guardian_url": "https://guardian.nexus.csi.gov:8443"}
        )
        assert protocol == "acs"


# ── SAFE2 v0.3 Compliance ─────────────────────────────────────────────────────

class TestSAFE2v03Compliance:
    """
    v0.3 additions close the remaining P4 gap (4/5 -> 5/5 target).
    These tests validate that the new modules satisfy the specific SAFE2 controls
    that were partial or missing in v0.2.
    """

    def test_p4_m4_6_emergence_detection_agbom_unsigned_count(self):
        """M4.6: Behavioral analytics observable - unsigned MCP servers detectable."""
        agbom = AgBOMManager(AGENT_DID)
        agbom.discover_mcp_server("untrusted", "https://u.mcp", signed=False)
        native = agbom.to_dict()
        assert native["unsigned_mcp_server_count"] >= 1

    def test_p4_m4_8_bias_as_security_observable_via_drift(self):
        """M4.8: Belief drift is a security observable - detectable via Memory Vaccine."""
        vaccine = MemoryVaccine(
            agent_did=AGENT_DID,
            purpose_declaration="Cybersecurity analysis",
            use_stub_embeddings=True,
        )
        result = vaccine.validate_write(
            "DRIFT_HIGH: content far from purpose",
            MemoryZone.CROSS_SESSION,
            AGENT_DID,
        )
        # Drift score is observable (whether allowed or blocked)
        assert result.drift_score is not None

    def test_p1_s1_3_guardian_per_call_argument_inspection(self):
        """S1.3: Per-call argument inspection at L3 (Guardian fills the gap)."""
        guardian = GuardianPolicy()
        ctx = build_tool_call_step(
            AGENT_DID, SPIFFE_ID,
            tool_name="filesystem:read",
            tool_arguments={"path": "/etc/passwd"},
        )
        verdict = guardian.evaluate(ctx)
        assert verdict.denied is True

    def test_p2_a2_5_nor_execution_trace_complete(self):
        """A2.5: Every allowed action has a non-repudiable NOR with full provenance."""
        nor = build_tool_call_nor(
            AGENT_DID, SPIFFE_ID, "search:web", "allow",
            vcc_id=VCC_ID, delegation_depth=1,
        )
        nor.sign()
        assert nor.receipt_id is not None
        assert nor.receipt_hash is not None
        assert nor.signature is not None
        assert nor.agent_did == AGENT_DID

    def test_p2_a2_3_agbom_supply_chain_provenance(self):
        """A2.3: Supply chain integrity via signed AgBOM with capability digest."""
        agbom = AgBOMManager(AGENT_DID)
        agbom.discover_mcp_server(
            "nca-verified-server", "https://nca.csi.gov/mcp",
            tool_manifest_digest="sha256:abc123",
            signed=True,
        )
        cdx = agbom.to_cyclonedx()
        components = cdx["components"]
        assert len(components) == 1
        hashes = components[0].get("hashes", [])
        assert any(h["alg"] == "SHA-256" for h in hashes)

    def test_p3_f3_1_guardian_inline_deny_prevents_execution(self):
        """F3.1: Fail-safe requires that Guardian deny prevents action execution."""
        guardian = GuardianPolicy(revoked_dids=[AGENT_DID])
        ctx = build_tool_call_step(AGENT_DID, SPIFFE_ID, "any:tool", {})
        verdict = guardian.evaluate(ctx)
        # Deny = execution must not proceed
        assert verdict.denied is True
        assert verdict.allowed is False

    def test_p5_l6_agbom_hash_chain_self_evolution_audit(self):
        """L6 readiness: AgBOM hash chain provides cryptographic amendment audit."""
        agbom = AgBOMManager(AGENT_DID)
        agbom.discover_mcp_server("v1", "https://v1.mcp")
        agbom.discover_mcp_server("v2", "https://v2.mcp")
        is_valid, violations = agbom.verify_chain_integrity()
        assert is_valid is True

    def test_version_bump_to_0_3_0(self):
        """SDK version must be bumped to 0.3.0 in __init__."""
        import nexus_sdk
        assert nexus_sdk.__version__ == "0.3.0"

    def test_guardian_module_importable_from_sdk_root(self):
        from nexus_sdk import GuardianPolicy, GuardianVerdict, StepMethod
        assert GuardianPolicy is not None
        assert GuardianVerdict.ALLOW == "allow"

    def test_otel_module_importable_from_sdk_root(self):
        from nexus_sdk import InMemoryNORExporter, NEXUSOutputReceipt
        assert InMemoryNORExporter is not None

    def test_agbom_module_importable_from_sdk_root(self):
        from nexus_sdk import AgBOMManager, AgBOMComponentType
        assert AgBOMManager is not None

    def test_acs_bridge_importable_from_sdk_root(self):
        from nexus_sdk import NEXUSACSBridge
        assert NEXUSACSBridge is not None


if __name__ == "__main__":
    print("Run with: pytest tests/test_nexus_v03.py -v")
    print("Run all:  pytest tests/ -v")
