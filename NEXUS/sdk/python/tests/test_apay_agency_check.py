"""
tests/test_apay_agency_check.py
Agency Check receipt as attributed payment evidence (nexus-apay-acr/0.1).

Three layers:
  1. the verifier against receipts signed by Agency Check's own makeNor
     (tests/fixtures/agency_check, cross-checked with scripts/verify-receipt.mjs);
  2. hostile and malformed input, against receipts signed here with throwaway keys;
  3. backward compatibility end to end: build_opa_input -> OPA, with and without
     the receipt, must give the same payment decision. Skipped if no OPA binary.

Nothing here calls Agency Check, a network, or a payment rail.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("cryptography")
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat  # noqa: E402

from nexus_sdk.payments.agency_check import (  # noqa: E402
    ACR_PROFILE,
    MAX_RECEIPT_BYTES,
    binding_digest,
    verify_agency_check_receipt,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "agency_check"
OPA_DIR = Path(__file__).resolve().parents[3] / "opa"
FIXTURE_TX = hashlib.sha256(b"nexus-apay-acr fixture transaction").hexdigest()
NOW = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)


def _load(name: str):
    return json.loads((FIXTURES / name).read_text())


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class Issuer:
    """A stand-in for Agency Check's makeNor with a throwaway key."""

    def __init__(self) -> None:
        self.key = Ed25519PrivateKey.generate()
        raw = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.jwks = {"keys": [{"kty": "OKP", "crv": "Ed25519", "x": _b64url(raw),
                               "kid": "test-key", "alg": "EdDSA", "use": "sig"}]}

    def receipt(self, tx_digest: str, *, issued_at: datetime = NOW, outcome: str = "allow",
                deny_reason: str | None = None, bind: bool = True) -> dict:
        body = {
            "receipt_id": "11111111-2222-4333-8444-555555555555",
            "agent_did": "did:web:agency-check.example:clients:test",
            "action_type": "tool_call",
            "tool_name": "agency_check",
            "tool_arguments_hash": "0" * 64,
            "outcome": outcome,
            "delegation_depth": 0,
            "timestamp_utc": issued_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ocsf_class_uid": 6002 if outcome == "deny" else 6003,
            "ocsf_severity_id": 4 if outcome == "deny" else 1,
        }
        if deny_reason:
            body["deny_reason"] = deny_reason
        if bind:
            body["cael_envelope_hash"] = binding_digest(tx_digest)
        return self.sign(body)

    def sign(self, body: dict) -> dict:
        body = {k: v for k, v in body.items() if k not in ("receipt_hash", "signature")}
        receipt_hash = hashlib.sha256(_canonical(body)).hexdigest()
        signature = self.key.sign(receipt_hash.encode("ascii"))
        return {**body, "receipt_hash": receipt_hash, "signature": _b64url(signature)}


TX = hashlib.sha256(b"payment request under test").hexdigest()


@pytest.fixture(scope="module")
def issuer() -> Issuer:
    return Issuer()


def _verify(receipt, issuer, tx=TX, **kw):
    return verify_agency_check_receipt(receipt, trusted_keys=issuer.jwks, transaction_digest=tx, **kw)


# --- 1. receipts signed by Agency Check's own signer --------------------------------

def test_fixture_allow_receipt_verifies_against_pinned_jwks():
    ev = verify_agency_check_receipt(
        _load("receipt-allow.json"), trusted_keys=_load("jwks.json"), transaction_digest=FIXTURE_TX)
    assert ev["profile"] == ACR_PROFILE
    assert ev["schema_valid"] and ev["hash_verified"] and ev["signature_verified"]
    assert ev["binding_verified"] and ev["transaction_digest"] == FIXTURE_TX
    assert ev["nor_outcome"] == "allow" and ev["tool_name"] == "agency_check"
    assert ev["issuer_key_id"] == "48c49af9838ed92d"
    assert ev["findings"] == []
    assert ev["card_state"] is None and ev["card_state_source"] == "absent"


