# IETF Internet-Draft: NEXUS-A2A Layer 1-2 -- Secure Agent Identity and Transport

**Draft Name:** draft-csi-nexus-agent-identity-00
**Intended Status:** Proposed Standard (Informational for this pre-submission framing)
**Expires:** 6 months from publication date
**Author:** Cyber Strategy Institute
**Contact:** standards@cyberstrategyinstitute.com

---

> **Note:** This document is a pre-submission framing document prepared to
> structure the IETF Internet-Draft submission for NEXUS L1-L2. It follows
> RFC 7322 (RFC Style Guide) formatting conventions. The formal I-D will be
> submitted following NEXUS-TGC formation and community review.

---

## Abstract

The proliferation of autonomous AI agents communicating over open protocols
has produced a structural security gap: no normative standard exists for
agent identity, workload attestation, cryptographically-enforced delegation,
or sovereign memory governance. Existing protocols (MCP, A2A, ACP) provide
communication semantics without security architecture.

This document specifies NEXUS-A2A Layers 1 and 2: the Transport Security
Profile (L1) and the Agent Identity and Delegation Protocol (L2). L1 defines
mandatory cryptographic transport requirements including Post-Quantum
Cryptography (PQC) hybrid cipher suites aligned with CNSA 2.0. L2 defines
the Agent Identity Manifest (AIM), Verifiable Capability Credential (VCC),
delegation chain governance with scope attenuation, and the NEXUS Agent
Name Service (ANS) for trustworthy capability discovery.

Together, L1 and L2 provide the identity and transport foundation that
all higher-layer agent governance protocols require.

---

## 1. Introduction

### 1.1 Problem Statement

Agent-to-agent communication in 2026 production deployments exhibits the
following security properties by default:

- **No cryptographic agent identity.** Authentication is trust-on-first-use,
  bearer token, or bare string identifier. No protocol provides workload-level
  cryptographic binding between an agent's claimed identity and its execution
  environment.

- **No delegation governance.** When Agent A delegates to Agent B, no protocol
  enforces that B's permission scope is a subset of A's. Permission amplification
  across delegation hops is architecturally permitted by every deployed protocol.

- **No memory provenance.** Agent memory persistence mechanisms carry no
  provenance metadata. Cross-session memory writes are indistinguishable from
  injected content.

- **No post-quantum resistance.** All deployed agent protocols use classical
  TLS cipher suites susceptible to harvest-now-decrypt-later attacks.

The consequences of this design state are documented in CSI Research Notes
023 and 024, the OWASP Agentic AI Top 10, and the May 2026 NSA AISC Advisory
on MCP Security.

### 1.2 Design Principles

NEXUS L1-L2 adheres to the following design principles:

- **Identity-first:** Cryptographic workload attestation is a precondition,
  not an optional overlay.
- **Delegation-native:** The delegation graph is a first-class protocol primitive.
  Scope attenuation is normatively required at every delegation hop.
- **Sovereignty-preserving:** Human authority over agent action must be
  cryptographically enforceable, not procedurally assumed.
- **Interoperability:** L1-L2 wraps existing protocols (MCP, A2A, ACS) rather
  than replacing them. The NEXUS-MCP bridge and NEXUS-ACS bridge preserve
  full ecosystem compatibility.

### 1.3 Terminology

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as
described in BCP 14, RFC 2119, RFC 8174.

**Agent:** An autonomous software entity that executes tasks, calls tools, and
communicates with other agents using protocol messages.

**AIM:** Agent Identity Manifest. The signed capability declaration that
establishes an agent's identity, capability scope, and governance constraints.

**VCC:** Verifiable Capability Credential. A signed, scoped, time-limited
authorization that governs what an agent may do within a delegation relationship.

**ANS:** Agent Name Service. A signed registry mapping agent DIDs to their
current AIM, enabling capability verification without trusted third party.

**DID:** Decentralized Identifier per W3C DID Core 1.0 [RFC:DID-CORE].

**SPIFFE SVID:** SPIFFE Verifiable Identity Document per SPIFFE specification
[RFC:SPIFFE]. Provides process-level workload attestation.

**NOR:** NEXUS Output Receipt. A cryptographic audit receipt produced for
every agent action, providing non-repudiable chain-of-custody evidence.

**HEAR:** Human Executive Authority and Response. The normative requirement
that ACT-Tier 3 and 4 agents operate under cryptographically enforced
human authority with a functional kill switch.

---

## 2. Layer 1 -- Transport Security Profile

### 2.1 Mandatory Requirements

All NEXUS-conformant agent communication MUST satisfy the following transport
security requirements:

**L1.1 mTLS 1.3:** All agent-to-agent communication MUST use TLS 1.3 with
mutual authentication. TLS 1.2 is not permitted. Cipher suites MUST include:
`TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256`.

