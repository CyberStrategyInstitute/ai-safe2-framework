"""
nexus_sdk/guardian.py
NEXUS Guardian Integration Profile v0.3

Implements the ACS (Agent Control Standard) Guardian verdict model with NEXUS
identity binding. Adds per-call argument-level interception to NEXUS's existing
capability-scope enforcement (OPA/Rego) - catching "legitimate credential,
illegitimate use" attacks that scope enforcement alone cannot detect.

Architecture position:
    NEXUS OPA/Rego = capability-scope enforcement (category level)
    NEXUS Guardian  = per-call argument inspection with reasoning context
    Together        = complete L3 enforcement stack

AOS Wire Protocol: JSON-RPC 2.0 over HTTPS
Verdicts: allow | deny | modify (returned BEFORE tool execution)

Key divergence from ACS v0.1.0:
    ACS StepContext.agent = { id: string }         (unauthenticated)
    NEXUS StepContext.agent = NEXUSAgentContext     (DID + SPIFFE + AIM digest)

The NEXUS identity extension makes Guardian verdicts trustworthy - the policy
engine evaluates against a cryptographically verified workload identity, not
a string that any process can set.

PRODUCTION: Deploy Guardian as an mTLS-protected sidecar or remote service.
            Use NEXUSGuardianClient for remote invocation.
TESTING:    GuardianPolicy.evaluate() runs inline with no network required.
            Stub mode validates the full verdict contract.

Reference: ACS v0.1.0, AOS v0.1.0 (aos.owasp.org), NEXUS-A2A v0.3
AI SAFE2 v3.1: S1.5, A2.5, F3.1, M4.4, CP.4, CP.5
"""

from __future__ import annotations
import hashlib
import ipaddress
import json
import re
import unicodedata
import uuid
from urllib.parse import unquote
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover
    from nexus_sdk.aim import AIMRegistry


# ── Verdict Types ─────────────────────────────────────────────────────────────

class GuardianVerdict(str, Enum):
    """AOS v0.1.0 verdict types returned before action execution."""
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"


class StepMethod(str, Enum):
    """
    AOS v0.1.0 step interception methods. Coverage = complete cognitive loop.
    NEXUS extensions: protocols/mcp wraps all MCP traffic; nexus/delegate wraps
    CAEL DELEGATE performatives for delegation chain validation.
    """
    # Core cognitive loop (AOS-compatible)
    AGENT_TRIGGER            = "steps/agentTrigger"
    KNOWLEDGE_RETRIEVAL      = "steps/knowledgeRetrieval"
    MEMORY_STORE             = "steps/memoryStore"
    MEMORY_CONTEXT_RETRIEVAL = "steps/memoryContextRetrieval"
    MESSAGE                  = "steps/message"
    TOOL_CALL_REQUEST        = "steps/toolCallRequest"
    TOOL_CALL_RESULT         = "steps/toolCallResult"
    # Protocol wrappers
    MCP_PROTOCOL             = "protocols/mcp"
    # NEXUS extensions (not in AOS v0.1.0)
    NEXUS_DELEGATE           = "nexus/delegate"       # Delegation chain validation
    NEXUS_SWARM_JOIN         = "nexus/swarmJoin"      # Swarm quorum check
    NEXUS_CONFIG_CHANGE      = "nexus/configChange"   # ACT-2+ approval gate


# ── NEXUS Agent Context (replaces bare string in ACS) ─────────────────────────

@dataclass
class NEXUSAgentContext:
    """
    Cryptographically verified agent identity for GuardianStepContext.
    Replaces ACS v0.1.0's { id: string } with full NEXUS identity binding.

    The aimDigest field allows Guardian policies to verify that the agent
    presenting this context matches the registered AIM - preventing identity
    spoofing at the Guardian layer even if transport identity is compromised.
    """
    agent_did: str                        # W3C DID (anchors to AIM)
    spiffe_id: str                        # SPIFFE workload identity
    aim_digest: Optional[str] = None      # SHA-256 of registered AIM document
    maturity_level: Optional[str] = None  # intern|member|associate|senior|principal
    agent_class: Optional[str] = None     # personal|orchestrator|swarm-member|ot-device
    act_tier: Optional[int] = None        # ACT capability tier (1-4)
    # ACS backward compatibility: expose id as the DID
    @property
    def id(self) -> str:
        return self.agent_did

    @property
    def name(self) -> str:
        return self.agent_did.split(":")[-1]

    def to_dict(self) -> dict:
        return {
            "id": self.agent_did,         # ACS compatibility field
            "agent_did": self.agent_did,
            "spiffe_id": self.spiffe_id,
            "aim_digest": self.aim_digest,
            "maturity_level": self.maturity_level,
            "agent_class": self.agent_class,
            "act_tier": self.act_tier,
        }


