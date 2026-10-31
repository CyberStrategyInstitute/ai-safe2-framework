"""
NEXUS MCP Adapter - tool-call authorization (agent-to-tool plane).

STATUS: IMPLEMENTED AND TESTED AS A PURE FUNCTION. The adapter as a whole is
still not production-ready; see README.md "Implementation status".

Python mirror of `opa/nexus-authz.rego` (`package nexus.authz`,
`authorize_tool_call`, policy_version nexus-authz-v0.3-v31). Ported back from
Agency Check's working TypeScript edge adapter (`src/nexus/authz.ts` and
`src/nexus/context.ts`), then re-aligned to the CURRENT upstream policy rather
than the older policy that port was written against. The port therefore also
carries the registry-bound ACT tier, the TASK_CONTEXT credential deny, the
ConfigChange approval deny, the AIM-registry deny, and the joined deny_reason.

Four deliberate differences from the Rego, all fail-closed. Each is pinned by a
test in NEXUS/sdk/python/tests/test_mcp_adapter_authz.py so the test flips when
the policy is corrected:

  AUTHZ-DIV-1  A non-integer delegation_depth (null, false, "1") is outside the
               limit. In Rego `null <= 4` and `false <= 4` are true because
               cross-type comparison orders null and booleans below numbers.
  AUTHZ-DIV-2  A config_change with no change_hash cannot match an approval, so
               ACT-2+ agents are denied. In Rego the undefined lookup removes
               the deny rule and the change is allowed.
  AUTHZ-DIV-3  With parent_vcc_capabilities absent, every requested capability
               is a widening. In Rego the undefined `in` removes the widening
               condition and the request passes.
  AUTHZ-DIV-4  A mandate counts only if its record in mandates.active is bound
               to this agent_id, lists this tool in `tools`, and has a numeric
               `expires_at_ns` in the future. In Rego any truthy entry for the
               ID satisfies every mandate-gated tool for every caller.

Inputs are plain dicts with the same field names as the Rego input document,
so the same table can be evaluated by OPA and by this module. `policy_data` is
the `data.nexus` subtree (mandates, revocation, approvals, aim).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional

__all__ = [
    "FRAMEWORK_VERSION",
    "POLICY_VERSION",
    "NexusContext",
    "NexusContextError",
    "authorize_tool_call",
    "parse_nexus_context",
    "persistence_scope",
]

POLICY_VERSION = "nexus-authz-v0.3-v31"
FRAMEWORK_VERSION = "AI SAFE2 v3.1"

MAX_DELEGATION_DEPTH = 4
CONTEXT_COMPARTMENTS = frozenset({"TASK_CONTEXT", "CREDENTIAL_SURFACE", "AGENT_STATE"})

_SCOPE_RANK = {"request": 0, "handle_scoped": 1, "durable": 2, "swarm_shared": 3}
_RANK_SCOPE = {rank: scope for scope, rank in _SCOPE_RANK.items()}
_ZONE_SCOPE = {
    "SESSION": "request", "SESSION_MEMORY": "request", "request": "request",
    "CROSS_SESSION": "handle_scoped", "CROSS_SESSION_MEMORY": "handle_scoped",
    "handle_scoped": "handle_scoped", "cross_session": "handle_scoped",
    "PERMANENT": "durable", "PERMANENT_MEMORY": "durable", "durable": "durable",
    "permanent": "durable",
    "SWARM_SHARED": "swarm_shared", "SWARM_SHARED_MEMORY": "swarm_shared",
    "swarm_shared": "swarm_shared",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _member(item: Any, collection: Any) -> bool:
    """Rego `item in collection` for arrays, sets and objects (object values)."""
    if isinstance(collection, Mapping):
        return item in collection.values()
    if isinstance(collection, (list, tuple, set, frozenset)):
        return item in collection
    return False


def _get(mapping: Any, *path: Any) -> Any:
    node = mapping
    for key in path:
        if not isinstance(node, Mapping) or not isinstance(key, str) or key not in node:
            return None
        node = node[key]
    return node


# ---------------------------------------------------------------------------
# Persistence scope (most restrictive declaration wins; unknown = swarm_shared)
# ---------------------------------------------------------------------------

def persistence_scope(i: Mapping[str, Any]) -> str:
    ranks: set[int] = set()
    declared = i.get("persistence_scope")
    if isinstance(declared, str):
        ranks.add(_SCOPE_RANK.get(declared.lower(), 3))
    if "memory_zone" in i and i["memory_zone"] is not False:
        zone = i["memory_zone"]
        scope = _ZONE_SCOPE.get(zone, "swarm_shared") if isinstance(zone, str) else "swarm_shared"
        ranks.add(_SCOPE_RANK[scope])
    if ranks:
        return _RANK_SCOPE[max(ranks)]
    return "swarm_shared" if i.get("performative") == "memory_write" else "request"


def _effective_act_tier(i: Mapping[str, Any], d: Mapping[str, Any]) -> tuple[Any, Any]:
    registered = _get(d, "aim", "agents", i.get("agent_id"), "act_tier")
    registered = registered if _is_number(registered) else None
    if registered is not None:
        return registered, registered
    declared = i.get("act_tier")
    return (declared if _is_number(declared) else 4), None


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

def authorize_tool_call(i: Mapping[str, Any], policy_data: Mapping[str, Any],
                        *, now_ns: Optional[int] = None) -> dict[str, Any]:
    """Return the same decision document as data.nexus.authz.authorize_tool_call."""
    d = policy_data or {}
    scope = persistence_scope(i)
    requires_memory_mandate = scope in {"durable", "swarm_shared"}
    tool = i.get("tool_name")
    agent = i.get("agent_id")

    mandate_id = i.get("mandate_id")
    active = _get(d, "mandates", "active")
    now = time.time_ns() if now_ns is None else now_ns
    # AUTHZ-DIV-4: the mandate record must be bound to principal, tool and expiry.
    record = active.get(mandate_id) if isinstance(active, Mapping) and isinstance(mandate_id, str) else None
    expires = record.get("expires_at_ns") if isinstance(record, Mapping) else None
    valid_mandate = (
        mandate_id != "" and isinstance(record, Mapping)
        and isinstance(agent, str) and record.get("agent_id") == agent
        and isinstance(tool, str) and _member(tool, record.get("tools"))
        and _is_number(expires) and expires > now
    )

    has_capability = _member(tool, i.get("vcc_capabilities"))
    mandate_required_op = _member(tool, i.get("vcc_mandate_required")) and not valid_mandate
    memory_mandate_missing = (
        i.get("performative") == "memory_write" and requires_memory_mandate and not valid_mandate
    )
    depth = i.get("delegation_depth")
    # AUTHZ-DIV-1: only an integer depth can be within the limit.
    within_depth = isinstance(depth, int) and not isinstance(depth, bool) and depth <= MAX_DELEGATION_DEPTH
    status = _get(d, "revocation", "agents", agent, "status")
    revoked = status in {"revoked", "hard_brake"}
    valid_compartment = i.get("context_compartment") in CONTEXT_COMPARTMENTS
    parent = i.get("parent_vcc_capabilities")
    requested = i.get("requested_new_capabilities")
    widening = isinstance(requested, (list, tuple)) and any(
        not _member(cap, parent) for cap in requested)

    tier, registered = _effective_act_tier(i, d)

    deny_reasons: set[str] = set()
    if i.get("context_compartment") == "TASK_CONTEXT" and isinstance(tool, str) and tool.startswith("credential:"):
        deny_reasons.add("TASK_CONTEXT cannot access credential: tools")
    if memory_mandate_missing:
        deny_reasons.add(f"{scope} memory writes require a Memory Mandate")
    if i.get("performative") == "config_change" and _is_number(tier) and tier >= 2:
        change_hash = i.get("change_hash")
        # AUTHZ-DIV-2: an absent change hash cannot match an approval.
        approved = isinstance(change_hash, str) and _get(
            d, "approvals", "config_change", agent, change_hash) not in (None, False)
        if not approved:
            deny_reasons.add("ConfigChange requires out-of-band approval for ACT-2+ agents")
    if _get(d, "aim", "required") is True and _get(d, "aim", "agents", agent) is None:
        deny_reasons.add("agent has no registered AIM (registry required)")
    declared = i.get("act_tier")
    if registered is not None and _is_number(declared) and declared > registered:
        deny_reasons.add(
            f"declared ACT-{_rego_num(declared)} exceeds registered ACT tier {_rego_num(registered)}")

    allow = (has_capability and not mandate_required_op and within_depth and not revoked
             and valid_compartment and not widening and not memory_mandate_missing
             and not deny_reasons)

    unmet: set[str] = set()
    if not has_capability:
        unmet.add("tool not in VCC capabilities")
    if mandate_required_op:
        unmet.add("tool requires an active mandate")
    if not within_depth:
        unmet.add("delegation depth missing or above 4")
    if revoked:
        unmet.add("agent revoked or under hard brake")
    if not valid_compartment:
        unmet.add("unrecognized context compartment")
    if widening:
        unmet.add("requested capabilities exceed parent VCC")

    reasons = deny_reasons | unmet
    return {
        "allow": allow,
        "mandate_required": mandate_required_op or memory_mandate_missing,
        "deny_reason": "; ".join(sorted(reasons)) if not allow and reasons else "",
        "policy_version": POLICY_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "decision_timestamp": now,
        "agent_id": agent,
        "tool_name": tool,
        "delegation_depth": depth,
        "persistence_scope": scope,
        "effective_act_tier": tier,
    }


def _rego_num(value: Any) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


# ---------------------------------------------------------------------------
# NEXUS context carried on an MCP call (params._meta)
# ---------------------------------------------------------------------------
# Port of Agency Check src/nexus/context.ts. Everything here is caller-asserted.
# It may narrow what is allowed (depth, compartment, requested capabilities); it
# never widens it, and it is never identity. Identity comes from the verified
# credential resolved by establish_trust, not from _meta. `_meta` is an MCP
# construct, so no control is bound to it (CP.5 protocol-independence rule):
# a call with no NEXUS fields is evaluated with the most common defaults and
# the verified principal.

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TRACE = re.compile(r"^[0-9a-f]{32}$|^[0-9a-f-]{36}$")
_KEY = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_DID = re.compile(r"^did:[a-z0-9]+:[A-Za-z0-9.:%_-]{1,200}$")
_TOOL = re.compile(r"^[a-z_][a-z0-9_:.-]{0,63}$")

_FIELDS = frozenset({
    "nexusTraceId", "nexusDelegationDepth", "nexusContextCompartment", "nexusMandateId",
    "nexusIdempotencyKey", "nexusSenderDID", "nexusCaelEnvelopeHash", "nexusReasoningHash",
    "nexusRequestedCapabilities",
})


class NexusContextError(ValueError):
    def __init__(self, field_name: str) -> None:
        super().__init__(f"nexus context field {field_name} is malformed")
        self.field = field_name


@dataclass(frozen=True)
class NexusContext:
    delegation_depth: int = 0
    context_compartment: str = "TASK_CONTEXT"
    requested_capabilities: tuple[str, ...] = ()
    trace_id: Optional[str] = None
    mandate_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    # Caller-asserted; validated and then not trusted as identity.
    sender_did: Optional[str] = None
    cael_envelope_hash: Optional[str] = None
    reasoning_hash: Optional[str] = None


def _full(rx: re.Pattern[str], value: str) -> bool:
    # JavaScript RegExp.test with ^...$ anchors; Python's $ also matches before
    # a trailing newline, so require a full match explicitly.
    return rx.fullmatch(value) is not None


def parse_nexus_context(meta: Any) -> NexusContext:
    if meta is None:
        return NexusContext()
    if not isinstance(meta, Mapping):
        raise NexusContextError("_meta")
    for key in meta:
        # Other _meta keys (progress tokens, client hints) are ignored; a key that
        # looks like NEXUS but is not in the contract is rejected so typos cannot pass.
        if isinstance(key, str) and key.startswith("nexus") and key not in _FIELDS:
            raise NexusContextError(key)

    def text(key: str, rx: re.Pattern[str]) -> Optional[str]:
        if key not in meta:
            return None
        value = meta[key]
        if not isinstance(value, str) or not _full(rx, value):
            raise NexusContextError(key)
        return value

    compartment = "TASK_CONTEXT"
    if "nexusContextCompartment" in meta:
        value = meta["nexusContextCompartment"]
        if not isinstance(value, str) or len(value) > 32:
            raise NexusContextError("nexusContextCompartment")
        compartment = value  # unknown values reach authz and are denied there

    depth = 0
    if "nexusDelegationDepth" in meta:
        value = meta["nexusDelegationDepth"]
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 64:
            raise NexusContextError("nexusDelegationDepth")
        depth = value  # > 4 is denied by authz, with a reason

    caps: tuple[str, ...] = ()
    if "nexusRequestedCapabilities" in meta:
        value = meta["nexusRequestedCapabilities"]
        if (not isinstance(value, list) or len(value) > 16
                or not all(isinstance(c, str) and _full(_TOOL, c) for c in value)):
            raise NexusContextError("nexusRequestedCapabilities")
        caps = tuple(value)

    return NexusContext(
        delegation_depth=depth,
        context_compartment=compartment,
        requested_capabilities=caps,
        trace_id=text("nexusTraceId", _TRACE),
        mandate_id=text("nexusMandateId", _KEY),
        idempotency_key=text("nexusIdempotencyKey", _KEY),
        sender_did=text("nexusSenderDID", _DID),
        cael_envelope_hash=text("nexusCaelEnvelopeHash", _HEX64),
        reasoning_hash=text("nexusReasoningHash", _HEX64),
    )
