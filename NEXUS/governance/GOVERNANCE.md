# NEXUS-A2A Multi-Sovereign Governance Charter

**Version:** 0.3 (Draft for Public Comment)
**Status:** Pre-formation -- open for steering committee nominations
**Issued by:** Cyber Strategy Institute
**Contact:** governance@cyberstrategyinstitute.com

---

## Preamble

NEXUS-A2A addresses a governance problem that no single organization can own.
The security of agentic AI communication at planetary scale requires a protocol
standard that is architecturally sound, institutionally independent, and
resilient to capture by any single commercial or national interest.

This charter establishes the governance model for NEXUS-A2A's evolution from
a Cyber Strategy Institute specification to an open, multi-sovereign standard.
The target structure mirrors successful precedents (OpenTelemetry, SPIFFE/SPIRE,
IETF working groups) while incorporating the specific sovereignty requirements
that agentic AI governance demands.

---

## Article I -- Name and Mission

**1.1 Name:** NEXUS-A2A Technical Governance Committee (NEXUS-TGC)

**1.2 Mission:** To govern the evolution of the NEXUS-A2A specification as an
open, vendor-neutral, sovereignty-preserving protocol standard for secure
agentic AI communication. The NEXUS-TGC ensures that protocol amendments
reflect the interests of the broader security community, not any single
commercial or governmental actor.

**1.3 Scope:** The NEXUS-TGC governs:

- The NEXUS-A2A core specification (Layers L1-L6)
- The NEXUS-ACS Bridge Specification
- The AISM Invariant set (I-1 through I-6)
- The NEXUS schema registry (NOR, AgBOM, Guardian, AIM)
- The HEAR Doctrine normative requirements
- The NEXUS Certification Authority (NCA) trust anchor criteria

The NEXUS-TGC does not govern commercial implementations, hosted deployments,
or third-party extensions that operate in the nexus: extension namespace.

---

## Article II -- Composition

**2.1 Steering Committee**

The NEXUS-TGC Steering Committee consists of five to nine seats:

| Seat Type | Count | Eligibility | Term |
|-----------|-------|-------------|------|
| Founding | 1 | Cyber Strategy Institute (non-voting on technical disputes) | Permanent |
| Elected Technical | 4-6 | Any individual with material contribution to the specification | 2 years, renewable once |
| Independent Security | 2 | Security researchers with no commercial interest in NEXUS implementations | 2 years |

**2.2 Workstream Leads**

The NEXUS-TGC establishes the following workstreams, each with an appointed lead:

- **L1-L2 Identity and Transport:** SPIFFE/SPIRE integration, DID methods, PQC roadmap
- **L3 Policy Enforcement:** OPA/Rego governance, Guardian protocol, ACS bridge alignment
- **L4 Memory and Context:** Memory Vaccine specification, AgBOM standards, ATPA defense
- **L5 Economic Governance:** JouleWork specification, ZHC protocol, billing amplification defense
- **L6 Self-Evolution:** Constitutional constraints, amendment pipeline, incident corpus
- **Compliance and Regulatory:** Framework mapping maintenance (32+ frameworks), regulatory engagement

**2.3 Founding Seat**

The Cyber Strategy Institute holds the founding seat for the duration of Phase 1
(inception through 50 production deployments). The founding seat is non-voting
on technical disputes but retains veto power over changes to:

- The six AISM Invariants (I-1 through I-6)
- The HEAR Doctrine constitutional constraints (CP.10)
- The AI SAFE2 v3.0 compliance mapping matrix

This veto is exercised only to prevent governance capture or regulatory
non-compliance, not to block competitive technical evolution.

---

## Article III -- Amendment Process

**3.1 Standard Amendment**

Any member of the community may submit an amendment proposal (AP) via GitHub
pull request to the NEXUS-A2A specification repository. An AP must include:

- Problem statement with specific risk or interoperability gap addressed
- Proposed normative language change (diff format)
- AI SAFE2 v3.0 control mapping for any new security requirement
- Compliance impact statement (which of the 32 mapped frameworks are affected)
- Reference implementation or test case demonstrating the change

Standard APs are accepted by majority vote of the Steering Committee after a
14-day public comment period.

**3.2 Constitutional Amendment**

Changes to the six AISM Invariants or HEAR Doctrine constitutional constraints
require:

- Steering Committee supermajority (6 of 7 seats minimum)
- 30-day public comment period
- Explicit statement that the change does not reduce human authority over
  ACT-3+ agent operations
- Independent security review by at least one member with no commercial interest

**3.3 Emergency Amendment**

