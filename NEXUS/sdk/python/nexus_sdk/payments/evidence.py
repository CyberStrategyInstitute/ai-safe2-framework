"""
nexus_sdk/payments/evidence.py
Payment Transaction Receipt (PTR) and the append-only evidence ledger.

Implements APAY-17 (privacy-preserving evidence) and APAY-19 (dispute-grade
evidence). PTR is the payment-plane sibling of the existing NEXUS Output
Receipt (NOR) and carries the same hash-chaining discipline.

WHAT "DISPUTE-GRADE" MEANS
    A third party who trusts none of the participants must be able to
    reconstruct, from the receipt alone: who was accountable, what authority
    existed, what the principal actually approved, what workload executed, which
    ruleset decided, what moved, and whether revocation had already fired. If
    reconstructing the decision requires believing the agent's own explanation of
    its reasoning, the evidence is worthless in exactly the cases it exists for.

    The Darwinium survey finding that there is no industry consensus on who pays
    when an agent transaction goes wrong is a statement about evidence, not about
    law. Liability follows whoever cannot prove their side.

PRIVACY
    A receipt that leaks the principal's identity, budget ceiling or purchase
    history to every verifier trades one risk for another. Receipts therefore
    separate three disclosure tiers: public (what a merchant or facilitator
    sees), adjudication (what a dispute reviewer sees), and sealed (what only
    the principal's own organization can open). `redacted()` is the default
    external form, and it commits to sealed fields by digest so their omission
    is detectable rather than silent.
"""

from __future__ import annotations

import threading
import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from nexus_sdk.payments.objects import canonical_hash, utcnow

__all__ = [
    "DisclosureTier",
    "PaymentTransactionReceipt",
    "EvidenceLedger",
    "DurableEvidenceLedger",
    "REQUIRED_EVIDENCE_FIELDS",
]


class DisclosureTier:
    PUBLIC = "public"
    ADJUDICATION = "adjudication"
    SEALED = "sealed"


# The evidence contract. `completeness()` scores against this list, which is the
# metric a conformance claim is measured on - not a vendor's assertion that its
# logging is "comprehensive".
REQUIRED_EVIDENCE_FIELDS: tuple[str, ...] = (
    "framework_version",
    "profile_version",
    "principal_id",
    "owner_of_record",
    "agent_did",
    "act_tier",
    "consequence_class",
    "instruction_ref",
    "instruction_digest",
    "normalized_constraints_digest",
    "approval_surface_digest",
    "approved_cart_digest",
    "canonical_digest",
    "authority_grant_id",
    "delegation_chain_id",
    "delegation_lineage",
    "attenuation_result",
    "runtime_measurement_id",
    "runtime_baseline_digest",
    "runtime_attested",
    "policy_id",
    "decision_id",
    "decision",
    "reason_codes",
    "merchant_id",
    "merchant_baseline_digest",
    "destination",
    "rail",
    "facilitator",
    "path_assurance",
    "amount",
    "aggregate_exposure_after",
    "revocation_epoch",
    "idempotency_key",
    "nonce",
    "risk_signals",
    "hear_satisfied_by",
    "decided_at",
    "settlement_id",
    "settlement_state",
    "settled_at",
)

_SEALED_FIELDS = frozenset({
    "instruction_ref",
    "instruction_digest",
    "normalized_constraints_digest",
    "aggregate_exposure_after",
    "owner_of_record",
})

_PUBLIC_FIELDS = frozenset({
    "profile_version",
    "canonical_digest",
    "decision",
    "merchant_id",
    "amount",
    "rail",
    "path_assurance",
    "idempotency_key",
    "decided_at",
    "settlement_id",
    "settlement_state",
})


