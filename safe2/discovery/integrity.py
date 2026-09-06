"""Deterministic integrity metadata for discovery evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_bytes(inventory: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in inventory.items() if key != "integrity"}
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def inventory_digest(inventory: dict[str, Any]) -> str:
    """Hash the complete inventory except its self-referential integrity block."""
    return hashlib.sha256(_canonical_bytes(inventory)).hexdigest()


def seal_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Attach tamper-evident metadata without claiming signer authenticity."""
    inventory["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "json-sort-keys-compact-utf8-v1",
        "digest": inventory_digest(inventory),
        "verification_scope": "all top-level content except integrity",
        "authenticity": "unsigned",
    }
    return inventory


def verify_inventory(inventory: dict[str, Any]) -> str:
    """Return valid, invalid, or not_present for compatible legacy evidence."""
    integrity = inventory.get("integrity")
    if not isinstance(integrity, dict):
        return "not_present"
    if integrity.get("algorithm") != "sha256":
        return "invalid"
    digest = integrity.get("digest")
    if not isinstance(digest, str) or len(digest) != 64:
        return "invalid"
    return "valid" if digest == inventory_digest(inventory) else "invalid"
