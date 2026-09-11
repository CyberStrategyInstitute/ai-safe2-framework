"""Detached, domain-separated signatures checked against an operator-supplied key.

Authentication binds bytes to a key, not truth to an observation. No key is
discovered from the report, network, environment, or signature itself.
"""

from __future__ import annotations

import base64
import hashlib
import time
from pathlib import Path
from typing import Any

from safe2.challenge.integrity import _crypto, canonical_bytes
from safe2.challenge.io import parse_json, read_bytes
from safe2.contracts import validate_artifact

MAX_TTL = 86400


def _message(attestation: dict[str, Any]) -> bytes:
    body = {key: value for key, value in attestation.items() if key != "signature_base64"}
    return b"safe2.report-attestation.v1\x00" + canonical_bytes(body)


def sign_report(payload: bytes, key_path: Path, signer_id: str, ttl: int = 3600) -> dict[str, Any]:
    """Sign a bounded structured report; signing does not approve its contents."""
    if len(payload) > 1_000_000 or isinstance(ttl, bool) or not 1 <= ttl <= MAX_TTL:
        raise ValueError("Report exceeds 1 MB or TTL is outside 1..86400 seconds")
    report = parse_json(payload)
    schema_version = report.get("schema_version")
    if not isinstance(schema_version, str):
        raise TypeError("Report needs a string schema version")
    contract = {"safe2.test-result.v1": "test-result-v1",
                "safe2.tool-result.v1": "tool-result-v1"}.get(schema_version)
    if contract is None or validate_artifact(contract, report):
        raise ValueError("Only structurally valid test/tool reports can be signed")
    serialization, private_type, _ = _crypto()
    private = serialization.load_pem_private_key(read_bytes(key_path, limit=16384), password=None)
    if not isinstance(private, private_type):
        raise TypeError("Expected an unencrypted Ed25519 private key")
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    issued = int(time.time())
    result = {
        "schema_version": "safe2.report-attestation.v1", "algorithm": "Ed25519",
        "report_sha256": hashlib.sha256(payload).hexdigest(), "signer_id": signer_id,
        "public_key_sha256": hashlib.sha256(public).hexdigest(),
        "issued_at": issued, "expires_at": issued + ttl,
        "signature_base64": "A" * 86 + "==",
    }
    if validate_artifact("report-attestation-v1", result):
        raise ValueError("Invalid signer identifier or attestation metadata")
    result["signature_base64"] = base64.b64encode(private.sign(_message(result))).decode("ascii")
    return result


def verify_report(payload: bytes, attestation: dict[str, Any], trusted_key: Path) -> str:
    """Return a bounded status; malformed input never becomes authenticated."""
    if len(payload) > 1_000_000 or validate_artifact("report-attestation-v1", attestation):
        return "invalid_attestation"
    if hashlib.sha256(payload).hexdigest() != attestation["report_sha256"]:
        return "report_digest_mismatch"
    issued, expires = attestation["issued_at"], attestation["expires_at"]
    if not 1 <= expires - issued <= MAX_TTL:
        return "invalid_validity_window"
    serialization, _, public_type = _crypto()
    from cryptography.exceptions import InvalidSignature

    try:
        public = serialization.load_pem_public_key(read_bytes(trusted_key, limit=16384))
        if not isinstance(public, public_type):
            return "invalid_trusted_key"
        raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        if hashlib.sha256(raw).hexdigest() != attestation["public_key_sha256"]:
            return "untrusted_key"
        signature = base64.b64decode(attestation["signature_base64"], validate=True)
        public.verify(signature, _message(attestation))
    except (ValueError, TypeError, InvalidSignature):
        return "invalid_signature_or_key"
    now = int(time.time())
    if now < issued:
        return "not_yet_valid"
    if now >= expires:
        return "expired"
    return "authenticated_trusted_key"
