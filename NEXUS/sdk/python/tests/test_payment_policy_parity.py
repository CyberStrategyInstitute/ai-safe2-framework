"""Adversarial tests for Policy Parity Guard."""

import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.authority import AuthorityGraph, RevocationPlane
from nexus_sdk.payments.execution_plane import ComponentAssurance
from nexus_sdk.payments.firewall import CounterpartyRegistry, TransactionFirewall
from nexus_sdk.payments.key_guardian import InProcessHMACReceiptAuthenticator
from nexus_sdk.payments.objects import (
    AssuranceLevel,
    AuthorityConstraints,
    AuthorityGrant,
    Money,
    PaymentDecision,
    PaymentRail,
    PaymentReasonCode,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
    canonical_hash,
)
from nexus_sdk.payments.policy_authority import DeterministicPolicyAuthority, PolicyDefinition
from nexus_sdk.payments.policy_parity import (
    DeployedPolicyEvaluation,
    ParityEnforcedPolicyAuthority,
    PolicyParityProfile,
)

NOW = datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)
PROOF_KEY = b"policy-parity-proof-key"
BUNDLE_DIGEST = "sha256:policy-bundle-1"


class InputProvider:
    def build(self, intent, *, runtime, expected_runtime_baseline,
              hear_satisfied_by, now):
        return {
            "intent": intent.to_dict(),
            "runtime": runtime.to_dict() if runtime else None,
            "expected_runtime_baseline": expected_runtime_baseline,
            "hear_satisfied_by": hear_satisfied_by,
            "now": now.isoformat(),
        }


class EvaluationAuthenticator:
    assurance = ComponentAssurance.REFERENCE

    def seal(self, evaluation):
        return hmac.new(
            PROOF_KEY, evaluation.evaluation_digest.encode(), hashlib.sha256
        ).hexdigest()

    def verify(self, evaluation):
        return hmac.compare_digest(self.seal(evaluation), evaluation.proof)


class Evaluator:
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, decision="allow", reasons=(), consequence="routine"):
        self.decision = decision
        self.reasons = tuple(reasons)
        self.consequence = consequence
        self.mutate = {}

    def evaluate(self, document):
        value = DeployedPolicyEvaluation(
            decision=self.decision,
            reason_codes=self.reasons,
            policy_id="policy-1",
            consequence=self.consequence,
            evaluator_id="opa-production-1",
            policy_bundle_digest=BUNDLE_DIGEST,
            input_digest=canonical_hash(document),
            evaluated_at=NOW.isoformat(),
            proof="",
        )
        value = replace(value, **self.mutate)
        return replace(value, proof=EvaluationAuthenticator().seal(value))


class UnavailableEvaluator(Evaluator):
    def evaluate(self, document):
        raise TimeoutError("policy authority timed out")


def configured(*, evaluator=None, authenticator=None):
    graph = AuthorityGraph(revocation=RevocationPlane())
    grant = graph.register_root(AuthorityGrant(
        principal_id="principal-1",
        constraints=AuthorityConstraints(
            max_transaction=Money(10_000, "USD"),
            currencies={"USD"},
            allowed_merchants={"merchant-1"},
            allowed_rails={PaymentRail.CARD_NETWORK},
            min_assurance=AssuranceLevel.RUNTIME_BOUND,
            max_finality=SettlementFinality.REVERSIBLE,
            not_after=(NOW + timedelta(days=1)).isoformat(),
        ),
        capabilities={"payment.execute"},
    ))
    registry = CounterpartyRegistry()
    registry.register_merchant(
        "merchant-1", "sha256:merchant-1", destinations={"destination-1"}
    )
    authority = DeterministicPolicyAuthority(
        firewall=TransactionFirewall(graph, counterparties=registry, policy_id="policy-1"),
        definition=PolicyDefinition(
            policy_id="policy-1",
            ruleset_version="nexus-apay/0.5",
            configuration_digest=BUNDLE_DIGEST,
            evaluator_id="reference-policy-1",
            human_approval_consequences=frozenset(),
        ),
        receipt_issuer=InProcessHMACReceiptAuthenticator(),
    )
    parity = ParityEnforcedPolicyAuthority(
        authority=authority,
        input_provider=InputProvider(),
        evaluator=evaluator or Evaluator(),
        authenticator=authenticator or EvaluationAuthenticator(),
        profile=PolicyParityProfile(
            evaluator_id="opa-production-1",
            policy_id="policy-1",
            policy_bundle_digest=BUNDLE_DIGEST,
            max_evaluation_age_seconds=30,
        ),
        now=lambda: NOW,
    )
    intent = TransactionIntent(
        authority_grant_id=grant.authority_grant_id,
        amount=Money(5_000, "USD"),
        merchant_id="merchant-1",
        merchant_verified=True,
        merchant_baseline_digest="sha256:merchant-1",
        destination="destination-1",
        rail=PaymentRail.CARD_NETWORK,
        finality=SettlementFinality.REVERSIBLE,
        path_assurance=AssuranceLevel.RUNTIME_BOUND,
        nonce="nonce-1",
    )
    intent.approved_cart_digest = intent.canonical_digest()
    runtime = RuntimeMeasurement(
        runtime_measurement_id="runtime-1",
        attested=True,
        attestation_method="tdx",
        measured_at=NOW.isoformat(),
    )
    return parity, intent, runtime


