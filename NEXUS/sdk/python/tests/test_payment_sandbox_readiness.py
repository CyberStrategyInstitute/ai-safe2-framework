"""Adversarial tests for Sandbox Rail Readiness."""

import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.execution_plane import GatewayReadiness
from nexus_sdk.payments.sandbox_readiness import (
    RailActivationMode,
    SandboxRailReadinessGate,
    SandboxReadinessProfile,
    SandboxRunEvidence,
)

NOW = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
KEY = b"sandbox-readiness-proof-key"


class Verifier:
    def seal(self, evidence):
        return hmac.new(KEY, evidence.evidence_digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, evidence):
        return hmac.compare_digest(self.seal(evidence), evidence.proof)


def profile():
    return SandboxReadinessProfile(
        profile_id="sandbox-readiness-1",
        contract_digest="sha256:contract-1",
        binding_digest="sha256:binding-1",
        policy_stack_digest="sha256:policy-stack-1",
        execution_profile_digest="sha256:execution-profile-1",
        trusted_observer_id="sandbox-observer-1",
        trusted_counterparties=frozenset({"facilitator-a", "facilitator-b"}),
        minimum_counterparties=2,
    )


def outcomes(value=True):
    return tuple((name, value) for name in sorted(profile().required_outcomes))


def evidence(run_id, counterparty, environment, **changes):
    value = SandboxRunEvidence(
        run_id=run_id,
        counterparty_id=counterparty,
        environment_id=environment,
        contract_digest="sha256:contract-1",
        binding_digest="sha256:binding-1",
        policy_stack_digest="sha256:policy-stack-1",
        execution_profile_digest="sha256:execution-profile-1",
        conformance_report_digest=f"sha256:conformance-{run_id}",
        outcomes=outcomes(),
        started_at=(NOW - timedelta(minutes=5)).isoformat(),
        completed_at=(NOW - timedelta(minutes=1)).isoformat(),
        observer_id="sandbox-observer-1",
        sandbox_only=True,
        production_credentials_used=False,
        real_value_moved=False,
        payloads_omitted=True,
        proof="",
    )
    value = replace(value, **changes)
    return replace(value, proof=Verifier().seal(value))


def gate(verifier=None):
    return SandboxRailReadinessGate(
        profile=profile(), verifier=verifier or Verifier(), now=lambda: NOW
    )


READY = GatewayReadiness(ready=True, missing=(), reference_only=())
REFERENCE_ONLY = GatewayReadiness(
    ready=False, missing=(), reference_only=("authority_store",)
)


def passing_runs():
    return (
        evidence("run-a", "facilitator-a", "sandbox-a"),
        evidence("run-b", "facilitator-b", "sandbox-b"),
    )


def test_two_independent_runs_and_ready_gateway_allow_enforced_mode():
    report = gate().evaluate(passing_runs(), gateway_readiness=READY)
    assert report.ready_for_enforcement
    assert report.maximum_mode is RailActivationMode.ENFORCED
    assert report.findings == ()
    assert len(report.accepted_run_digests) == 2


def test_one_passing_run_permits_observe_only_not_enforcement():
    report = gate().evaluate(passing_runs()[:1], gateway_readiness=READY)
    assert not report.ready_for_enforcement
    assert report.maximum_mode is RailActivationMode.OBSERVE_ONLY
    assert "counterparty threshold" in " ".join(report.findings)


def test_reference_only_gateway_cannot_reach_enforced_mode():
    report = gate().evaluate(passing_runs(), gateway_readiness=REFERENCE_ONLY)
    assert report.maximum_mode is RailActivationMode.OBSERVE_ONLY
    assert "not deployment-ready" in " ".join(report.findings)


def test_no_authenticated_run_keeps_rail_disabled():
    report = gate().evaluate((), gateway_readiness=READY)
    assert report.maximum_mode is RailActivationMode.DISABLED
    assert "no authenticated" in " ".join(report.findings)