**L1.2 SPIFFE SVID:** Each communicating agent MUST present a SPIFFE
Verifiable Identity Document (SVID) during TLS handshake. The SVID MUST
be issued by a NEXUS-registered SPIFFE trust domain.

**L1.3 Certificate Lifetime:** Agent TLS certificates MUST have a maximum
lifetime of 24 hours. Automated certificate rotation MUST be implemented.

**L1.4 Revocation:** Revocation of a compromised agent certificate MUST
propagate to all delegates within 500 milliseconds via the NEXUS kill-switch
propagation pathway.

### 2.2 Post-Quantum Cryptography (PQC) -- NEXUS-Full Mode

NEXUS-Full mode (required for ACT-Tier 3 and 4 agents and for FedRAMP HIGH,
CMMC 2.0 Level 3, and ITAR deployments) MUST additionally implement:

**L1.5 PQC Key Exchange:** ML-KEM-1024 (CRYSTALS-KYBER, NIST FIPS 203)
hybrid with X25519 for key exchange. This provides harvest-now-decrypt-later
resistance aligned with CNSA 2.0 Algorithm Suite timelines.

**L1.6 PQC Signatures:** ML-DSA-65 (CRYSTALS-Dilithium, NIST FIPS 204)
for all long-lived agent identity signatures (AIM signing, VCC issuance,
NOR fingerprinting).

**Rationale:** At projected agent population growth rates (48.5% CAGR),
inter-agent communication traffic generated in 2026-2030 will mature as a
harvest-now-decrypt-later target by the time CRQCs become available. NEXUS
mandates PQC now, before the harvest window closes.

### 2.3 Circuit Breaker Constraints

To prevent cascade failure and swarm C2 attack amplification:

**L1.7 Max Fan-Out:** An agent MUST NOT send the same message to more than
8 downstream agents simultaneously (max-fan-out=8).

**L1.8 Max Delegation Depth:** A delegation chain MUST NOT exceed 4 hops
(max-depth=4). Agents MUST reject delegation requests that would exceed
this depth.

---

## 3. Layer 2 -- Agent Identity and Delegation Protocol

### 3.1 Agent Identity Manifest (AIM)

Every NEXUS-conformant agent MUST register an Agent Identity Manifest (AIM)
before initiating any agent-to-agent communication.

**3.1.1 Required AIM Fields**

```json
{
  "agent_did": "did:nexus:agent:{identifier}",
  "spiffe_id": "spiffe://{trust-domain}/agent/{identifier}",
  "version": "0.3",
  "capability_digest": "{sha256-of-capability-declaration}",
  "act_tier": 1,
  "owner_of_record": "{email-or-identifier}",
  "hear_acknowledged": false,
  "max_delegation_depth": 2,
  "kill_switch": {
    "operator_registered": true,
    "domain_registered": false,
    "cryptographic_kill_confirmed": false
  },
  "created_utc": "{ISO-8601}",
  "signature": "{Ed25519-signature-over-canonical-aim}"
}
```

**3.1.2 AIM Signing**

The AIM MUST be signed with the agent's Ed25519 key. In NEXUS-Full mode,
the signature MUST use ML-DSA-65. The signing key MUST be generated within
the SPIFFE trust domain and bound to the SPIFFE SVID.

**3.1.3 AIM Revocation**

An AIM MUST be revocable by the agent's registered owner-of-record or by
any entity with operator-level kill-switch authority. Revocation MUST
propagate within 500ms to all delegates via the kill-switch pathway.

### 3.2 Verifiable Capability Credential (VCC)

Agent-to-agent delegation MUST be governed by a Verifiable Capability
Credential (VCC). A VCC binds a delegating principal to a delegate agent
with an explicitly scoped, time-limited permission grant.

**3.2.1 Required VCC Fields**

```json
{
  "vcc_id": "{uuid-v4}",
  "issuer_did": "{principal-did}",
  "subject_did": "{delegate-did}",
  "granted_scopes": ["{scope-1}", "{scope-2}"],
  "max_scope": "{most-permissive-allowed-scope}",
  "ttl_seconds": 3600,
  "sub_delegation_depth": 1,
  "issued_utc": "{ISO-8601}",
  "expires_utc": "{ISO-8601}",
  "signature": "{Ed25519-signature-over-canonical-vcc}"
}
```

**3.2.2 Scope Attenuation**

A VCC MUST NOT grant scopes that are not present in the issuer's own
VCC (or AIM for root agents). This is Invariant I-2 (Monotonic Scope
Narrowing). Any VCC that would violate I-2 MUST be rejected by the
NEXUS policy engine.

**3.2.3 Sub-Delegation Limits**

