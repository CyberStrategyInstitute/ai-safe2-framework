"""Adversarial tests for Deployment Proof & Readiness."""

import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.deployment_readiness import (
    DeploymentApprovalEvidence,
    DeploymentControlEvidence,
    DeploymentReadinessAuthority,
    DeploymentReadinessProfile,
)
from nexus_sdk.payments.execution_plane import ComponentAssurance, GatewayReadiness
from nexus_sdk.payments.objects import canonical_hash
from nexus_sdk.payments.sandbox_readiness import RailActivationMode, SandboxReadinessReport

NOW = datetime(2026, 9, 27, 16, 0, 0, tzinfo=timezone.utc)
KEY = b"deployment-readiness-test-key"
READY = GatewayReadiness(ready=True, missing=(), reference_only=())


class Verifier:
    assurance = ComponentAssurance.DEPLOYMENT

    def seal(self, evidence):
        return hmac.new(KEY, evidence.evidence_digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, evidence):
        return hmac.compare_digest(self.seal(evidence), evidence.proof)


class ApprovalVerifier:
    assurance = ComponentAssurance.DEPLOYMENT

    def seal(self, approval):
        return hmac.new(KEY, approval.approval_digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, approval):
        return hmac.compare_digest(self.seal(approval), approval.proof)


class Issuer:
    authority_id = "deployment-authority-1"
    assurance = ComponentAssurance.DEPLOYMENT

    def seal(self, decision):
        return hmac.new(KEY, decision.decision_digest.encode(), hashlib.sha256).hexdigest()


def sandbox_report(**changes):
    report = SandboxReadinessReport(
        maximum_mode=RailActivationMode.ENFORCED,
        ready_for_enforcement=True,
        profile_digest="sha256:sandbox-profile-1",
        accepted_run_digests=("sha256:run-a", "sha256:run-b"),
        counterparties=("facilitator-a", "facilitator-b"),
        environments=("sandbox-a", "sandbox-b"),
        findings=(),
    )
    return replace(report, **changes)


def profile():
    return DeploymentReadinessProfile(
        profile_id="production-readiness-1",
        deployment_id="gateway-east-1",
        environment_id="production-east",
        software_digest="sha256:software-1",
        configuration_digest="sha256:configuration-1",
        policy_profile_digest="sha256:policy-parity-1",
        sandbox_profile_digest="sha256:sandbox-profile-1",
        accountable_owner_id="payments-owner",
        security_owner_id="security-owner",
        data_owner_id="evidence-owner",
        data_jurisdiction="US",
        authority_id="deployment-authority-1",
        trusted_assessors=frozenset({"assessor-a", "assessor-b"}),
        authorized_approvers=frozenset({"change-approver"}),
    )


def approval(**changes):
    value = DeploymentApprovalEvidence(
        approval_id="approval-1",
        deployment_id="gateway-east-1",
        environment_id="production-east",
        profile_digest=profile().profile_digest,
        approver_id="change-approver",
        approved_mode=RailActivationMode.ENFORCED.value,
        approved_at=(NOW - timedelta(minutes=2)).isoformat(),
        expires_at=(NOW + timedelta(minutes=30)).isoformat(),
        proof="",
    )
    value = replace(value, **changes)
    return replace(value, proof=ApprovalVerifier().seal(value))


def artifact_for(control_id, gateway=READY, sandbox=None):
    if control_id == "execution_plane_ready":
        return canonical_hash({
            "ready": gateway.ready,
            "missing": list(gateway.missing),
            "reference_only": list(gateway.reference_only),
        })
    if control_id == "sandbox_enforced_ready":
        return canonical_hash((sandbox or sandbox_report()).to_dict())
    if control_id == "policy_parity_live":
        return profile().policy_profile_digest
    return f"sha256:artifact-{control_id}"


def evidence(control_id, index, **changes):
    value = DeploymentControlEvidence(
        evidence_id=f"evidence-{control_id}",
        control_id=control_id,
        deployment_id="gateway-east-1",
        environment_id="production-east",
        software_digest="sha256:software-1",
        configuration_digest="sha256:configuration-1",
        policy_profile_digest="sha256:policy-parity-1",
        sandbox_profile_digest="sha256:sandbox-profile-1",
        artifact_digest=artifact_for(control_id),
        assessor_id="assessor-a" if index % 2 == 0 else "assessor-b",
        observed_at=(NOW - timedelta(minutes=5)).isoformat(),
        passed=True,
        proof="",
    )
    value = replace(value, **changes)
    return replace(value, proof=Verifier().seal(value))


def passing_evidence():
    return tuple(
        evidence(control_id, index)
        for index, control_id in enumerate(sorted(profile().required_controls))
    )