@dataclass
class PaymentTransactionReceipt:
    """One append-only, hash-chained record of a payment decision and its outcome."""
    fields: dict[str, Any]
    receipt_id: str = field(default_factory=lambda: f"ptr_{uuid.uuid4().hex[:24]}")
    prev_hash: Optional[str] = None
    created_at: str = field(default_factory=lambda: utcnow().isoformat())
    profile_version: str = "CP.5.APAY/0.4"

    def __post_init__(self) -> None:
        self.fields.setdefault("profile_version", self.profile_version)

    def content_hash(self) -> str:
        return canonical_hash({
            "receipt_id": self.receipt_id,
            "prev_hash": self.prev_hash,
            "created_at": self.created_at,
            "fields": self.fields,
        })

    def completeness(self) -> float:
        """Fraction of required evidence fields actually present and non-null.

        Reported rather than asserted. A deployment claiming CP.5.APAY
        conformance publishes this number; a low score is a finding, not a
        formatting problem.
        """
        present = sum(1 for key in REQUIRED_EVIDENCE_FIELDS if self._present(key))
        return present / len(REQUIRED_EVIDENCE_FIELDS)

    def _present(self, key: str) -> bool:
        """An empty list is an answer, not a gap.

        A clean allow carries no reason codes and no risk signals. Scoring []
        as missing would penalize exactly the transactions where nothing went
        wrong, which makes the completeness metric measure the wrong thing.
        """
        return self.fields.get(key) not in (None, "")

    def missing_fields(self) -> list[str]:
        return [k for k in REQUIRED_EVIDENCE_FIELDS if not self._present(k)]

    def redacted(self, tier: str = DisclosureTier.ADJUDICATION,
                 *, commitment_key: Optional[bytes] = None) -> dict:
        """APAY-17. Disclose only what the tier needs; commit to the rest.

        Sealed fields are replaced by a digest, not dropped. A verifier can
        therefore tell that a field existed and was withheld, and the principal
        can later open it to prove what it said - which is the property that
        makes selective disclosure evidence rather than omission.
        """
        if tier == DisclosureTier.SEALED:
            out = dict(self.fields)
        elif tier == DisclosureTier.PUBLIC:
            out = {k: v for k, v in self.fields.items() if k in _PUBLIC_FIELDS}
        else:
            out = {k: v for k, v in self.fields.items() if k not in _SEALED_FIELDS}

        if tier != DisclosureTier.SEALED:
            withheld = {k: v for k, v in self.fields.items() if k not in out}
            if withheld:
                encoded = json.dumps(withheld, sort_keys=True, separators=(",", ":"), default=str).encode()
                out["_sealed_commitment"] = (
                    hmac.new(commitment_key, encoded, hashlib.sha256).hexdigest()
                    if commitment_key else canonical_hash(withheld)
                )
                out["_commitment_type"] = "HMAC-SHA256" if commitment_key else "SHA-256-UNKEYED"
                out["_sealed_fields"] = sorted(withheld)
        out["_receipt_id"] = self.receipt_id
        out["_content_hash"] = self.content_hash()
        return out

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "prev_hash": self.prev_hash,
            "created_at": self.created_at,
            "content_hash": self.content_hash(),
            "completeness": round(self.completeness(), 4),
            "fields": self.fields,
        }