def test_fixture_service_paused_receipt_verifies_and_carries_signed_deny_reason():
    ev = verify_agency_check_receipt(
        _load("receipt-service-paused.json"), trusted_keys=_load("jwks.json"), transaction_digest=FIXTURE_TX)
    assert ev["signature_verified"] and ev["binding_verified"]
    assert ev["nor_outcome"] == "deny" and ev["nor_deny_reason"] == "kill_switch"


def test_fixture_receipt_is_not_bound_to_any_other_transaction():
    ev = verify_agency_check_receipt(
        _load("receipt-allow.json"), trusted_keys=_load("jwks.json"), transaction_digest=TX)
    assert ev["signature_verified"] and not ev["binding_verified"]
    assert "ACR_BINDING_MISMATCH" in ev["findings"]
    assert ev["transaction_digest"] is None


def test_get_receipt_result_shape_is_accepted_and_meta_is_declared_not_attested():
    rec = _load("receipt-allow.json")
    result = {"receipt": rec, "meta": {"receipt_id": rec["receipt_id"], "card_state": "clarify",
                                       "ruleset_version": "1.7.0"}}
    ev = verify_agency_check_receipt(result, trusted_keys=_load("jwks.json"), transaction_digest=FIXTURE_TX)
    assert ev["card_state"] == "clarify" and ev["card_state_source"] == "unsigned_meta"
    assert ev["ruleset_version"] == "1.7.0"


# --- 2. hostile and malformed input -------------------------------------------------

def test_live_receipt_verifies(issuer):
    ev = _verify(issuer.receipt(TX), issuer)
    assert ev["hash_verified"] and ev["signature_verified"] and ev["binding_verified"]
    assert ev["findings"] == []


def test_tampered_body_fails_hash_and_signature_is_not_credited(issuer):
    rec = issuer.receipt(TX)
    rec["outcome"] = "deny"
    ev = _verify(rec, issuer)
    assert not ev["hash_verified"] and not ev["signature_verified"]
    assert "ACR_HASH_MISMATCH" in ev["findings"]


def test_rehashed_but_unsigned_body_fails_signature(issuer):
    rec = issuer.receipt(TX)
    rec["tool_name"] = "other_tool"
    rec["receipt_hash"] = hashlib.sha256(_canonical(
        {k: v for k, v in rec.items() if k not in ("receipt_hash", "signature")})).hexdigest()
    ev = _verify(rec, issuer)
    assert ev["hash_verified"] and not ev["signature_verified"]
    assert "ACR_SIGNATURE_INVALID" in ev["findings"]


def test_receipt_from_an_unpinned_key_is_rejected(issuer):
    other = Issuer()
    ev = _verify(other.receipt(TX), issuer)
    assert not ev["signature_verified"] and "ACR_SIGNATURE_INVALID" in ev["findings"]


@pytest.mark.parametrize("jwks", [{}, {"keys": []}, None, "keys", {"keys": "x"},
                                  {"keys": [{"kty": "RSA", "n": "AQAB"}]}])
def test_missing_or_unusable_trusted_keys_never_verify(issuer, jwks):
    ev = verify_agency_check_receipt(issuer.receipt(TX), trusted_keys=jwks, transaction_digest=TX)
    assert not ev["signature_verified"]
    assert ev["findings"]


def test_too_many_trusted_keys_is_refused(issuer):
    jwks = {"keys": issuer.jwks["keys"] * 17}
    ev = verify_agency_check_receipt(issuer.receipt(TX), trusted_keys=jwks, transaction_digest=TX)
    assert not ev["signature_verified"] and "ACR_NO_TRUSTED_KEYS" in ev["findings"]


