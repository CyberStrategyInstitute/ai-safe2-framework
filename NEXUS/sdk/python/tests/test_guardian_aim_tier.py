"""Registry-bound ACT tiers (AIM v0.3; IETF draft section 3.1.1).

Before: Guardian took act_tier from the request. An agent registered as ACT-4 could
declare ACT-1 and skip HEAR. Omitting the tier was the only case covered (interim
ACT-4 floor). Now, with an AIM registry configured, the registered tier governs.
"""
import json
from pathlib import Path

import pytest

from nexus_sdk.aim import AIMRegistry, AIMValidationError, aim_digest
from nexus_sdk.guardian import GuardianPolicy, GuardianVerdict, NEXUSGuardianClient, build_tool_call_step

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "aim-v0.3.schema.json"
THIN = "x"
REAL = "Ticket OPS-12 approved by owner; staging only; rollback plan R-4 recorded."


def aim(did, tier, **extra):
    doc = {
        "agentDID": did,
        "spiffeID": "spiffe://nexus.local/agent/" + did.rsplit(":", 1)[-1],
        "agentClass": "orchestrator",
        "maturityLevel": "senior",
        "ownerChain": "did:nexus:human:owner",
        "purposeDeclaration": "Operate deployments for the platform team.",
        "jurisdictionProfile": "US",
        "pqcPublicKeys": {"mldsa65": "stub"},
        "actTier": tier,
        "signature": "stub",
    }
    doc.update(extra)
    return doc


@pytest.fixture
def registry():
    r = AIMRegistry()
    r.register(aim("did:nexus:agent:orch", 4))
    r.register(aim("did:nexus:agent:helper", 1))
    return r


def evaluate(registry, did, tier, reasoning=None, digest=None):
    g = NEXUSGuardianClient(inline_policy=GuardianPolicy(aim_registry=registry),
                            fail_mode=NEXUSGuardianClient.FAIL_CLOSED)
    step = build_tool_call_step(agent_did=did, spiffe_id="spiffe://nexus.local/agent/x", tool_name="deploy",
                                tool_arguments={"env": "staging"}, act_tier=tier, reasoning=reasoning)
    step.agent.aim_digest = digest
    return g.evaluate(step)


def test_registered_act4_cannot_claim_act1_to_skip_hear(registry):
    v = evaluate(registry, "did:nexus:agent:orch", tier=1, reasoning=None)
    assert v.decision == GuardianVerdict.DENY
    assert "REASONING_REQUIRED" in v.reason_codes and "ACT_TIER_FROM_REGISTRY" in v.reason_codes


def test_registered_act4_with_thin_reasoning_still_denied(registry):
    v = evaluate(registry, "did:nexus:agent:orch", tier=1, reasoning=THIN)
    assert v.decision == GuardianVerdict.DENY and "REASONING_INSUFFICIENT" in v.reason_codes


def test_registered_act4_with_real_reasoning_allowed(registry):
    assert evaluate(registry, "did:nexus:agent:orch", tier=4, reasoning=REAL).decision == GuardianVerdict.ALLOW


def test_claim_above_registered_tier_denied(registry):
    v = evaluate(registry, "did:nexus:agent:helper", tier=3, reasoning=REAL)
    assert v.decision == GuardianVerdict.DENY and "ACT_TIER_EXCEEDS_REGISTERED" in v.reason_codes


def test_registered_act1_omitting_tier_is_not_treated_as_act4(registry):
    # The registry answers the question the interim floor had to guess.
    assert evaluate(registry, "did:nexus:agent:helper", tier=None).decision == GuardianVerdict.ALLOW


def test_unregistered_agent_denied(registry):
    v = evaluate(registry, "did:nexus:agent:ghost", tier=1)
    assert v.decision == GuardianVerdict.DENY and "AIM_NOT_REGISTERED" in v.reason_codes


def test_presented_digest_must_match_registered_aim(registry):
    good = aim_digest(aim("did:nexus:agent:helper", 1))
    assert evaluate(registry, "did:nexus:agent:helper", tier=1, digest=good).decision == GuardianVerdict.ALLOW
    v = evaluate(registry, "did:nexus:agent:helper", tier=1, digest="0" * 64)
    assert v.decision == GuardianVerdict.DENY and "AIM_DIGEST_MISMATCH" in v.reason_codes


def test_without_registry_interim_floor_still_applies():
    g = NEXUSGuardianClient(inline_policy=GuardianPolicy(), fail_mode=NEXUSGuardianClient.FAIL_CLOSED)
    step = build_tool_call_step(agent_did="did:nexus:agent:x", spiffe_id="spiffe://nexus.local/agent/x",
                                tool_name="deploy", tool_arguments={}, act_tier=None)
    v = g.evaluate(step)
    assert v.decision == GuardianVerdict.DENY and "ACT_TIER_UNDECLARED" in v.reason_codes


@pytest.mark.parametrize("bad", [0, 5, "4", None, 2.5])
def test_registry_rejects_invalid_tier(bad):
    with pytest.raises(AIMValidationError):
        AIMRegistry().register(aim("did:nexus:agent:bad", bad))


def test_registry_rejects_missing_required_fields():
    doc = aim("did:nexus:agent:bad", 2)
    del doc["ownerChain"]
    with pytest.raises(AIMValidationError):
        AIMRegistry().register(doc)


def test_raising_a_tier_is_a_recorded_new_aim_version(registry):
    before = registry.resolve("did:nexus:agent:helper")
    registry.register(aim("did:nexus:agent:helper", 3))
    after = registry.resolve("did:nexus:agent:helper")
    assert (before.act_tier, after.act_tier) == (1, 3)
    assert after.aim_digest != before.aim_digest
    assert [r.act_tier for r in registry.history("did:nexus:agent:helper")] == [1, 3]


def test_schema_v03_requires_act_tier_and_matches_registry():
    schema = json.loads(SCHEMA.read_text())
    assert "actTier" in schema["required"]
    assert schema["properties"]["actTier"] == {"type": "integer", "minimum": 1, "maximum": 4,
                                               "description": schema["properties"]["actTier"]["description"]}
    v02 = json.loads((SCHEMA.parent / "aim-v0.2.schema.json").read_text())
    assert set(v02["required"]) <= set(schema["required"])


def test_registry_required_fields_match_schema():
    from nexus_sdk.aim import AIM_V03_REQUIRED
    assert list(AIM_V03_REQUIRED) == json.loads(SCHEMA.read_text())["required"]


def test_opa_export_matches_policy_contract(registry):
    # nexus-authz.rego and nexus-aism-invariants.rego read
    # data.nexus.aim.required and data.nexus.aim.agents[<did>].act_tier.
    data = registry.to_opa_data()
    assert data["required"] is True
    assert data["agents"]["did:nexus:agent:orch"]["act_tier"] == 4
    assert data["agents"]["did:nexus:agent:helper"]["act_tier"] == 1
    opa_dir = Path(__file__).resolve().parents[3] / "opa"
    for policy in ("nexus-authz.rego", "nexus-aism-invariants.rego"):
        text = (opa_dir / policy).read_text()
        assert "data.nexus.aim.agents[" in text and ".act_tier" in text