class EvidenceLedger:
    """Append-only, hash-chained PTR store.

    In-memory by design: the reference implementation shows the chaining
    contract without pretending to be durable storage. Production bindings write
    the same records to a WORM store, an append-only log service, or the
    existing NEXUS OTel/OCSF evidence path, and `verify_chain()` is what a
    conformance check runs against whatever backend is used.
    """

    def __init__(self) -> None:
        self._receipts: list[PaymentTransactionReceipt] = []
        self._by_intent: dict[str, list[str]] = {}
        self._lock = threading.RLock()

    def append(self, fields: dict[str, Any]) -> PaymentTransactionReceipt:
        with self._lock:
            prev = self._receipts[-1].content_hash() if self._receipts else None
            receipt = PaymentTransactionReceipt(fields=fields, prev_hash=prev)
            self._receipts.append(receipt)
            intent_id = fields.get("transaction_intent_id")
            if intent_id:
                self._by_intent.setdefault(intent_id, []).append(receipt.receipt_id)
            return receipt

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Detect any insertion, deletion or edit in the receipt chain."""
        with self._lock:
            problems: list[str] = []
            expected_prev: Optional[str] = None
            for receipt in self._receipts:
                if receipt.prev_hash != expected_prev:
                    problems.append(
                        f"{receipt.receipt_id}: prev_hash {receipt.prev_hash} != {expected_prev}"
                    )
                expected_prev = receipt.content_hash()
            return (not problems), problems

    def for_intent(self, transaction_intent_id: str) -> list[PaymentTransactionReceipt]:
        with self._lock:
            ids = set(self._by_intent.get(transaction_intent_id, []))
            return [r for r in self._receipts if r.receipt_id in ids]

    def completeness_for_intent(self, transaction_intent_id: str) -> tuple[float, list[str]]:
        """Union coverage across every receipt for one transaction.

        Completeness is a property of the transaction's evidence, not of any
        single receipt. The authorization receipt cannot carry a settlement id
        because settlement has not happened yet; scoring receipts individually
        would mark correct behavior as incomplete. What an adjudicator needs is
        that the *set* of receipts answers every required question.
        """
        receipts = self.for_intent(transaction_intent_id)
        if not receipts:
            return 0.0, list(REQUIRED_EVIDENCE_FIELDS)
        missing = [
            key for key in REQUIRED_EVIDENCE_FIELDS
            if not any(r._present(key) for r in receipts)
        ]
        covered = len(REQUIRED_EVIDENCE_FIELDS) - len(missing)
        return covered / len(REQUIRED_EVIDENCE_FIELDS), missing

    def bundle(self, transaction_intent_id: str,
               tier: str = DisclosureTier.ADJUDICATION) -> dict:
        """The dispute package for one transaction, at one disclosure tier."""
        receipts = self.for_intent(transaction_intent_id)
        chain_ok, problems = self.verify_chain()
        coverage, missing = self.completeness_for_intent(transaction_intent_id)
        return {
            "transaction_intent_id": transaction_intent_id,
            "profile_version": "CP.5.APAY/0.4",
            "disclosure_tier": tier,
            "chain_intact": chain_ok,
            "chain_problems": problems,
            "receipts": [r.redacted(tier) for r in receipts],
            "completeness": round(coverage, 4),
            "missing_evidence_fields": missing,
            "generated_at": utcnow().isoformat(),
        }

    def __len__(self) -> int:
        with self._lock:
            return len(self._receipts)

    def __iter__(self) -> Iterable[PaymentTransactionReceipt]:
        with self._lock:
            return iter(list(self._receipts))


class DurableEvidenceLedger(EvidenceLedger):
    """Evidence Vault (`DurableEvidenceLedger`).

    Appends HMAC-authenticated JSONL records and fsyncs each receipt. Storage
    confidentiality is intentionally delegated to an encrypted volume/KMS
    envelope; this class refuses operation without an integrity key.
    """
    human_name = "Evidence Vault"
    technical_name = "DurableEvidenceLedger"

    def __init__(self, path: str, *, integrity_key: bytes,
                 commitment_key: Optional[bytes] = None) -> None:
        if len(integrity_key) < 32:
            raise ValueError("Evidence Vault integrity_key must be at least 32 bytes")
        super().__init__()
        self.path = path
        self.integrity_key = integrity_key
        self.commitment_key = commitment_key or integrity_key
        self._load_existing()

    def _load_existing(self) -> None:
        """Restore and authenticate existing records before accepting writes."""
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                envelope = json.loads(line)
                record = envelope.get("record")
                mac = envelope.get("mac")
                encoded = json.dumps(
                    record, sort_keys=True, separators=(",", ":"), default=str
                ).encode()
                expected = hmac.new(self.integrity_key, encoded, hashlib.sha256).hexdigest()
                if not isinstance(mac, str) or not hmac.compare_digest(expected, mac):
                    raise ValueError(f"Evidence Vault integrity failure at line {line_number}")
                receipt = PaymentTransactionReceipt(
                    fields=record["fields"],
                    receipt_id=record["receipt_id"],
                    prev_hash=record["prev_hash"],
                    created_at=record["created_at"],
                )
                if receipt.content_hash() != record.get("content_hash"):
                    raise ValueError(f"Evidence Vault content hash failure at line {line_number}")
                self._receipts.append(receipt)
        intact, problems = self.verify_chain()
        if not intact:
            raise ValueError("Evidence Vault chain failure: " + "; ".join(problems))

    def append(self, fields: dict[str, Any]) -> PaymentTransactionReceipt:
        receipt = super().append(fields)
        record = receipt.to_dict()
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()
        envelope = {
            "record": record,
            "mac": hmac.new(self.integrity_key, encoded, hashlib.sha256).hexdigest(),
            "mac_algorithm": "HMAC-SHA256",
        }
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return receipt

    def redacted_receipt(self, receipt: PaymentTransactionReceipt,
                         tier: str = DisclosureTier.ADJUDICATION) -> dict:
        return receipt.redacted(tier, commitment_key=self.commitment_key)

    def bundle(self, transaction_intent_id: str,
               tier: str = DisclosureTier.ADJUDICATION) -> dict:
        bundle = super().bundle(transaction_intent_id, tier)
        bundle["receipts"] = [self.redacted_receipt(r, tier)
                              for r in self.for_intent(transaction_intent_id)]
        bundle["integrity"] = "HMAC-SHA256 + hash chain"
        bundle["confidentiality"] = "requires encrypted volume or KMS envelope"
        return bundle