# ── Memory Provenance Extension (NEXUS-specific, P1 improvement) ──────────────

@dataclass
class NEXUSMemoryProvenance:
    """
    Provenance metadata passed to Guardian on memory hooks.
    Enables Guardian policies to enforce temporal and drift constraints inline:
      deny if drift_score > 0.25 (tighter than Vaccine's 0.30 default)
      deny if checkpoint_age_hours > 48 (stale provenance)
      deny if source_did not in trusted_principals

    This is the data ACS's Guardian cannot compute without NEXUS Memory Vaccine.
    Including it in StepContext makes memory Guardian policies semantically rich.
    """
    source_did: str                        # DID of agent performing the write
    zone: str                              # SESSION|CROSS_SESSION|PERMANENT|SWARM_SHARED
    embedding_hash: Optional[str] = None  # SHA-256 of content embedding
    drift_score: Optional[float] = None   # Cosine distance from purpose baseline
    session_id: Optional[str] = None      # Source session identifier
    checkpoint_timestamp: Optional[str] = None  # Last validated checkpoint time
    mandate_id: Optional[str] = None      # Required for PERMANENT zone writes

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# ── Guardian Step Context ──────────────────────────────────────────────────────

@dataclass
class GuardianStepContext:
    """
    Complete context passed to Guardian for each step interception.
    AOS v0.1.0 compatible + NEXUS identity and provenance extensions.

    Key additions over ACS v0.1.0 StepContext:
      - agent: NEXUSAgentContext (cryptographic identity vs bare string)
      - nexus_provenance: memory provenance metadata for memory hooks
      - delegation_context: delegation graph info for scope validation
      - reasoning: agent's LLM reasoning chain (for non-repudiation)
      - cael_envelope_hash: integrity reference to the originating CAEL message
    """
    method: StepMethod
    agent: NEXUSAgentContext
    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:16]}")
    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Action being intercepted (tool call, memory op, message, etc.)
    action_method: Optional[str] = None
    action_arguments: Optional[dict] = None

    # Memory hook context (populated for MEMORY_STORE, MEMORY_CONTEXT_RETRIEVAL)
    memory_content: Optional[list[str]] = None
    nexus_provenance: Optional[NEXUSMemoryProvenance] = None

    # Delegation context (for scope validation in delegated requests)
    delegation_depth: int = 0
    vcc_id: Optional[str] = None
    vcc_capabilities: Optional[list[str]] = None
    parent_vcc_capabilities: Optional[list[str]] = None

    # Agent reasoning chain (for Reasoning Chain Non-Repudiation, P2)
    reasoning: Optional[str] = None
    reasoning_hash: Optional[str] = None  # SHA-256 of reasoning text

    # NEXUS trace linkage
    cael_envelope_hash: Optional[str] = None
    trace_id: Optional[str] = None

    def compute_reasoning_hash(self) -> Optional[str]:
        """Compute and attach SHA-256 hash of reasoning chain for NOR inclusion."""
        if self.reasoning:
            self.reasoning_hash = hashlib.sha256(self.reasoning.encode()).hexdigest()
        return self.reasoning_hash

    def to_jsonrpc_params(self) -> dict:
        """
        Serialize to AOS v0.1.0-compatible JSON-RPC params.
        NEXUS extensions are namespaced under 'nexus' to avoid collisions.
        ACS Guardians that don't understand NEXUS extensions see valid AOS params.
        """
        params: dict[str, Any] = {
            "stepId": self.step_id,
            "sessionId": self.session_id,
            "timestamp": self.timestamp,
            "agent": self.agent.to_dict(),
        }

        if self.action_method:
            params["action"] = {
                "method": self.action_method,
                "arguments": self.action_arguments or {},
            }
        if self.memory_content is not None:
            params["memory"] = self.memory_content
        if self.reasoning:
            params["reasoning"] = self.reasoning

        # NEXUS extension block (ignored by ACS-only Guardians)
        nexus_ext: dict[str, Any] = {}
        if self.nexus_provenance:
            nexus_ext["memoryProvenance"] = self.nexus_provenance.to_dict()
        if self.delegation_depth:
            nexus_ext["delegationDepth"] = self.delegation_depth
        if self.vcc_id:
            nexus_ext["vccId"] = self.vcc_id
        if self.vcc_capabilities is not None:
            nexus_ext["vccCapabilities"] = self.vcc_capabilities
        if self.parent_vcc_capabilities is not None:
            nexus_ext["parentVccCapabilities"] = self.parent_vcc_capabilities
        if self.reasoning_hash:
            nexus_ext["reasoningHash"] = self.reasoning_hash
        if self.cael_envelope_hash:
            nexus_ext["caelEnvelopeHash"] = self.cael_envelope_hash
        if self.trace_id:
            nexus_ext["traceId"] = self.trace_id

        if nexus_ext:
            params["nexus"] = nexus_ext

        return params