A VCC MUST include a `sub_delegation_depth` field indicating how many
further delegation hops the delegate may create. A delegate MUST NOT
create sub-delegations that would exceed the `sub_delegation_depth` limit.

### 3.3 Agent Name Service (ANS)

The NEXUS Agent Name Service (ANS) is a signed registry mapping agent DIDs
to their current AIM. It provides:

- Capability verification without central trusted third party
- Supply chain provenance for discovered MCP servers and tools
- ANS entries MUST be signed by the agent's AIM signing key
- Changes to ANS entries MUST trigger re-attestation by relying parties

### 3.4 Delegation Chain Governance

**3.4.1 Graph Structure**

The delegation graph is a directed acyclic graph (DAG) where edges represent
VCC grants. Each edge carries the full scope intersection of the delegating
principal's scope. No path through the graph may exhibit scope amplification.

**3.4.2 Revocation Propagation**

Revocation of any node in the delegation graph MUST propagate to all
reachable descendants within 500 milliseconds. The propagation mechanism
uses the QUARANTINE performative defined in the NEXUS APEM specification.

**3.4.3 Kill Switch Tiers**

Three kill-switch tiers are defined:

| Tier | Scope | Propagation Target |
|------|-------|--------------------|
| Operator | Single agent | Immediate suspension |
| Domain | All agents in SPIFFE trust domain | Domain-wide quarantine |
| Principal | All delegates of a specific principal | Delegation subtree severance |

---

## 4. CAEL Envelope Specification

The Cryptographically Attested Execution Ledger (CAEL) envelope wraps all
agent-to-agent messages. It provides:

- Ed25519 (or ML-DSA-65 in PQC mode) signatures over message content
- Context compartmentalization preventing credential surface leakage
- Idempotency keys preventing replay attacks
- Delegation metadata enabling end-to-end chain verification

CAEL envelopes are defined in nexus_sdk/cael.py with full JSON schema at
schemas/aim-v0.2.schema.json (updated to v0.3 in schemas/aim-v0.3.schema.json).

---

## 5. Security Considerations

### 5.1 Threat Model

NEXUS L1-L2 addresses the following threat categories from the NEXUS-vs-MCP
risk analysis (CSI Research, May 2026):

- **T2.1 (Unauthenticated Access):** Mandatory DID + SPIFFE eliminates
  unauthenticated communication boundaries.
- **T1.2 (Token Passthrough):** VCC scope binding prevents token replay
  across delegation hops.
- **T6.3 (Multi-Agent Lateral Movement):** Delegation graph with per-hop
  scope attenuation contains compromise propagation.
- **T2.4 (Post-Update Privilege Persistence):** 500ms revocation propagation
  eliminates residual access windows.

### 5.2 Assumptions and Limitations

- NEXUS L1-L2 assumes a functional SPIFFE/SPIRE deployment for production
  workload attestation. The nexus_sdk supports stub mode (use_stub_embeddings=True)
  for development, but stub mode does not satisfy ACT-Tier 3+ requirements.
- PQC (L1.5, L1.6) requires liboqs or equivalent. NEXUS-Micro profile
  (embedded systems, <128KB RAM) defers PQC to the gateway layer.
- The L6 Governance Plane (protocol self-evolution) is Phase 2 (2027).

---

## 6. IANA Considerations

This document requests registration of the following:

- NEXUS CAEL Envelope MIME type: `application/nexus-cael+json`
- NEXUS VCC MIME type: `application/nexus-vcc+json`
- NEXUS AIM MIME type: `application/nexus-aim+json`
- NEXUS-specific URI scheme: `nexus://` for ANS resolution

---

## 7. References

### 7.1 Normative References

- RFC 2119: Key words for use in RFCs to Indicate Requirement Levels
- RFC 8174: Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words
- RFC 9207: OAuth 2.0 Authorization Server Issuer Identification
- W3C DID Core 1.0: Decentralized Identifiers
- SPIFFE Specification: Secure Production Identity Framework for Everyone
- NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)
- NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)
- CNSA 2.0: Commercial National Security Algorithm Suite 2.0
- OWASP Agentic AI Security Top 10 (ASI01-ASI10)
- AOS v0.1.0: Agent Operating Standard (agentcontrolstandard.ai)

### 7.2 Informative References

- CSI Research Note 023: MCP Server Security Profile
- CSI Research Note 024: MCP Consumer Protection
- CSI NEXUS-vs-MCP Analysis (May 2026)
- CSI NEXUS-vs-ACS Analysis (May 2026)
- NSA AISC Advisory: MCP Security Considerations (May 2026)
- NEXUS-A2A Specification v0.3

---

*This document reflects the state of the NEXUS-A2A specification as of v0.3.
Feedback welcome via GitHub issues: CyberStrategyInstitute/ai-safe2-framework.*