def test_signature_by_second_pinned_key_is_accepted(issuer):
    other = Issuer()
    jwks = {"keys": other.jwks["keys"] + issuer.jwks["keys"]}
    ev = verify_agency_check_receipt(issuer.receipt(TX), trusted_keys=jwks, transaction_digest=TX)
    assert ev["signature_verified"] and ev["issuer_key_id"] == "test-key"


def test_receipt_bound_to_a_different_transaction_is_not_bound(issuer):
    other_tx = hashlib.sha256(b"a different payment").hexdigest()
    ev = _verify(issuer.receipt(other_tx), issuer)
    assert ev["signature_verified"] and not ev["binding_verified"]
    assert "ACR_BINDING_MISMATCH" in ev["findings"] and ev["transaction_digest"] is None


def test_receipt_without_binding_is_authentic_but_unbound(issuer):
    ev = _verify(issuer.receipt(TX, bind=False), issuer)
    assert ev["signature_verified"] and not ev["binding_verified"]
    assert "ACR_BINDING_ABSENT" in ev["findings"]


@pytest.mark.parametrize("digest", ["", "abc", "G" * 64, "A" * 64, None, 7])
def test_invalid_transaction_digest_never_binds(issuer, digest):
    ev = _verify(issuer.receipt(TX), issuer, tx=digest)
    assert not ev["binding_verified"] and "ACR_TRANSACTION_DIGEST_INVALID" in ev["findings"]


def test_binding_is_domain_separated_from_the_bare_digest(issuer):
    # A client that put the raw transaction digest in nexusCaelEnvelopeHash is not bound.
    body = {k: v for k, v in issuer.receipt(TX).items() if k not in ("receipt_hash", "signature")}
    body["cael_envelope_hash"] = TX
    ev = _verify(issuer.sign(body), issuer)
    assert ev["signature_verified"] and not ev["binding_verified"]


def test_unknown_field_is_a_schema_failure(issuer):
    body = dict(issuer.receipt(TX), extra="x")
    ev = _verify(issuer.sign(body), issuer)
    assert not ev["schema_valid"] and "ACR_SCHEMA_UNKNOWN_FIELD" in ev["findings"]


def test_missing_required_field_stops_early_and_credits_nothing(issuer):
    rec = issuer.receipt(TX)
    del rec["outcome"]
    ev = _verify(rec, issuer)
    assert "ACR_SCHEMA_MISSING_FIELD" in ev["findings"]
    assert not (ev["hash_verified"] or ev["signature_verified"] or ev["binding_verified"])


@pytest.mark.parametrize("patch", [
    {"outcome": "maybe"}, {"action_type": "payment"}, {"delegation_depth": 5},
    {"delegation_depth": True}, {"timestamp_utc": "yesterday"}, {"timestamp_utc": "2026-09-21T12:00:00"},
    {"receipt_id": "has space"}, {"agent_did": "not-a-did"}, {"cael_envelope_hash": "xyz"},
])
def test_schema_violations_are_flagged_even_when_correctly_signed(issuer, patch):
    ev = _verify(issuer.sign({**issuer.receipt(TX), **patch}), issuer)
    assert not ev["schema_valid"] and "ACR_SCHEMA_INVALID" in ev["findings"]


def test_oversized_receipt_is_refused_before_any_work(issuer):
    rec = issuer.receipt(TX)
    rec["deny_reason"] = "x" * (MAX_RECEIPT_BYTES + 1)
    ev = _verify(rec, issuer)
    assert ev["findings"] == ["ACR_RECEIPT_TOO_LARGE"] and not ev["hash_verified"]


@pytest.mark.parametrize("junk", [None, 5, "receipt", [], {"receipt": "x"}, {"receipt": None}])
def test_non_object_input_never_raises(issuer, junk):
    ev = _verify(junk, issuer)
    assert not ev["signature_verified"] and ev["findings"]


def test_non_json_values_never_raise(issuer):
    ev = _verify({"receipt_id": object()}, issuer)
    assert not ev["schema_valid"]