# ── Guardian Verdict ──────────────────────────────────────────────────────────

@dataclass
class GuardianVerdictResult:
    """
    Guardian verdict: allow, deny, or modify - returned BEFORE action execution.
    AOS v0.1.0 compatible response structure.
    """
    decision: GuardianVerdict
    step_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Reasoning and audit (optional in AOS; required in NEXUS-Full)
    reasoning: Optional[str] = None
    reason_codes: list[str] = field(default_factory=list)

    # Modification payload (only populated when decision = MODIFY)
    modified_request: Optional[dict] = None

    # NEXUS-specific audit fields
    policy_version: str = "nexus-guardian-v0.3"
    nor_fingerprint: Optional[str] = None  # Hash for NOR chain inclusion

    @property
    def allowed(self) -> bool:
        return self.decision == GuardianVerdict.ALLOW

    @property
    def denied(self) -> bool:
        return self.decision == GuardianVerdict.DENY

    def compute_nor_fingerprint(self, step_context: GuardianStepContext) -> str:
        """
        Compute NOR fingerprint for Reasoning Chain Non-Repudiation (P2).
        Hashes: decision + step_id + agent_did + action + reasoning_hash
        Included in the NEXUS Output Receipt for the parent tool call.
        """
        fingerprint_input = json.dumps({
            "decision": self.decision.value,
            "step_id": self.step_id,
            "agent_did": step_context.agent.agent_did,
            "action_method": step_context.action_method,
            "reasoning_hash": step_context.reasoning_hash,
            "timestamp": self.timestamp,
        }, sort_keys=True)
        self.nor_fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()
        return self.nor_fingerprint

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "decision": self.decision.value,
            "stepId": self.step_id,
            "timestamp": self.timestamp,
            "policyVersion": self.policy_version,
        }
        if self.reasoning:
            d["reasoning"] = self.reasoning
        if self.reason_codes:
            d["reasonCode"] = self.reason_codes
        if self.modified_request:
            d["modifiedRequest"] = self.modified_request
        if self.nor_fingerprint:
            d["norFingerprint"] = self.nor_fingerprint
        return d


# ── Built-in Guardian Policies ─────────────────────────────────────────────────


# ── Argument normalization and built-in detectors ─────────────────────────────
#
# v0.3 substring-matched a short list against the raw JSON of the arguments, so
# encoding (%2e%2e%2f), Windows separators, doubled slashes, numeric IP spellings
# (2852039166, 0xa9fea9fe) and secrets carried as values all passed. Every string
# leaf and key is now normalized before matching, and the detectors below run in
# addition to any caller-supplied pattern list.

_CREDENTIAL_PATHS = (
    "/.ssh/", ".ssh/", "/.aws/credentials", "/.aws/config", ".aws/credentials",
    "/.kube/config", ".kube/config", "/.config/gcloud", ".config/gcloud",
    "/.netrc", ".git-credentials", "/.docker/config.json", "/.gnupg/",
    "/etc/shadow", "/etc/sudoers", "/etc/gshadow",
)
_TRAVERSAL = re.compile(r"(^|/)\.\.(/|$)")
_SECRET_MATERIAL = (
    re.compile(r"-----begin [a-z0-9 ]*private key-----"),
    re.compile(r"\b(akia|asia)[0-9a-z]{16}\b"),
    re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[a-z0-9]{36}\b|\bgithub_pat_[a-z0-9_]{40,}"),
    re.compile(r"\bsk-(live|proj|ant|test)-[a-z0-9_-]{20,}"),
    re.compile(r"\bxox[abposr]-[a-z0-9-]{10,}"),
)
_REMOTE_CODE_PIPE = re.compile(
    r"\b(curl|wget|fetch|iwr|invoke-webrequest|invoke-restmethod)\b[^|;&\n]*\|\s*(sudo\s+)?"
    r"((ba|z|da|k|fi)?sh|python3?|perl|ruby|node|iex|invoke-expression)\b"
)
_URL_HOST = re.compile(r"[a-z][a-z0-9+.-]*://(?:[^/@\s]*@)?(\[[^\]]+\]|[^/:?#\s]+)")
_METADATA_HOSTNAMES = {"metadata.google.internal", "metadata", "metadata.azure.com", "instance-data",
                       "instance-data.ec2.internal"}