In response to a critical security vulnerability (CVSS 9.0+) affecting the
NEXUS protocol, the founding seat and any two Steering Committee members may
authorize an emergency patch with a 72-hour comment period. Emergency amendments
are reviewed for normative adoption within 60 days.

**3.4 L6 Cryptographic Amendment Pipeline (Phase 2, 2027)**

Upon delivery of the L6 Governance Plane, amendments to normative security
controls will be anchored to a cryptographic amendment log: each accepted AP
produces a signed entry in the amendment corpus, and all deployed NEXUS
implementations can verify their protocol version against the signed chain.
This prevents silent fork divergence at scale.

---

## Article IV -- Constitutional Constraints

The following constraints are permanent and cannot be amended by any governance
process. They represent the foundational sovereignty commitments of NEXUS-A2A:

**CC-1 Human Override Preservation:** No amendment may reduce the ability of
a human with appropriate authority to terminate, suspend, or roll back any
NEXUS-governed agent or delegation chain.

**CC-2 Scope Monotonicity:** No amendment may introduce a mechanism by which a
delegated agent can hold permissions exceeding its principal's grant. Scope
narrows at every delegation hop, always.

**CC-3 Memory Provenance Non-Negotiable:** No amendment may remove the
requirement for cryptographic provenance on cross-session and permanent memory
writes. The four memory zones (SESSION, CROSS_SESSION, PERMANENT, SWARM_SHARED)
and their differential provenance requirements are immutable.

**CC-4 No Silent Cryptographic Downgrade:** No amendment may permit a NEXUS
implementation to silently downgrade cryptographic primitives below the
specified minimum (Ed25519 for signatures, SHA-256 for content hashing, mTLS 1.3
for transport). PQC adoption may be accelerated but not delayed below CNSA 2.0
timelines.

**CC-5 Vendor Neutrality:** No amendment may introduce a dependency on a
proprietary service, algorithm, or infrastructure component that is not
available under an open license. NEXUS-Full must be deployable by any
organization with access to open-source tooling.

---

## Article V -- Relationship to External Standards Bodies

**5.1 IETF**

The NEXUS-TGC targets submission of NEXUS L1-L2 (identity and transport
specification) as an IETF Internet-Draft by Q4 2026. The NEXUS-ACS Bridge
Specification will be submitted as a joint contribution with the ACS community.

**5.2 OWASP**

NEXUS maps to the OWASP Agentic AI Security Top 10 (ASI01-ASI10). The
NEXUS-TGC maintains the ASI crosswalk in the compliance/ directory and
contributes to OWASP Agentic AI working group activities.

**5.3 W3C**

NEXUS L2 DID/VC integration will be submitted as a W3C Community Group Note
through the Decentralized Identifier Working Group, targeting interoperability
with the W3C DID Core specification.

**5.4 Linux Foundation / AAIF**

The Agentic AI Foundation (AAIF) under the Linux Foundation governs MCP
evolution. The NEXUS-TGC engages the AAIF through the CP.5.MCP contribution
channel and proposes NEXUS L2 identity layer as the security profile standard
for MCP gateway deployments.

**5.5 ACS Community**

The NEXUS-ACS Bridge Specification is a joint contribution. NEXUS-TGC
workstream leads participate in ACS enforcement workstream activities and the
NEXUS AISM Invariants are published as ACS Guardian policy templates.

---

## Article VI -- Phase Roadmap

| Phase | Timeline | Governance Milestone |
|-------|----------|---------------------|
| Phase 1 | 2026 | NEXUS-TGC formation; 5-member steering committee; NCA beta launch |
| Phase 2 | 2027 | L6 Governance Plane MVP; cryptographic amendment pipeline operational |
| Phase 3 | 2028 | Full multi-sovereign governance body; IETF working group status |
| Phase 4 | 2030 | Constitutional constraints reviewed at EX-4 agent population |

---

## Article VII -- Nomination Process

Steering Committee nominations for Phase 1 formation are open from June 1, 2026
through September 1, 2026. Nominations must include:

- GitHub handle with documented contributions to NEXUS-A2A or AI agent security
- Statement of affiliation and any commercial interests in NEXUS implementations
- Signed acknowledgment of Constitutional Constraints (CC-1 through CC-5)

Submit nominations via GitHub issue in CyberStrategyInstitute/ai-safe2-framework
with label: `nexus-governance-nomination`.

---

*This charter is a governance instrument, not a technical specification.
Binding normative requirements are in the NEXUS-A2A specification documents
in the /spec/ directory and are enforced via the amendment process above.*