def test_meta_for_another_receipt_is_not_attached(issuer):
    ev = _verify(issuer.receipt(TX), issuer, meta={"receipt_id": "someone-else", "card_state": "ready"})
    assert ev["card_state"] is None and ev["card_state_source"] == "absent"
    assert "ACR_META_RECEIPT_MISMATCH" in ev["findings"]


@pytest.mark.parametrize("state", ["approve", "READY", "", 1, ["ready"]])
def test_meta_card_state_outside_the_enum_is_dropped(issuer, state):
    rec = issuer.receipt(TX)
    ev = _verify(rec, issuer, meta={"receipt_id": rec["receipt_id"], "card_state": state})
    assert ev["card_state"] is None and ev["card_state_source"] == "absent"
    assert "ACR_CARD_STATE_UNKNOWN" in ev["findings"]


def test_meta_cannot_upgrade_an_unauthentic_receipt(issuer):
    rec = issuer.receipt(TX)
    rec["outcome"] = "allow"
    rec["timestamp_utc"] = "2026-09-21T12:00:01.000Z"
    ev = _verify(rec, issuer, meta={"receipt_id": rec["receipt_id"], "card_state": "ready"})
    assert not ev["signature_verified"]
    assert ev["card_state_source"] == "unsigned_meta"  # carried as declared, never as attested


def test_evidence_contains_no_free_text_from_the_receipt(issuer):
    rec = issuer.receipt(TX, outcome="deny", deny_reason="kill_switch")
    ev = _verify(rec, issuer, meta={"receipt_id": rec["receipt_id"], "card_state": "pause",
                                    "title": "SECRET PURCHASE", "details": "private"})
    text = json.dumps(ev)
    assert "SECRET" not in text and "private" not in text
    assert set(ev) == {"profile", "receipt_id", "receipt_hash", "issuer_key_id", "schema_valid",
                       "hash_verified", "signature_verified", "binding_verified",
                       "transaction_digest", "issued_at", "nor_outcome", "nor_deny_reason",
                       "tool_name", "card_state", "card_state_source", "ruleset_version", "findings"}


def test_verifier_does_not_mutate_its_input(issuer):
    rec = issuer.receipt(TX)
    snapshot = copy.deepcopy(rec)
    _verify(rec, issuer)
    assert rec == snapshot


# --- 3. end to end through OPA: the receipt is advisory only ------------------------

def _opa() -> str | None:
    configured = os.environ.get("OPA_BIN")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("opa")


def _opa_eval(doc: dict, query: str):
    proc = subprocess.run(
        [_opa(), "eval", "-f", "json", "-d", str(OPA_DIR / "nexus-apay.rego"), "-I", query],
        input=json.dumps(doc), capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)["result"]
    return result[0]["expressions"][0]["value"] if result else None


