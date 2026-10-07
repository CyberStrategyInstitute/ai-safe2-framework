"""
NEXUS Agent Identity Manifest (AIM) v0.3 registry.

The ACT capability tier is an identity property (IETF draft-nexus-l1-l2,
section 3.1.1): the owner of record sets it when the agent's AIM is registered.
Enforcement points resolve the tier from the registered AIM. A tier carried in
a request is only a claim; it may not exceed the registered tier and cannot
lower it.

Raising a tier means registering a new AIM version. Every version is retained
in order, so tier changes are reconstructable.

Trust model: the registry is the trust anchor. Production deployments must
verify the AIM's ML-DSA-65 signature (FIPS 204) before ``register``. Pass a
``signature_verifier`` to enforce that here; without one, records carry
``signature_verified=False``.

Stdlib only, consistent with the SDK's minimal core dependencies.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

# Required fields of schemas/aim-v0.3.schema.json (kept in sync by tests).
AIM_V03_REQUIRED = (
    "agentDID", "spiffeID", "agentClass", "maturityLevel", "actTier", "ownerChain",
    "purposeDeclaration", "jurisdictionProfile", "pqcPublicKeys", "signature",
)


class AIMValidationError(ValueError):
    """An AIM document cannot be registered."""


def aim_digest(doc: dict) -> str:
    """SHA-256 over the canonical JSON of the AIM, excluding its signature."""
    body = {k: v for k, v in doc.items() if k != "signature"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class AIMRecord:
    agent_did: str
    act_tier: int
    owner_of_record: str
    aim_digest: str
    version: int
    max_delegation_depth: Optional[int]
    signature_verified: bool
    registered_at: str


class AIMRegistry:
    """In-process AIM registry: current record per DID plus full version history."""

    def __init__(self, signature_verifier: Optional[Callable[[dict], bool]] = None):
        self._verifier = signature_verifier
        self._history: dict[str, list[AIMRecord]] = {}

    @staticmethod
    def validate(doc: dict) -> None:
        if not isinstance(doc, dict):
            raise AIMValidationError("AIM must be a JSON object")
        missing = [f for f in AIM_V03_REQUIRED if f not in doc or doc[f] in (None, "")]
        if missing:
            raise AIMValidationError(f"AIM missing required fields: {missing}")
        if not str(doc["agentDID"]).startswith("did:"):
            raise AIMValidationError("agentDID must be a DID")
        tier = doc["actTier"]
        if isinstance(tier, bool) or not isinstance(tier, int) or not 1 <= tier <= 4:
            raise AIMValidationError(f"actTier must be an integer 1-4, got {tier!r}")
        depth = doc.get("maxDelegationDepth")
        if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= 16):
            raise AIMValidationError(f"maxDelegationDepth must be an integer 0-16, got {depth!r}")

    def register(self, doc: dict) -> AIMRecord:
        """Validate and register an AIM version. Raises AIMValidationError."""
        self.validate(doc)
        verified = False
        if self._verifier is not None:
            if not self._verifier(doc):
                raise AIMValidationError("AIM signature verification failed")
            verified = True
        did = doc["agentDID"]
        versions = self._history.setdefault(did, [])
        record = AIMRecord(
            agent_did=did,
            act_tier=doc["actTier"],
            owner_of_record=doc["ownerChain"],
            aim_digest=aim_digest(doc),
            version=len(versions) + 1,
            max_delegation_depth=doc.get("maxDelegationDepth"),
            signature_verified=verified,
            registered_at=datetime.now(timezone.utc).isoformat(),
        )
        versions.append(record)
        return record

    def resolve(self, agent_did: str) -> Optional[AIMRecord]:
        versions = self._history.get(agent_did)
        return versions[-1] if versions else None

    def history(self, agent_did: str) -> list[AIMRecord]:
        return list(self._history.get(agent_did, []))

    def to_opa_data(self) -> dict:
        """Document for OPA ``data.nexus.aim`` (read by nexus-authz and AISM invariants)."""
        return {"required": True, "agents": {
            did: {"act_tier": v[-1].act_tier, "aim_digest": v[-1].aim_digest}
            for did, v in self._history.items() if v
        }}