_METADATA_NETS = (ipaddress.ip_network("169.254.0.0/16"), ipaddress.ip_network("fd00:ec2::254/128"),
                  ipaddress.ip_network("100.100.100.200/32"))


def _normalized_views(value: Any, _depth: int = 0) -> list[str]:
    """Every string leaf and dict key, decoded and canonicalized for matching."""
    if _depth > 32:
        return ["<depth-limit>"]
    out: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            out.extend(_normalized_views(str(k), _depth + 1))
            out.extend(_normalized_views(v, _depth + 1))
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            out.extend(_normalized_views(v, _depth + 1))
    elif value is not None:
        text = str(value)
        for _ in range(3):  # repeated percent-decoding defeats double encoding
            decoded = unquote(text)
            if decoded == text:
                break
            text = decoded
        text = unicodedata.normalize("NFKC", text).lower().replace("\\", "/")
        text = re.sub(r"(?<!:)/{2,}", "/", text)  # keep scheme://
        out.append(text)
    return out


def _parse_ipv4_any_radix(host: str) -> Optional[ipaddress.IPv4Address]:
    """inet_aton semantics: 1-4 parts, each decimal, 0x-hex or 0-octal."""
    parts = host.split(".")
    if not 1 <= len(parts) <= 4:
        return None
    try:
        nums = [int(p, 16) if p.startswith("0x") else int(p, 8) if len(p) > 1 and p.startswith("0") else int(p)
                for p in parts]
    except ValueError:
        return None
    *head, last = nums
    if any(n > 255 for n in head) or last >= 256 ** (5 - len(parts)):
        return None
    value = 0
    for n in head:
        value = value * 256 + n
    value = value * 256 ** (5 - len(parts)) + last
    return ipaddress.IPv4Address(value) if value < 2 ** 32 else None


def _is_metadata_host(host: str) -> bool:
    host = host.strip("[]").rstrip(".")
    if host in _METADATA_HOSTNAMES:
        return True
    addr: Any = None
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        addr = _parse_ipv4_any_radix(host)
    if addr is None:
        return False
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return any(addr in net for net in _METADATA_NETS if addr.version == net.version)


def _builtin_findings(views: list[str]) -> list[tuple[str, str]]:
    """Return (reason_code, description) for every built-in detector that fires."""
    found: list[tuple[str, str]] = []
    for v in views:
        if any(p in v for p in _CREDENTIAL_PATHS) or v.startswith((".ssh/", "~/.ssh", "~/.aws/", "~/.kube/")):
            found.append(("CREDENTIAL_PATH", "argument references a credential store"))
        if _TRAVERSAL.search(v):
            found.append(("PATH_TRAVERSAL", "argument contains a parent-directory segment"))
        if any(rx.search(v) for rx in _SECRET_MATERIAL):
            found.append(("SECRET_IN_ARGUMENTS", "argument carries credential material"))
        if _REMOTE_CODE_PIPE.search(v):
            found.append(("REMOTE_CODE_PIPE", "argument pipes downloaded content into an interpreter"))
        for host in _URL_HOST.findall(v):
            if _is_metadata_host(host):
                found.append(("METADATA_ENDPOINT", f"URL targets a cloud metadata endpoint ({host})"))
    return found


def _reasoning_is_substantive(reasoning: Optional[str], min_chars: int, min_words: int) -> bool:
    if not reasoning:
        return False
    text = " ".join(reasoning.split())
    return len(text) >= min_chars and len(text.split(" ")) >= min_words and len(set(text)) > 4


