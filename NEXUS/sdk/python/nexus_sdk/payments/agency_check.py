"""
nexus_sdk/payments/agency_check.py
Agency Check receipt as attributed payment evidence (profile nexus-apay-acr/0.1).

Spec: NEXUS/payments/AGENCY-CHECK-RECEIPT-EVIDENCE.md

WHAT THIS DOES
    Verifies one Agency Check NOR v0.3 receipt offline against PINNED keys and
    turns it into the `agency_check_evidence` document that opa/nexus-apay.rego
    reads. The policy cannot verify Ed25519 itself, so verification happens here,
    outside the policy, the same way runtime attestation is verified before the
    policy sees `runtime.attested`.

WHAT IT DOES NOT DO
    - It never fetches keys. A JWKS URL inside a receipt or a get_receipt result
      is a hint, not a trust anchor; the deployment pins the keys.
    - It never receives or stores what was checked. The agency_check arguments
      stay with the client; only ids, enums, hashes and timestamps leave here.
    - It does not make the receipt an authorization. A receipt says a check ran.
      The card is a recommendation for a person. Under this profile the evidence
      can only add friction to a payment, never remove a denial or satisfy HEAR.

SIGNED VS DECLARED
    Agency Check signs the NOR fields only. `card_state` (ready, clarify, pause)
    and `ruleset_version` are returned beside the receipt and are NOT covered by
    the signature. They are carried as `card_state_source: "unsigned_meta"`, and
    the policy treats them as declared, never attested.

BINDING
    The client sets MCP `params._meta.nexusCaelEnvelopeHash` on the agency_check
    call to binding_digest(transaction.canonical_digest()). Agency Check signs
    that value into the receipt as `cael_envelope_hash`. This verifier recomputes
    it for the transaction being authorized. No other binding is accepted.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from typing import Any, Mapping, Optional

from nexus_sdk.payments.objects import canonical_hash, parse_ts

__all__ = [
    "ACR_PROFILE",
    "CARD_STATES",
    "binding_digest",
    "verify_agency_check_receipt",
]

ACR_PROFILE = "nexus-apay-acr/0.1"
CARD_STATES = ("ready", "clarify", "pause")

MAX_RECEIPT_BYTES = 8192
MAX_TRUSTED_KEYS = 16

# NOR v0.3 (schemas/nor-v0.3.schema.json, additionalProperties: false).
_NOR_FIELDS = frozenset({
    "receipt_id", "agent_did", "action_type", "tool_name", "tool_arguments_hash", "outcome",
    "guardian_policy_id", "deny_reason", "delegation_depth", "cael_envelope_hash",
    "reasoning_chain_hash", "timestamp_utc", "receipt_hash", "signature",
    "ocsf_class_uid", "ocsf_severity_id",
})
_NOR_REQUIRED = ("receipt_id", "agent_did", "action_type", "tool_name", "outcome",
                 "timestamp_utc", "receipt_hash", "signature")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_DID = re.compile(r"did:[a-z]+:.+")
_B64URL = re.compile(r"[A-Za-z0-9_-]+")
_SHORT = re.compile(r"[A-Za-z0-9._:/-]{1,128}")


def binding_digest(transaction_digest: str) -> str:
    """The value a client puts in nexusCaelEnvelopeHash for one transaction."""
    if not isinstance(transaction_digest, str) or not _HEX64.fullmatch(transaction_digest):
        raise ValueError("transaction digest must be 64 lowercase hex characters")
    return canonical_hash({"profile": ACR_PROFILE, "transaction_digest": transaction_digest})


def _nor_canonical(value: Any) -> bytes:
    # Agency Check: JSON.stringify over recursively key-sorted objects, UTF-8.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _ed25519_verify(x: str, signature: bytes, message: bytes) -> Optional[bool]:
    """True/False, or None when no Ed25519 implementation is installed."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return None
    try:
        key = Ed25519PublicKey.from_public_bytes(_b64url_decode(x))
        key.verify(signature, message)
        return True
    except (InvalidSignature, ValueError, binascii.Error):
        return False