@pytest.mark.parametrize("field,value,expected", [
    ("contract_digest", "sha256:other", "contract digest"),
    ("binding_digest", "sha256:other", "binding digest"),
    ("policy_stack_digest", "sha256:other", "policy stack"),
    ("execution_profile_digest", "sha256:other", "execution profile"),
    ("observer_id", "attacker-observer", "observer identity"),
    ("counterparty_id", "attacker-facilitator", "not trusted"),
    ("sandbox_only", False, "sandbox-only"),
    ("production_credentials_used", True, "production credentials"),
    ("real_value_moved", True, "real value"),
    ("payloads_omitted", False, "minimize"),
])
def test_identity_safety_and_privacy_mutations_block_enforcement(field, value, expected):
    attacked = evidence("run-a", "facilitator-a", "sandbox-a", **{field: value})
    report = gate().evaluate((attacked, passing_runs()[1]), gateway_readiness=READY)
    assert not report.ready_for_enforcement
    assert expected in " ".join(report.findings)


def test_missing_or_failed_required_outcome_blocks_enforcement():
    required = sorted(profile().required_outcomes)
    missing = evidence(
        "run-a", "facilitator-a", "sandbox-a",
        outcomes=tuple((name, True) for name in required[1:]),
    )
    failed_outcomes = tuple((name, name != required[0]) for name in required)
    failed = evidence(
        "run-b", "facilitator-b", "sandbox-b", outcomes=failed_outcomes
    )
    report = gate().evaluate((missing, failed), gateway_readiness=READY)
    assert report.maximum_mode is RailActivationMode.DISABLED
    assert "missing" in " ".join(report.findings)
    assert "failed" in " ".join(report.findings)


def test_identical_duplicate_run_is_idempotent_not_independent_evidence():
    first = passing_runs()[0]
    report = gate().evaluate((first, first), gateway_readiness=READY)
    assert len(report.accepted_run_digests) == 1
    assert report.maximum_mode is RailActivationMode.OBSERVE_ONLY


def test_conflicting_same_run_id_blocks_enforcement():
    first, second = passing_runs()
    conflict = evidence("run-a", "facilitator-b", "sandbox-b")
    report = gate().evaluate((first, second, conflict), gateway_readiness=READY)
    assert not report.ready_for_enforcement
    assert "conflicting run evidence" in " ".join(report.findings)


def test_stale_future_and_excessive_duration_are_rejected():
    values = (
        evidence(
            "stale", "facilitator-a", "sandbox-a",
            completed_at=(NOW - timedelta(days=2)).isoformat(),
            started_at=(NOW - timedelta(days=2, minutes=5)).isoformat(),
        ),
        evidence(
            "future", "facilitator-a", "sandbox-a",
            completed_at=(NOW + timedelta(seconds=1)).isoformat(),
        ),
        evidence(
            "long", "facilitator-a", "sandbox-a",
            started_at=(NOW - timedelta(hours=2)).isoformat(),
        ),
    )
    for item in values:
        report = gate().evaluate((item,), gateway_readiness=READY)
        assert report.maximum_mode is RailActivationMode.DISABLED


def test_forged_or_unavailable_proof_keeps_rail_disabled():
    forged = replace(passing_runs()[0], proof="forged")

    class BrokenVerifier(Verifier):
        def verify(self, item):
            raise RuntimeError("trust root unavailable")

    assert gate().evaluate((forged,), gateway_readiness=READY).maximum_mode is RailActivationMode.DISABLED
    assert gate(BrokenVerifier()).evaluate(
        (passing_runs()[0],), gateway_readiness=READY
    ).maximum_mode is RailActivationMode.DISABLED


def test_unknown_or_digest_hostile_evidence_is_a_finding_not_an_exception():
    malformed = replace(passing_runs()[0], outcomes=None)
    report = gate().evaluate(
        ({"decision": "enforced"}, malformed), gateway_readiness=READY
    )
    assert report.maximum_mode is RailActivationMode.DISABLED
    assert "unknown sandbox evidence type" in report.findings
    assert "evidence is malformed" in " ".join(report.findings)


def test_report_omits_payloads_and_credentials():
    report = gate().evaluate(passing_runs(), gateway_readiness=READY).to_dict()
    serialized = repr(report).lower()
    assert "payloads and credentials omitted" in report["privacy"]
    assert "proof" not in serialized
    assert "account" not in serialized
