"""
tests/test_apay_opa_contract.py
Keeps opa/nexus-apay.rego and the Python enforcement point from drifting.

OPA itself is not run here - the policy engine is a deployment dependency, not a
test dependency. What IS verified, statically, is the thing that actually breaks
in production: the Rego referencing an input field that nothing ever supplies.
A rule whose input path is absent is undefined, an undefined violation rule
contributes nothing, and a control silently stops existing.

So this suite parses the policy, extracts every `input.*` path it reads, and
asserts each one is present in the document build_opa_input() emits. Adding a
rule to the policy without wiring its input fails here instead of failing open.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from nexus_sdk.payments import (
    AssuranceLevel,
    AuthorityConstraints,
    AuthorityGrant,
    AuthorityGraph,
    Money,
    PaymentRail,
    PrincipalBinding,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
)
from nexus_sdk.payments.opa_input import OPA_INPUT_FIELDS, build_opa_input

UTC = timezone.utc
NOW = datetime(2026, 9, 21, 12, 0, 0, tzinfo=UTC)

POLICY = Path(__file__).resolve().parents[3] / "opa" / "nexus-apay.rego"

# Paths reached through a local alias (`tx := input.transaction`,
# `cons := input.grant.constraints`) rather than written as input.* literally.
_ALIASES = {"tx": "input.transaction", "cons": "input.grant.constraints"}


@pytest.fixture(scope="module")
def policy_text() -> str:
    if not POLICY.exists():
        pytest.skip(f"policy not found at {POLICY}")
    return POLICY.read_text()


@pytest.fixture
def sample_input():
    graph = AuthorityGraph()
    grant = graph.register_root(AuthorityGrant(
        principal_id="principal-1",
        constraints=AuthorityConstraints(
            max_transaction=Money.parse("500.00", "USD"),
            max_aggregate=Money.parse("2000.00", "USD"),
            currencies={"USD"},
            allowed_merchants={"merchant-a"},
            allowed_categories={"cloud"},
            allowed_geographies={"US"},
            allowed_rails={PaymentRail.CARD_NETWORK},
            allowed_facilitators={"facilitator-1"},
            allowed_destinations={"acct-a"},
            min_assurance=AssuranceLevel.RUNTIME_BOUND,
            max_finality=SettlementFinality.REVERSIBLE,
            window_seconds=3600,
            window_max=Money.parse("800.00", "USD"),
            max_transactions=50,
            hear_above=Money.parse("400.00", "USD"),
            not_after="2026-09-22T12:00:00+00:00",
        ),
        agent_did="did:nexus:agent:buyer",
        capabilities={"payment.execute"},
    ))
    intent = TransactionIntent(
        authority_grant_id=grant.authority_grant_id,
        amount=Money.parse("100.00", "USD"),
        merchant_id="merchant-a",
        merchant_verified=True,
        merchant_baseline_digest="sha256:baseline-a",
        destination="acct-a",
        category="cloud",
        geography="US",
        rail=PaymentRail.CARD_NETWORK,
        finality=SettlementFinality.REVERSIBLE,
        facilitator="facilitator-1",
        path_assurance=AssuranceLevel.RUNTIME_BOUND,
        nonce="n-1",
        quote_expires_at="2026-09-21T13:00:00+00:00",
    )
    intent.approved_cart_digest = intent.canonical_digest()
    runtime = RuntimeMeasurement(
        workload_id="spiffe://nexus.local/agent/buyer",
        attested=True, attestation_method="tdx",
        artifact_digest="sha256:img", measured_at=NOW.isoformat())
    principal = PrincipalBinding(
        principal_id="principal-1", owner_of_record="vincent@example.org",
        agent_did="did:nexus:agent:buyer")
    return build_opa_input(
        graph=graph, grant=grant, intent=intent, principal=principal,
        runtime=runtime, expected_runtime_baseline=runtime.baseline_digest(),
        merchant_baseline="sha256:baseline-a", known_destinations={"acct-a"},
        seen_nonces=set(), hear_satisfied_by=None, now=NOW)


def _referenced_paths(text: str) -> set[str]:
    """Every input path the policy reads, with aliases expanded."""
    paths: set[str] = set()
    for match in re.finditer(r"\binput\.([A-Za-z_][A-Za-z0-9_.]*)", text):
        paths.add("input." + match.group(1))
    for alias, target in _ALIASES.items():
        for match in re.finditer(rf"\b{alias}\.([A-Za-z_][A-Za-z0-9_.]*)", text):
            paths.add(f"{target}.{match.group(1)}")
    return paths


def _resolve(doc, path: str) -> bool:
    """True if the dotted path exists in the document (null counts as present)."""
    parts = path.split(".")[1:]  # drop leading "input"
    node = doc
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
        if node is None:
            return True   # present and explicitly null: the rule can still evaluate
    return True


class TestOPAContract:

    def test_every_top_level_key_is_emitted(self, sample_input):
        for key in OPA_INPUT_FIELDS:
            assert key in sample_input, f"builder omits declared key: {key}"

    def test_policy_reads_nothing_the_builder_does_not_supply(self, policy_text, sample_input):
        missing = sorted(p for p in _referenced_paths(policy_text)
                         if not _resolve(sample_input, p))
        assert not missing, (
            "policy references input paths the builder never supplies; "
            f"these rules would be silently undefined: {missing}"
        )

    def test_builder_emits_nulls_rather_than_omitting(self):
        graph = AuthorityGraph()
        intent = TransactionIntent(
            authority_grant_id="missing", amount=Money(100, "USD"),
            merchant_id="m", nonce="n")
        doc = build_opa_input(graph=graph, grant=None, intent=intent, now=NOW)
        # A missing grant must still produce an evaluable document so the
        # policy can deny, rather than an absent key that skips rules.
        assert "grant" in doc and doc["grant"] is None
        assert "runtime" in doc and doc["runtime"] is None
        assert doc["revocation"]["available"] is True

    def test_unreachable_revocation_is_reported_not_defaulted(self):
        graph = AuthorityGraph()
        grant = graph.register_root(AuthorityGrant(
            principal_id="p", constraints=AuthorityConstraints()))
        graph.revocation.available = False
        intent = TransactionIntent(
            authority_grant_id=grant.authority_grant_id,
            amount=Money(100, "USD"), merchant_id="m", nonce="n")
        doc = build_opa_input(graph=graph, grant=grant, intent=intent, now=NOW)
        assert doc["revocation"]["available"] is False

    def test_policy_has_no_unconditional_allow(self, policy_text):
        """There must be no rule body that grants allow without evaluating reasons."""
        assert "default allow := false" in policy_text
        assert "default decision" in policy_text
        allow_bodies = re.findall(r"^allow\s*\{(.*?)^\}", policy_text,
                                  re.DOTALL | re.MULTILINE)
        assert allow_bodies, "policy defines no allow rule"
        for body in allow_bodies:
            assert "reason_codes" in body, f"allow rule bypasses reason evaluation: {body!r}"

    def test_credential_release_gate_rechecks_revocation(self, policy_text):
        gate = re.search(r"release_credential\s*\{(.*?)^\}", policy_text,
                         re.DOTALL | re.MULTILINE)
        assert gate, "policy defines no credential release gate"
        body = gate.group(1)
        assert "revocation.current_epoch" in body
        assert "available" in body
        assert "runtime_measurement_id" in body

    def test_declared_fields_match_builder_output_exactly(self, sample_input):
        assert set(sample_input) == set(OPA_INPUT_FIELDS)