def evaluate(parity, intent, runtime):
    return parity.evaluate(
        intent,
        runtime=runtime,
        expected_runtime_baseline=runtime.baseline_digest(),
        now=NOW,
    )


def test_exact_authenticated_parity_preserves_policy_authorization():
    parity, intent, runtime = configured()
    result = evaluate(parity, intent, runtime)
    assert result.authorized
    assert result.parity_report is not None and result.parity_report.matched
    assert result.receipt is not None
    assert result.receipt.policy_digest == parity.authority.definition.policy_digest


def test_deployed_allow_cannot_override_reference_denial():
    parity, intent, runtime = configured()
    intent.amount = Money(10_001, "USD")
    intent.approved_cart_digest = intent.canonical_digest()
    result = evaluate(parity, intent, runtime)
    assert result.verdict.decision is PaymentDecision.DENY
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_DIVERGENCE]
    assert result.canonical is None and result.receipt is None


def test_matching_deployed_denial_preserves_exact_reference_denial():
    evaluator = Evaluator(
        decision="deny", reasons=("AMOUNT_EXCEEDS_GRANT",), consequence="routine"
    )
    parity, intent, runtime = configured(evaluator=evaluator)
    intent.amount = Money(10_001, "USD")
    intent.approved_cart_digest = intent.canonical_digest()
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.AMOUNT_EXCEEDS_GRANT]
    assert result.parity_report is not None and result.parity_report.matched
    assert result.canonical is None and result.receipt is None


def test_reason_code_omission_is_policy_divergence():
    evaluator = Evaluator(decision="deny", reasons=(), consequence="routine")
    parity, intent, runtime = configured(evaluator=evaluator)
    intent.amount = Money(10_001, "USD")
    intent.approved_cart_digest = intent.canonical_digest()
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_DIVERGENCE]


@pytest.mark.parametrize("field,value", [
    ("evaluator_id", "attacker-evaluator"),
    ("policy_bundle_digest", "sha256:weaker-policy"),
    ("input_digest", "sha256:other-input"),
    ("policy_id", "policy-lookalike"),
    ("evaluated_at", (NOW - timedelta(seconds=31)).isoformat()),
    ("evaluated_at", (NOW + timedelta(seconds=1)).isoformat()),
])
def test_untrusted_or_stale_deployed_evidence_has_no_authority(field, value):
    evaluator = Evaluator()
    evaluator.mutate = {field: value}
    parity, intent, runtime = configured(evaluator=evaluator)
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_EVIDENCE_INVALID]
    assert not result.authorized


def test_forged_proof_has_no_authority():
    class RejectingAuthenticator(EvaluationAuthenticator):
        def verify(self, evaluation):
            return False

    parity, intent, runtime = configured(authenticator=RejectingAuthenticator())
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_EVIDENCE_INVALID]


def test_evaluator_outage_fails_closed_without_policy_receipt():
    parity, intent, runtime = configured(evaluator=UnavailableEvaluator())
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_AUTHORITY_UNAVAILABLE]
    assert result.canonical is None and result.receipt is None


def test_input_provider_failure_fails_closed_without_policy_receipt():
    class BrokenProvider(InputProvider):
        def build(self, *args, **kwargs):
            raise RuntimeError("authority store unavailable")

    parity, intent, runtime = configured()
    parity.input_provider = BrokenProvider()
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_AUTHORITY_UNAVAILABLE]
    assert result.canonical is None and result.receipt is None


def test_unknown_evaluator_response_type_is_invalid_evidence():
    class MalformedEvaluator(Evaluator):
        def evaluate(self, document):
            return {"decision": "allow"}

    parity, intent, runtime = configured(evaluator=MalformedEvaluator())
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_EVIDENCE_INVALID]


def test_proof_verifier_exception_fails_closed():
    class BrokenAuthenticator(EvaluationAuthenticator):
        def verify(self, evaluation):
            raise RuntimeError("trust root unavailable")

    parity, intent, runtime = configured(authenticator=BrokenAuthenticator())
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_EVIDENCE_INVALID]


def test_duplicate_deployed_reason_codes_are_invalid_evidence():
    evaluator = Evaluator(decision="deny", reasons=("HEAR_REQUIRED", "HEAR_REQUIRED"))
    parity, intent, runtime = configured(evaluator=evaluator)
    result = evaluate(parity, intent, runtime)
    assert result.verdict.reason_codes == [PaymentReasonCode.POLICY_EVIDENCE_INVALID]


def test_policy_definition_must_pin_exact_deployed_bundle():
    parity, _, _ = configured()
    changed_authority = DeterministicPolicyAuthority(
        firewall=parity.authority.firewall,
        definition=replace(
            parity.authority.definition,
            configuration_digest="sha256:other-bundle",
        ),
        receipt_issuer=parity.authority.receipt_issuer,
    )
    with pytest.raises(ValueError, match="bundle digest"):
        ParityEnforcedPolicyAuthority(
            authority=changed_authority,
            input_provider=parity.input_provider,
            evaluator=parity.evaluator,
            authenticator=parity.authenticator,
            profile=parity.profile,
        )