def _sample_doc() -> dict:
    """A payment request the policy allows, built through the real SDK input builder."""
    from nexus_sdk.payments import (
        AssuranceLevel, AuthorityConstraints, AuthorityGrant, AuthorityGraph, Money, PaymentRail,
        PrincipalBinding, RuntimeMeasurement, SettlementFinality, TransactionIntent)
    from nexus_sdk.payments.opa_input import build_opa_input

    graph = AuthorityGraph()
    grant = graph.register_root(AuthorityGrant(
        principal_id="principal-1",
        constraints=AuthorityConstraints(
            max_transaction=Money.parse("500.00", "USD"), max_aggregate=Money.parse("2000.00", "USD"),
            currencies={"USD"}, allowed_merchants={"merchant-a"}, allowed_categories={"cloud"},
            allowed_geographies={"US"}, allowed_rails={PaymentRail.CARD_NETWORK},
            allowed_facilitators={"facilitator-1"}, allowed_destinations={"acct-a"},
            min_assurance=AssuranceLevel.RUNTIME_BOUND, max_finality=SettlementFinality.REVERSIBLE,
            window_seconds=3600, window_max=Money.parse("800.00", "USD"), max_transactions=50,
            hear_above=Money.parse("400.00", "USD"), not_after="2026-09-22T12:00:00+00:00"),
        agent_did="did:nexus:agent:buyer", capabilities={"payment.execute"}))
    intent = TransactionIntent(
        authority_grant_id=grant.authority_grant_id, amount=Money.parse("100.00", "USD"),
        merchant_id="merchant-a", merchant_verified=True, merchant_baseline_digest="sha256:baseline-a",
        destination="acct-a", category="cloud", geography="US", rail=PaymentRail.CARD_NETWORK,
        finality=SettlementFinality.REVERSIBLE, facilitator="facilitator-1",
        path_assurance=AssuranceLevel.RUNTIME_BOUND, nonce="n-1",
        quote_expires_at="2026-09-21T13:00:00+00:00")
    intent.approved_cart_digest = intent.canonical_digest()
    runtime = RuntimeMeasurement(
        workload_id="spiffe://nexus.local/agent/buyer", attested=True, attestation_method="tdx",
        artifact_digest="sha256:img", measured_at=NOW.isoformat())
    principal = PrincipalBinding(
        principal_id="principal-1", owner_of_record="owner@example.org", agent_did="did:nexus:agent:buyer")
    return build_opa_input(
        graph=graph, grant=grant, intent=intent, principal=principal, runtime=runtime,
        expected_runtime_baseline=runtime.baseline_digest(), merchant_baseline="sha256:baseline-a",
        known_destinations={"acct-a"}, seen_nonces=set(), hear_satisfied_by=None, now=NOW)


needs_opa = pytest.mark.skipif(_opa() is None, reason="OPA binary not available (set OPA_BIN)")


@needs_opa
def test_receipt_evidence_is_advisory_and_never_changes_the_payment_decision(issuer):
    doc = _sample_doc()
    tx = doc["transaction"]["canonical_digest"]
    baseline = {q: _opa_eval(doc, q) for q in ("data.nexus.apay.decision", "data.nexus.apay.release_credential")}

    variants = {
        "ready": (issuer.receipt(tx), {"card_state": "ready"}),
        "pause": (issuer.receipt(tx), {"card_state": "pause"}),
        "clarify": (issuer.receipt(tx), {"card_state": "clarify"}),
        "paused-service": (issuer.receipt(tx, outcome="deny", deny_reason="kill_switch"), None),
        "wrong-tx": (issuer.receipt(hashlib.sha256(b"other").hexdigest()), None),
        "stale": (issuer.receipt(tx, issued_at=NOW - timedelta(hours=3)), None),
    }
    for name, (rec, card) in variants.items():
        meta = {"receipt_id": rec["receipt_id"], **card} if card else None
        evidence = verify_agency_check_receipt(rec, trusted_keys=issuer.jwks, transaction_digest=tx, meta=meta)
        with_receipt = dict(doc, agency_check_evidence=evidence)
        for query, expected in baseline.items():
            assert _opa_eval(with_receipt, query) == expected, f"{name} changed {query}"

    advisory = _opa_eval(dict(doc, agency_check_evidence=verify_agency_check_receipt(
        issuer.receipt(tx), trusted_keys=issuer.jwks, transaction_digest=tx,
        meta={"receipt_id": issuer.receipt(tx)["receipt_id"], "card_state": "ready"})),
        "data.nexus.apay.agency_check_advisory")
    assert advisory["mode"] == "shadow" and advisory["enforced"] is False
    assert advisory["card_state_attested"] is False
    assert advisory["status"] == "ready"


@needs_opa
def test_missing_receipt_is_absent_and_changes_nothing():
    doc = _sample_doc()
    advisory = _opa_eval(doc, "data.nexus.apay.agency_check_advisory")
    assert advisory["status"] == "absent" and advisory["shadow_effect"] == "none"
    assert advisory["findings"] == ["ACR_ABSENT"]