def authority(verifier=None, approval_verifier=None, issuer=None):
    return DeploymentReadinessAuthority(
        profile=profile(),
        verifier=verifier or Verifier(),
        approval_verifier=approval_verifier or ApprovalVerifier(),
        issuer=issuer or Issuer(),
        now=lambda: NOW,
    )


def assess(items=None, **changes):
    return authority().assess(
        passing_evidence() if items is None else items,
        gateway_readiness=changes.get("gateway_readiness", READY),
        sandbox_report=changes.get("sandbox_report", sandbox_report()),
        approval=changes.get("approval", approval()),
    )


def test_complete_independent_proof_issues_signed_enforced_decision():
    decision = assess()
    assert decision.ready
    assert decision.maximum_mode is RailActivationMode.ENFORCED
    assert decision.findings == ()
    assert decision.assessor_ids == ("assessor-a", "assessor-b")
    assert decision.approval_digest == approval().approval_digest
    assert decision.proof == Issuer().seal(replace(decision, proof=""))


@pytest.mark.parametrize("control_id", sorted(profile().required_controls))
def test_every_required_control_is_fail_closed(control_id):
    remaining = tuple(item for item in passing_evidence() if item.control_id != control_id)
    decision = assess(remaining)
    assert not decision.ready
    assert decision.maximum_mode is RailActivationMode.DISABLED
    assert control_id in " ".join(decision.findings)
    assert decision.proof


@pytest.mark.parametrize("field,value,expected", [
    ("deployment_id", "attacker-deployment", "deployment identity"),
    ("environment_id", "attacker-environment", "environment identity"),
    ("software_digest", "sha256:attacker", "software digest"),
    ("configuration_digest", "sha256:attacker", "configuration digest"),
    ("policy_profile_digest", "sha256:attacker", "policy profile"),
    ("sandbox_profile_digest", "sha256:attacker", "sandbox profile"),
    ("assessor_id", "attacker", "not trusted"),
    ("passed", False, "explicitly pass"),
])
def test_identity_configuration_and_result_mutations_block_readiness(field, value, expected):
    items = list(passing_evidence())
    items[0] = evidence(items[0].control_id, 0, **{field: value})
    decision = assess(tuple(items))
    assert not decision.ready
    assert expected in " ".join(decision.findings)


def test_reference_only_or_missing_execution_component_blocks_readiness():
    for gateway in (
        GatewayReadiness(False, (), ("credential_broker",)),
        GatewayReadiness(False, ("evidence_ledger",), ()),
    ):
        decision = assess(gateway_readiness=gateway)
        assert not decision.ready
        assert "execution plane" in " ".join(decision.findings)


def test_unknown_gateway_or_sandbox_result_types_are_signed_refusals():
    for gateway, report in (({"ready": True}, sandbox_report()), (READY, {"ready": True})):
        decision = authority().assess(
            passing_evidence(), gateway_readiness=gateway,
            sandbox_report=report, approval=approval(),
        )
        assert not decision.ready
        assert "unknown type" in " ".join(decision.findings)
        assert decision.proof


def test_observe_only_failed_or_wrong_sandbox_report_blocks_readiness():
    reports = (
        sandbox_report(maximum_mode=RailActivationMode.OBSERVE_ONLY,
                       ready_for_enforcement=False),
        sandbox_report(findings=("negative path failed",)),
        sandbox_report(profile_digest="sha256:attacker"),
    )
    for report in reports:
        decision = assess(sandbox_report=report)
        assert not decision.ready
        assert "sandbox" in " ".join(decision.findings)


def test_special_evidence_must_bind_exact_gateway_sandbox_and_policy_artifacts():
    for control_id in (
        "execution_plane_ready", "sandbox_enforced_ready", "policy_parity_live"
    ):
        items = list(passing_evidence())
        index = next(i for i, item in enumerate(items) if item.control_id == control_id)
        items[index] = evidence(control_id, index, artifact_digest="sha256:substitute")
        decision = assess(tuple(items))
        assert not decision.ready
        assert "bound artifact digest mismatch" in " ".join(decision.findings)


def test_forged_stale_future_and_naive_evidence_are_rejected():
    base = passing_evidence()
    attacks = (
        replace(base[0], proof="forged"),
        evidence(base[0].control_id, 0,
                 observed_at=(NOW - timedelta(days=2)).isoformat()),
        evidence(base[0].control_id, 0,
                 observed_at=(NOW + timedelta(seconds=1)).isoformat()),
        evidence(base[0].control_id, 0,
                 observed_at=(NOW - timedelta(minutes=1)).replace(tzinfo=None).isoformat()),
    )
    for attacked in attacks:
        decision = assess((attacked,) + base[1:])
        assert not decision.ready