def _schema_findings(nor: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    if set(nor) - _NOR_FIELDS:
        findings.append("ACR_SCHEMA_UNKNOWN_FIELD")
    if any(k not in nor for k in _NOR_REQUIRED):
        findings.append("ACR_SCHEMA_MISSING_FIELD")
        return findings
    checks = (
        isinstance(nor["receipt_id"], str) and _SHORT.fullmatch(nor["receipt_id"]),
        isinstance(nor["agent_did"], str) and _DID.fullmatch(nor["agent_did"]) and len(nor["agent_did"]) <= 256,
        nor["action_type"] == "tool_call",
        isinstance(nor["tool_name"], str) and _SHORT.fullmatch(nor["tool_name"]),
        nor["outcome"] in ("allow", "deny"),
        isinstance(nor["receipt_hash"], str) and _HEX64.fullmatch(nor["receipt_hash"]),
        isinstance(nor["signature"], str) and _B64URL.fullmatch(nor["signature"]) and len(nor["signature"]) <= 128,
        all(isinstance(nor.get(k), str) and _HEX64.fullmatch(nor[k])
            for k in ("tool_arguments_hash", "cael_envelope_hash", "reasoning_chain_hash") if k in nor),
        all(isinstance(nor.get(k), str) and _SHORT.fullmatch(nor[k])
            for k in ("guardian_policy_id", "deny_reason") if k in nor),
        "delegation_depth" not in nor or (
            isinstance(nor["delegation_depth"], int) and not isinstance(nor["delegation_depth"], bool)
            and 0 <= nor["delegation_depth"] <= 4),
    )
    if not all(checks):
        findings.append("ACR_SCHEMA_INVALID")
    try:
        ts = parse_ts(nor["timestamp_utc"]) if isinstance(nor["timestamp_utc"], str) else None
        if ts is None or ts.tzinfo is None:
            findings.append("ACR_SCHEMA_INVALID")
    except ValueError:
        findings.append("ACR_SCHEMA_INVALID")
    return sorted(set(findings))


def _empty(findings: list[str]) -> dict[str, Any]:
    return {
        "profile": ACR_PROFILE,
        "receipt_id": None,
        "receipt_hash": None,
        "issuer_key_id": None,
        "schema_valid": False,
        "hash_verified": False,
        "signature_verified": False,
        "binding_verified": False,
        "transaction_digest": None,
        "issued_at": None,
        "nor_outcome": None,
        "nor_deny_reason": None,
        "tool_name": None,
        "card_state": None,
        "card_state_source": "absent",
        "ruleset_version": None,
        "findings": sorted(set(findings)),
    }


def verify_agency_check_receipt(
    receipt: Any,
    *,
    trusted_keys: Mapping[str, Any],
    transaction_digest: str,
    meta: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Verify one receipt and return the policy's `agency_check_evidence` document.

    `receipt` is the NOR object (or a get_receipt result with a `receipt` key).
    `trusted_keys` is a pinned JWKS ({"keys": [...]}) for the Agency Check
    deployment. `meta` is the unsigned get_receipt `meta`, if the client has it.
    Never raises on hostile input: every failure becomes a finding and a False.
    Freshness is judged by the policy against its own `now`, not here.
    """
    if isinstance(receipt, Mapping) and isinstance(receipt.get("receipt"), Mapping):
        if meta is None and isinstance(receipt.get("meta"), Mapping):
            meta = receipt["meta"]
        receipt = receipt["receipt"]
    if not isinstance(receipt, Mapping):
        return _empty(["ACR_SCHEMA_INVALID"])
    try:
        size = len(_nor_canonical(receipt))
    except (TypeError, ValueError):
        return _empty(["ACR_SCHEMA_INVALID"])
    if size > MAX_RECEIPT_BYTES:
        return _empty(["ACR_RECEIPT_TOO_LARGE"])

    nor = dict(receipt)
    findings = _schema_findings(nor)
    out = _empty(findings)
    out["schema_valid"] = not findings
    if "ACR_SCHEMA_MISSING_FIELD" in findings:
        return out

    out.update({
        "receipt_id": nor["receipt_id"] if isinstance(nor["receipt_id"], str) else None,
        "receipt_hash": nor["receipt_hash"] if isinstance(nor["receipt_hash"], str) else None,
        "issued_at": nor["timestamp_utc"] if isinstance(nor["timestamp_utc"], str) else None,
        "nor_outcome": nor["outcome"] if nor["outcome"] in ("allow", "deny") else None,
        "nor_deny_reason": nor.get("deny_reason") if isinstance(nor.get("deny_reason"), str) else None,
        "tool_name": nor["tool_name"] if isinstance(nor["tool_name"], str) else None,
    })

    body = {k: v for k, v in nor.items() if k not in ("receipt_hash", "signature")}
    out["hash_verified"] = hashlib.sha256(_nor_canonical(body)).hexdigest() == nor["receipt_hash"]
    if not out["hash_verified"]:
        findings.append("ACR_HASH_MISMATCH")

    keys = trusted_keys.get("keys") if isinstance(trusted_keys, Mapping) else None
    if not isinstance(keys, list) or not keys or len(keys) > MAX_TRUSTED_KEYS:
        findings.append("ACR_NO_TRUSTED_KEYS")
    elif out["hash_verified"] and out["schema_valid"]:
        try:
            signature = _b64url_decode(nor["signature"])
        except (binascii.Error, ValueError):
            signature = b""
        unavailable = False
        for key in keys:
            if not (isinstance(key, Mapping) and key.get("kty") == "OKP"
                    and key.get("crv") == "Ed25519" and isinstance(key.get("x"), str)):
                continue
            result = _ed25519_verify(key["x"], signature, nor["receipt_hash"].encode("ascii"))
            if result is None:
                unavailable = True
                break
            if result:
                out["signature_verified"] = True
                kid = key.get("kid")
                out["issuer_key_id"] = kid if isinstance(kid, str) and _SHORT.fullmatch(kid) else None
                break
        if unavailable:
            findings.append("ACR_VERIFIER_UNAVAILABLE")
        elif not out["signature_verified"]:
            findings.append("ACR_SIGNATURE_INVALID")

    try:
        expected = binding_digest(transaction_digest)
    except ValueError:
        expected = None
        findings.append("ACR_TRANSACTION_DIGEST_INVALID")
    if expected is not None and nor.get("cael_envelope_hash") == expected:
        out["binding_verified"] = True
        out["transaction_digest"] = transaction_digest
    elif "cael_envelope_hash" not in nor:
        findings.append("ACR_BINDING_ABSENT")
    elif expected is not None:
        findings.append("ACR_BINDING_MISMATCH")

    # Declared, unsigned. Only kept when it names this receipt and is a known enum.
    if isinstance(meta, Mapping) and meta.get("receipt_id") == out["receipt_id"]:
        state = meta.get("card_state")
        if state in CARD_STATES:
            out["card_state"] = state
            out["card_state_source"] = "unsigned_meta"
        elif state is not None:
            findings.append("ACR_CARD_STATE_UNKNOWN")
        version = meta.get("ruleset_version")
        if isinstance(version, str) and _SHORT.fullmatch(version):
            out["ruleset_version"] = version
    elif isinstance(meta, Mapping):
        findings.append("ACR_META_RECEIPT_MISMATCH")

    out["findings"] = sorted(set(findings))
    return out