class GuardianPolicy:
    """
    Inline Guardian policy evaluator. Runs per-call argument inspection.

    PRODUCTION: Route to remote OPA Guardian sidecar or NEXUSGuardianClient.
    TESTING:    evaluate() runs inline with no network required. All tests
                use this path with deterministic policy rules.

    Policy hierarchy (checked in order, first match wins):
      1. Revocation list (hard deny)
      2. Delegation scope overflow (deny if requested > inherited)
      3. Memory zone enforcement (deny if PERMANENT without mandate)
      4. Argument-level tool policies (deny /etc/passwd, etc.)
      5. ACT tier capability check (deny ACT-1 doing ACT-3 ops)
      6. Default: allow

    This catches attacks that OPA scope enforcement cannot:
      "Legitimate VCC + illegitimate specific argument" (e.g., email:read
       VCC, but action_arguments["path"] = "/etc/shadow")
    """

    def __init__(self,
                 revoked_dids: Optional[list[str]] = None,
                 blocked_argument_patterns: Optional[list[str]] = None,
                 max_delegation_depth: int = 4,
                 require_reasoning_for_act_tiers: Optional[list[int]] = None,
                 builtin_detectors: bool = True,
                 treat_undeclared_tier_as: Optional[int] = 4,
                 min_reasoning_chars: int = 40,
                 min_reasoning_words: int = 5,
                 aim_registry: Optional["AIMRegistry"] = None):
        self.revoked_dids = set(revoked_dids or [])
        self.blocked_argument_patterns = blocked_argument_patterns or [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
            "../../", "../..", ".ssh/id_rsa",
            "metadata/credentials", "169.254.169.254",  # IMDS
        ]
        self.max_delegation_depth = max_delegation_depth
        # ACT-3 and ACT-4 require reasoning chain before execution
        self.require_reasoning_for_act_tiers = require_reasoning_for_act_tiers or [3, 4]
        # Credential paths, traversal, metadata endpoints, secret material and
        # download-to-interpreter pipes, matched on normalized arguments.
        self.builtin_detectors = builtin_detectors
        # An undeclared tier is unknown capability: treat it as ACT-4 so HEAR
        # applies. None restores v0.3 behavior (undeclared tier skips HEAR).
        self.treat_undeclared_tier_as = treat_undeclared_tier_as
        # HEAR needs a reason a reviewer can act on, not any non-empty string.
        self.min_reasoning_chars = min_reasoning_chars
        self.min_reasoning_words = min_reasoning_words
        # AIM v0.3 registry: when set, the registered ACT tier governs and an
        # unregistered agent is denied. Request-supplied tiers become claims.
        self.aim_registry = aim_registry

    def evaluate(self, ctx: GuardianStepContext) -> GuardianVerdictResult:
        """
        Evaluate a step context and return a verdict BEFORE action execution.
        Called synchronously - the agent waits for this result.
        """
        # Rule 1: Revocation hard deny
        if ctx.agent.agent_did in self.revoked_dids:
            return GuardianVerdictResult(
                decision=GuardianVerdict.DENY,
                step_id=ctx.step_id,
                reasoning="Agent DID is in revocation list",
                reason_codes=["REVOKED_AGENT"],
            )

        # Rule 1b: Registered identity and tier (AIM v0.3, IETF draft 3.1.1)
        registered = None
        if self.aim_registry is not None:
            registered = self.aim_registry.resolve(ctx.agent.agent_did)
            if registered is None:
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning="Agent has no registered AIM",
                    reason_codes=["AIM_NOT_REGISTERED"],
                )
            if ctx.agent.aim_digest and ctx.agent.aim_digest != registered.aim_digest:
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning="Presented AIM digest does not match the registered AIM",
                    reason_codes=["AIM_DIGEST_MISMATCH"],
                )
            claimed = ctx.agent.act_tier
            if isinstance(claimed, int) and not isinstance(claimed, bool) and claimed > registered.act_tier:
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=f"Declared ACT-{claimed} exceeds registered ACT-{registered.act_tier}",
                    reason_codes=["ACT_TIER_EXCEEDS_REGISTERED"],
                )

        # Rule 2: Delegation scope overflow (catch what OPA scope categories miss)
        if ctx.parent_vcc_capabilities and ctx.vcc_capabilities:
            overflow = [c for c in ctx.vcc_capabilities
                        if c not in ctx.parent_vcc_capabilities]
            if overflow:
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=f"Requested capabilities exceed inherited scope: {overflow}",
                    reason_codes=["SCOPE_OVERFLOW", "DELEGATION_VIOLATION"],
                )

        # Rule 3: Delegation depth circuit breaker
        if ctx.delegation_depth > self.max_delegation_depth:
            return GuardianVerdictResult(
                decision=GuardianVerdict.DENY,
                step_id=ctx.step_id,
                reasoning=f"Delegation depth {ctx.delegation_depth} exceeds maximum {self.max_delegation_depth}",
                reason_codes=["DELEGATION_DEPTH_EXCEEDED"],
            )

        # Rule 4: Memory zone enforcement
        if ctx.method in (StepMethod.MEMORY_STORE, StepMethod.MEMORY_CONTEXT_RETRIEVAL):
            verdict = self._evaluate_memory(ctx)
            if verdict is not None:
                return verdict

        # Rule 5: Tool call argument inspection
        if ctx.method == StepMethod.TOOL_CALL_REQUEST and ctx.action_arguments:
            verdict = self._evaluate_tool_arguments(ctx)
            if verdict is not None:
                return verdict

        # Rule 6: ACT tier reasoning requirement (HEAR)
        tier = ctx.agent.act_tier
        tier_codes: list[str] = []
        if tier is not None and (isinstance(tier, bool) or not (isinstance(tier, int) and 1 <= tier <= 4)):
            return GuardianVerdictResult(
                decision=GuardianVerdict.DENY,
                step_id=ctx.step_id,
                reasoning=f"ACT tier {tier!r} is not one of 1-4",
                reason_codes=["ACT_TIER_INVALID"],
            )
        if registered is not None:
            # The registered tier governs; a lower claim cannot skip HEAR.
            tier, tier_codes = registered.act_tier, ["ACT_TIER_FROM_REGISTRY"]
        elif tier is None and self.treat_undeclared_tier_as is not None:
            tier, tier_codes = self.treat_undeclared_tier_as, ["ACT_TIER_UNDECLARED"]
        if tier in self.require_reasoning_for_act_tiers and ctx.method == StepMethod.TOOL_CALL_REQUEST:
            if not ctx.reasoning:
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=f"ACT-{tier} agents must provide reasoning chain before tool execution",
                    reason_codes=["REASONING_REQUIRED", "HEAR_DOCTRINE", *tier_codes],
                )
            if not _reasoning_is_substantive(ctx.reasoning, self.min_reasoning_chars, self.min_reasoning_words):
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=(f"ACT-{tier} reasoning is too thin to review (need >= {self.min_reasoning_chars} "
                               f"chars and >= {self.min_reasoning_words} words)"),
                    reason_codes=["REASONING_INSUFFICIENT", "HEAR_DOCTRINE", *tier_codes],
                )

        # Rule 7: PERMANENT memory write requires mandate
        if ctx.method == StepMethod.MEMORY_STORE:
            if (ctx.nexus_provenance and
                    ctx.nexus_provenance.zone == "PERMANENT_MEMORY" and
                    not ctx.nexus_provenance.mandate_id):
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning="PERMANENT_MEMORY write requires mandate_id (HEAR Doctrine)",
                    reason_codes=["NO_MANDATE", "HEAR_DOCTRINE"],
                )

        # Rule 8: Memory drift threshold (tighter Guardian-level check)
        if (ctx.method == StepMethod.MEMORY_STORE and
                ctx.nexus_provenance and
                ctx.nexus_provenance.drift_score is not None):
            if ctx.nexus_provenance.drift_score > 0.25:  # Tighter than Vaccine's 0.30
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=f"Memory drift score {ctx.nexus_provenance.drift_score:.3f} exceeds Guardian threshold 0.25",
                    reason_codes=["MEMORY_DRIFT_EXCEEDED", "POTENTIAL_POISONING"],
                )

        # Default: allow
        result = GuardianVerdictResult(
            decision=GuardianVerdict.ALLOW,
            step_id=ctx.step_id,
            reasoning="All policies passed",
        )
        result.compute_nor_fingerprint(ctx)
        return result

    def _evaluate_memory(self, ctx: GuardianStepContext) -> Optional[GuardianVerdictResult]:
        """Evaluate memory operation against provenance constraints."""
        if not ctx.nexus_provenance:
            return None  # No provenance info - allow (Vaccine will enforce)

        prov = ctx.nexus_provenance

        # Stale checkpoint check (>48h since last checkpoint)
        if prov.checkpoint_timestamp:
            try:
                from datetime import datetime, timezone
                checkpoint_dt = datetime.fromisoformat(prov.checkpoint_timestamp.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                age_hours = (now - checkpoint_dt).total_seconds() / 3600
                if age_hours > 48:
                    return GuardianVerdictResult(
                        decision=GuardianVerdict.DENY,
                        step_id=ctx.step_id,
                        reasoning=f"Memory checkpoint is {age_hours:.1f}h old (max 48h). Checkpoint required.",
                        reason_codes=["STALE_CHECKPOINT"],
                    )
            except (ValueError, TypeError):
                pass  # Malformed timestamp - do not block, log

        return None

    def _evaluate_tool_arguments(self, ctx: GuardianStepContext) -> Optional[GuardianVerdictResult]:
        """
        Per-argument inspection: block attacks that match scope but violate intent.
        This is the key gap ACS fills - NEXUS OPA enforces tool categories;
        Guardian enforces specific argument values.
        """
        args = ctx.action_arguments or {}
        views = _normalized_views(args)

        findings: list[tuple[str, str]] = []
        for pattern in self.blocked_argument_patterns:
            needle = pattern.lower()
            if any(needle in v for v in views):
                findings.append(("BLOCKED_ARGUMENT_PATTERN", f"Tool argument matches blocked pattern: {pattern}"))
                findings.append(("POTENTIAL_PATH_TRAVERSAL", f"Tool argument matches blocked pattern: {pattern}"))
        if self.builtin_detectors:
            findings.extend(_builtin_findings(views))
        if findings:
            # Report every rule that fired, so a denial explains itself completely.
            return GuardianVerdictResult(
                decision=GuardianVerdict.DENY,
                step_id=ctx.step_id,
                reasoning="; ".join(sorted({desc for _, desc in findings})),
                reason_codes=sorted({code for code, _ in findings}),
            )

        # Detect credential: tool scope in wrong context (belt and suspenders over OPA)
        tool_name = ctx.action_method or ""
        if tool_name.startswith("credential:"):
            return GuardianVerdictResult(
                decision=GuardianVerdict.DENY,
                step_id=ctx.step_id,
                reasoning="credential: tools require CREDENTIAL_SURFACE context, not TASK_CONTEXT",
                reason_codes=["CONTEXT_VIOLATION", "CREDENTIAL_SURFACE_REQUIRED"],
            )

        return None


# ── Guardian Client (Remote Invocation) ───────────────────────────────────────

class NEXUSGuardianClient:
    """
    Client for remote Guardian service invocation.
    PRODUCTION: Point at a Guardian sidecar running behind mTLS.
    TESTING:    Use inline_policy=GuardianPolicy() for local evaluation.

    Failover modes (P2 gap closure):
      FAIL_CLOSED: deny all actions when Guardian unavailable (secure default)
      FAIL_OPEN:   allow all actions when Guardian unavailable (high-availability)
      FAIL_MANDATE_ONLY: deny only mandate-required actions (balanced)

    The fail_mode selection is a SECURITY POLICY DECISION, not a config choice.
    Document your chosen mode in your AIM and explain it in your threat model.
    """

    FAIL_CLOSED = "fail_closed"
    FAIL_OPEN   = "fail_open"
    FAIL_MANDATE_ONLY = "fail_mandate_only"

    def __init__(self,
                 guardian_url: Optional[str] = None,
                 inline_policy: Optional[GuardianPolicy] = None,
                 fail_mode: str = "fail_closed",
                 heartbeat_interval_sec: int = 30,
                 sla_max_latency_ms: int = 200):
        """
        Args:
            guardian_url: Remote Guardian endpoint (None = inline mode)
            inline_policy: Policy for inline evaluation (used when no remote URL)
            fail_mode: Behavior when Guardian is unreachable
            heartbeat_interval_sec: Guardian liveness probe frequency
            sla_max_latency_ms: Max acceptable Guardian response time
        """
        self.guardian_url = guardian_url
        self.inline_policy = inline_policy or GuardianPolicy()
        self.fail_mode = fail_mode
        self.heartbeat_interval_sec = heartbeat_interval_sec
        self.sla_max_latency_ms = sla_max_latency_ms
        self._available = True  # Optimistic initial state; updated by heartbeat

    def evaluate(self, ctx: GuardianStepContext) -> GuardianVerdictResult:
        """
        Evaluate a step context against the Guardian.
        Inline evaluation if no remote URL configured; remote otherwise.
        """
        if not self.guardian_url:
            # Inline evaluation (testing and edge deployments)
            return self.inline_policy.evaluate(ctx)

        # Remote invocation (production)
        try:
            return self._invoke_remote(ctx)
        except Exception as e:
            return self._handle_guardian_unavailable(ctx, str(e))

    def _invoke_remote(self, ctx: GuardianStepContext) -> GuardianVerdictResult:
        """
        POST AOS JSON-RPC 2.0 request to remote Guardian.
        PRODUCTION: Replace with actual httpx async client + mTLS certs.
        """
        try:
            import httpx
            payload = {
                "jsonrpc": "2.0",
                "id": ctx.step_id,
                "method": ctx.method.value,
                "params": ctx.to_jsonrpc_params(),
            }
            # PRODUCTION: add client certs for mTLS
            resp = httpx.post(
                self.guardian_url,
                json=payload,
                timeout=self.sla_max_latency_ms / 1000,
            )
            resp.raise_for_status()
            result_data = resp.json().get("result", {})
            decision_str = result_data.get("decision", "deny")
            try:
                decision = GuardianVerdict(decision_str)
            except ValueError:
                decision = GuardianVerdict.DENY
            return GuardianVerdictResult(
                decision=decision,
                step_id=ctx.step_id,
                reasoning=result_data.get("reasoning"),
                reason_codes=result_data.get("reasonCode", []),
                modified_request=result_data.get("modifiedRequest"),
            )
        except ImportError as exc:
            # A configured remote Guardian that cannot be called is unavailable.
            # v0.3 silently evaluated the default inline policy here, bypassing
            # the remote policy and the configured fail mode.
            raise RuntimeError("httpx is not installed; remote Guardian cannot be invoked "
                               "(pip install 'nexus-a2a-sdk[full]')") from exc

    def _handle_guardian_unavailable(self, ctx: GuardianStepContext,
                                      error: str) -> GuardianVerdictResult:
        """
        Guardian failover handler. The fail_mode is a security policy decision.
        FAIL_CLOSED is the secure default; document your choice in your AIM.
        """
        self._available = False

        if self.fail_mode == self.FAIL_OPEN:
            return GuardianVerdictResult(
                decision=GuardianVerdict.ALLOW,
                step_id=ctx.step_id,
                reasoning=f"Guardian unavailable (fail-open): {error}",
                reason_codes=["GUARDIAN_UNAVAILABLE_FAIL_OPEN"],
            )

        if self.fail_mode == self.FAIL_MANDATE_ONLY:
            # Allow non-mandate operations; deny mandate-required ops
            if ctx.action_method and "mandate_required" in (ctx.action_method or ""):
                return GuardianVerdictResult(
                    decision=GuardianVerdict.DENY,
                    step_id=ctx.step_id,
                    reasoning=f"Guardian unavailable; mandate-required operation denied: {error}",
                    reason_codes=["GUARDIAN_UNAVAILABLE_MANDATE_DENIED"],
                )
            return GuardianVerdictResult(
                decision=GuardianVerdict.ALLOW,
                step_id=ctx.step_id,
                reasoning=f"Guardian unavailable (fail-mandate-only): {error}",
                reason_codes=["GUARDIAN_UNAVAILABLE_NON_MANDATE_ALLOWED"],
            )

        # Default: FAIL_CLOSED - deny everything
        return GuardianVerdictResult(
            decision=GuardianVerdict.DENY,
            step_id=ctx.step_id,
            reasoning=f"Guardian unavailable (fail-closed): {error}",
            reason_codes=["GUARDIAN_UNAVAILABLE_FAIL_CLOSED"],
        )

    def ping(self) -> bool:
        """
        Guardian liveness probe. Called on heartbeat_interval_sec schedule.
        Returns True if Guardian is reachable, updates internal availability flag.
        """
        if not self.guardian_url:
            self._available = True
            return True
        try:
            import httpx
            resp = httpx.get(
                self.guardian_url.rstrip("/") + "/health",
                timeout=2.0,
            )
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    @property
    def is_available(self) -> bool:
        return self._available


# ── Step Context Builders (convenience API) ───────────────────────────────────

def build_tool_call_step(
    agent_did: str,
    spiffe_id: str,
    tool_name: str,
    tool_arguments: dict,
    vcc_id: Optional[str] = None,
    vcc_capabilities: Optional[list[str]] = None,
    parent_vcc_capabilities: Optional[list[str]] = None,
    delegation_depth: int = 0,
    act_tier: Optional[int] = None,
    reasoning: Optional[str] = None,
    cael_envelope_hash: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> GuardianStepContext:
    """
    Build a steps/toolCallRequest StepContext - the most critical interception point.
    Called AFTER LLM inference but BEFORE tool execution. The Guardian sees:
      - The actual tool arguments the LLM chose
      - The agent's reasoning chain (if provided)
      - The full delegation context

    This is where "legitimate credential, illegitimate use" attacks are caught.
    """
    agent = NEXUSAgentContext(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        act_tier=act_tier,
    )
    ctx = GuardianStepContext(
        method=StepMethod.TOOL_CALL_REQUEST,
        agent=agent,
        action_method=tool_name,
        action_arguments=tool_arguments,
        vcc_id=vcc_id,
        vcc_capabilities=vcc_capabilities,
        parent_vcc_capabilities=parent_vcc_capabilities,
        delegation_depth=delegation_depth,
        reasoning=reasoning,
        cael_envelope_hash=cael_envelope_hash,
        trace_id=trace_id,
    )
    if reasoning:
        ctx.compute_reasoning_hash()
    return ctx


def build_memory_store_step(
    agent_did: str,
    spiffe_id: str,
    memory_content: list[str],
    provenance: Optional[NEXUSMemoryProvenance] = None,
    delegation_depth: int = 0,
) -> GuardianStepContext:
    """
    Build a steps/memoryStore StepContext with NEXUS provenance metadata.
    The Guardian receives memory content + provenance, enabling:
      - Drift score enforcement (tighter than Vaccine threshold)
      - Temporal constraint checking (stale checkpoint detection)
      - Mandate verification for PERMANENT zone writes
    """
    agent = NEXUSAgentContext(agent_did=agent_did, spiffe_id=spiffe_id)
    return GuardianStepContext(
        method=StepMethod.MEMORY_STORE,
        agent=agent,
        memory_content=memory_content,
        nexus_provenance=provenance,
        delegation_depth=delegation_depth,
    )