def test_duplicate_conflicting_and_unknown_evidence_cannot_outvote_controls():
    base = passing_evidence()
    duplicate = evidence(
        base[0].control_id, 1, evidence_id="evidence-duplicate-control"
    )
    conflict = evidence(base[0].control_id, 0, evidence_id=base[0].evidence_id,
                        artifact_digest="sha256:conflict")
    decision = assess(base + (duplicate, conflict, {"passed": True}))
    assert not decision.ready
    joined = " ".join(decision.findings)
    assert "duplicate control evidence" in joined
    assert "conflicting evidence identity" in joined
    assert "unknown deployment evidence type" in joined


def test_one_assessor_or_unapproved_change_authority_blocks_readiness():
    one_assessor = tuple(
        evidence(item.control_id, 0, assessor_id="assessor-a")
        for item in passing_evidence()
    )
    assert "assessor threshold" in " ".join(assess(one_assessor).findings)
    assert "not authorized" in " ".join(
        assess(approval=approval(approver_id="agent-self-approval")).findings
    )


@pytest.mark.parametrize("changes,expected", [
    ({"deployment_id": "attacker"}, "deployment identity"),
    ({"environment_id": "attacker"}, "environment identity"),
    ({"profile_digest": "sha256:attacker"}, "profile digest"),
    ({"approved_mode": RailActivationMode.OBSERVE_ONLY.value}, "enforced mode"),
    ({"approved_at": (NOW + timedelta(seconds=1)).isoformat()}, "currently valid"),
    ({"expires_at": NOW.isoformat()}, "currently valid"),
])
def test_approval_is_exact_fresh_and_bound(changes, expected):
    decision = assess(approval=approval(**changes))
    assert not decision.ready
    assert expected in " ".join(decision.findings)


def test_forged_unknown_or_unavailable_approval_fails_closed():
    forged = replace(approval(), proof="forged")

    class BrokenApprovalVerifier(ApprovalVerifier):
        def verify(self, item):
            raise RuntimeError("approval authority unavailable")

    assert "approval proof" in " ".join(assess(approval=forged).findings)
    assert "unknown approval" in " ".join(assess(approval={"approver": "change-approver"}).findings)
    decision = authority(approval_verifier=BrokenApprovalVerifier()).assess(
        passing_evidence(), gateway_readiness=READY,
        sandbox_report=sandbox_report(), approval=approval(),
    )
    assert not decision.ready
    assert "approval proof" in " ".join(decision.findings)


def test_reference_verifier_or_issuer_and_wrong_authority_fail_closed():
    class ReferenceVerifier(Verifier):
        assurance = ComponentAssurance.REFERENCE

    class ReferenceIssuer(Issuer):
        assurance = ComponentAssurance.REFERENCE

    class WrongIssuer(Issuer):
        authority_id = "attacker-authority"

    for candidate in (
        DeploymentReadinessAuthority(
            profile=profile(), verifier=ReferenceVerifier(),
            approval_verifier=ApprovalVerifier(), issuer=Issuer(), now=lambda: NOW
        ),
        DeploymentReadinessAuthority(
            profile=profile(), verifier=Verifier(),
            approval_verifier=ApprovalVerifier(), issuer=ReferenceIssuer(), now=lambda: NOW
        ),
        DeploymentReadinessAuthority(
            profile=profile(), verifier=Verifier(),
            approval_verifier=ApprovalVerifier(), issuer=WrongIssuer(), now=lambda: NOW
        ),
    ):
        decision = candidate.assess(
            passing_evidence(), gateway_readiness=READY,
            sandbox_report=sandbox_report(), approval=approval(),
        )
        assert not decision.ready


def test_unavailable_or_empty_issuer_never_returns_unsigned_decision():
    class BrokenIssuer(Issuer):
        def seal(self, decision):
            raise RuntimeError("kms unavailable")

    class EmptyIssuer(Issuer):
        def seal(self, decision):
            return ""

    for issuer in (BrokenIssuer(), EmptyIssuer()):
        with pytest.raises(RuntimeError, match="decision|issuer"):
            authority(issuer=issuer).assess(
                passing_evidence(), gateway_readiness=READY,
                sandbox_report=sandbox_report(), approval=approval(),
            )


def test_decision_is_payload_minimized_and_expires():
    payload = assess().to_dict()
    serialized = repr(payload).lower()
    assert payload["privacy"] == "payment payloads, credentials, and account details omitted"
    assert "card_number" not in serialized
    assert "bank_account" not in serialized
    assert datetime.fromisoformat(payload["expires_at"]) == NOW + timedelta(hours=1)


def test_profile_rejects_collapsed_governance_roles():
    with pytest.raises(ValueError, match="separated"):
        replace(profile(), security_owner_id="payments-owner")
    with pytest.raises(ValueError, match="separated"):
        replace(profile(), authorized_approvers=frozenset({"assessor-a"}))
    with pytest.raises(ValueError, match="separated"):
        replace(profile(), required_controls=frozenset({""}))
