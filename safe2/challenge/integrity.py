"""Artifact change detection and optional caller-trusted Ed25519 signatures.

Neither an unkeyed hash nor a valid artifact signature proves the observations.
The private/public key formats are unencrypted PKCS8 PEM / SubjectPublicKeyInfo PEM.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from safe2.challenge.io import read_bytes


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _body(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in {"integrity_sha256", "signature"}}


def seal(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(_body(value))
    result["integrity_sha256"] = digest(result)
    return result


def verify_digest(value: dict[str, Any]) -> bool:
    return isinstance(value.get("integrity_sha256"), str) and (
        value["integrity_sha256"] == digest(_body(value))
    )


def _crypto():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )
    except ImportError as exc:
        raise ValueError("Signing requires the optional extra: pip install 'ai-safe2[challenge]'") from exc
    return serialization, Ed25519PrivateKey, Ed25519PublicKey


def _message(value: dict[str, Any], signature: dict[str, Any]) -> bytes:
    return canonical_bytes({
        "domain": "safe2.challenge-artifact-signature.v1",
        "integrity_sha256": value["integrity_sha256"],
        "algorithm": "Ed25519",
        "signer_id": signature["signer_id"],
        "public_key_sha256": signature["public_key_sha256"],
    })


def sign_run(run: dict[str, Any], key_path: str | Path, signer_id: str) -> dict[str, Any]:
    from safe2.challenge.model import validate_run

    validate_run(run)
    if not verify_digest(run):
        raise ValueError("Cannot sign a modified artifact")
    if not isinstance(signer_id, str) or not re.fullmatch(r"[A-Za-z0-9._:@/-]{1,120}", signer_id):
        raise ValueError("Signer ID must be 1-120 safe identifier characters")
    serialization, private_type, _ = _crypto()
    try:
        private = serialization.load_pem_private_key(read_bytes(key_path, limit=16_384), password=None)
    except (TypeError, ValueError) as exc:
        raise ValueError("Expected an unencrypted Ed25519 PKCS8 PEM private key") from exc
    if not isinstance(private, private_type):
        raise TypeError("Expected an Ed25519 private key")
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    result = copy.deepcopy(run)
    signature = {"algorithm": "Ed25519", "signer_id": signer_id,
                 "public_key_sha256": hashlib.sha256(public).hexdigest()}
    signature["signature_base64"] = base64.b64encode(private.sign(_message(result, signature))).decode("ascii")
    result["signature"] = signature
    return result


def verify_signature(value: dict[str, Any], public_key: str | Path | None = None) -> str:
    signature = value.get("signature")
    if signature is None:
        return "not_present"
    if public_key is None:
        return "unverified_no_trusted_key"
    serialization, _, public_type = _crypto()
    try:
        public = serialization.load_pem_public_key(read_bytes(public_key, limit=16_384))
        if not isinstance(public, public_type):
            return "invalid"
        raw_public = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        if signature["public_key_sha256"] != hashlib.sha256(raw_public).hexdigest():
            return "invalid"
        decoded = base64.b64decode(signature["signature_base64"], validate=True)
        public.verify(decoded, _message(value, signature))
    except (ValueError, TypeError, KeyError):
        return "invalid"
    except Exception as exc:
        # Do not conceal I/O/runtime failures; only the library's signature rejection.
        from cryptography.exceptions import InvalidSignature
        if isinstance(exc, InvalidSignature):
            return "invalid"
        raise
    return "valid_trusted_key"
