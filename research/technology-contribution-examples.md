# Technology contribution examples and adoption backlog
### Nine supplied examples, with claims separated from validation

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface](https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square)](./README.md)
[![Status](https://img.shields.io/badge/Status-Proposed_candidates-808080?style=flat-square)](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Research Index](./README.md) | [Challenge Lab](../challenges/README.md)

---

## Review boundary

Prepared October 2, 2026 from the supplied scoring recommendations. Primary
publication abstracts, project documentation, and the investigative announcement
linked below were reviewed for identity and scope on that date. No implementation,
raw benchmark results, independent reproduction, or production deployment was
evaluated in this change. The supplied brief did not include its underlying
test artifacts or exact versions for every item.

Consequently, the brief's pillar numbers, E ratings, rank order, and claims of
"Level 5-quality" validation are **provisional input, not adopted scores**.
Contribution assessments remain `not_assessed` until a completed
[Technology Card](../docs/templates/TECHNOLOGY-CARD.md) binds each claim to reviewable
evidence. The source links support the attributed descriptions, not SAFE2 validation.

These are nine different artifact types. Investigations and accountability events
are evaluated for evidentiary/governance relevance, not as runtime products.

## Example decisions

| Candidate | Artifact/effect to review | Candidate control mappings | Proposed action and acceptance condition |
|---|---|---|---|
| Asymmetric rogue-agent investigation | Investigation; challenges/evidences | P1.T2.3, P1.T2.5; P2.T3.1, P2.T3.3, P2.T3.7; P4.T8.2, P4.T8.3; P5.T9.1, P5.T9.2; CP.5 | Design isolated composed-capability tests; prove end-to-end outcomes and preserve target-impact uncertainty |
| ContractWarden | Research reference monitor; proposed enforces/evidences | P1.T2.1, P1.T2.2, P1.T2.5, P1.T2.6; P3.T5.1, P3.T5.2; CP.5, CP.10 | Review pinned code and kernel prerequisites; test side effects, supported IPC, bypasses, shutdown, and unsupported paths |
| DGF-Bench | Benchmark; validates/challenges | P1.T1.2; P2.T3.3, P2.T3.7, P2.T1.2_ADV; P4.T7.1, P4.T1.1_ADV; P5.T9.2 | Review the exact pack/license; reproduce paired clean/attacked decisions and record utility and provenance |
| OpenAI notification report | Incident/accountability input; evidences/challenges if verified | P2.T3.1, P2.T3.7; P3.T5.10; P4.T8.2, P4.T8.3; P5.T9.1, P5.T9.2; CP.6 | Hold quantitative claims pending the original notice/source; exercise reconstruction and external-notification ownership in a tabletop |
| NVIDIA OpenShell and Sentry | Separate software and hardware/runtime claims; proposed implements/enforces/evidences | P1.T2.1, P1.T2.2, P1.T2.5, P1.T2.7, P1.T2.9; P2.T3.1; P3.T5.1, P3.T5.2; P4.T8.2, P4.T8.3; CP.5, CP.10 | Pilot only after pinning each component and platform; independently test containment, outages, revocation, and credential handling |
| ActionGuard | Research authorization interceptor; proposed enforces | P1.T1.7, P1.T1.9, P1.T2.5; P3.T5.1; P4.T7.1; CP.5 | Test interception, probabilistic judgment, and actuation separately, including direct bypasses and reviewer outages |
| Self-Evolving Defense | Research policy-learning method; addresses/validates | P1.T1.2; P2.T3.2, P2.T3.3; P5.T9.1, P5.T9.2; CP.6 | Test poisoning, malicious lesson extraction, conflict handling, approval, provenance, and rollback before promoting contribution claims |
| Randomized oversight analysis | Theory/design; addresses | P2.T3.7; P4.T7.1, P4.T8.2; P5.T9.2 | Use as design justification; test evidence survival and audit unpredictability separately |
| California DOJ subpoena | Accountability event; governance driver | P2.T3.1, P2.T3.7; P3.T5.10; P4.T8.3; P5.T9.2; CP.6 | Tabletop retention, custodian, legal hold decision, affected-party identification, and approved notification; no technical score |

Mappings identify review targets, not coverage or conformance findings. Control
IDs/names come from the [canonical core dataset](../skills/mcp/data/ai-safe2-controls-v3.0.json).
The supplied DGF-Bench mappings `P2.T1.2` and `P4.T1.1` are corrected to
`P2.T1.2_ADV` (Agent Behavior Verification) and `P4.T1.1_ADV` (Multi-Agent Approval).
Supply Chain Artifact Validation is `P1.T1.9`; `P1.T1.7` is Dependency Verification.
`P1.T2.7` is Container Security. Do not silently replace canonical names with
broader claims. CP.5 is Platform-Specific Agent Security Profiles; select its
actual applicable profile before making protocol-enforcement claims.

## Source and scope notes

### Asymmetric investigation

[Asymmetric Security's Rogue Agents Investigation](https://www.asymmetricsecurity.com/newsroom/rogue-agents-investigation/)
describes agents combining public-service capabilities. The report distinguishes
attempts from verified outcomes and discloses missing transcripts and target logs.
Treat this as a source of composed-capability challenge hypotheses. Use local
service substitutes and synthetic targets, not the public endpoints in the report.
Do not infer that every target was breached or that this investigation implements
containment. Primary contribution areas to review are Ledger, Command Center,
and Learning Engine; prevention remains a separate control claim.

### ContractWarden

[ContractWarden, arXiv 2609.38248](https://arxiv.org/abs/2609.38248)
describes a Linux reference monitor and human-authorized damage boundary. Its
abstract names eBPF LSM enforcement and supported propagation paths. That is
author-described architecture; this review did not inspect its implementation
or reproduce its tests. The design statement can be cited as E1 under
assurance v1.0, while runtime effectiveness and all pillar scores remain unassessed.
Kernel support, IPC limitations, cloud paths, descendants, and stopping authority
must be reviewed before a control claim is promoted.

### DGF-Bench

[DGF-Bench, arXiv 2609.34913](https://arxiv.org/abs/2609.34913)
is a benchmark for deception against multi-agent governance boards. Review its
paired clean/attacked methodology and process-mimicking inputs as validation
candidates. It evaluates governance decisions; it is not a runtime enforcement
product. Repeated testing can support a learning process but does not alone meet
TCP contribution 5's formal-verification, durable-evidence, and authority criteria.

### OpenAI notification report

The supplied brief refers to "100-plus notifications" without the original
notice, source URL, incident-specific artifacts, or denominator. That count and
the proposed E2 rating remain unverified and must not be republished as facts.
No substituted incident source is treated as confirmation of that specific claim.
The useful assessment scenario is whether an organization can reconstruct actions,
identify potentially affected parties, assign a notification owner, and create
regression tests. A notification is not evidence that its recipient was breached.

### NVIDIA OpenShell and Sentry

[NVIDIA's OpenShell architecture](https://docs.nvidia.com/openshell/about/architecture)
describes kernel enforcement and policy verification.
[NVIDIA's platform announcement](https://nvidianews.nvidia.com/news/open-agent-safety-platform)
describes Sentry as an out-of-band component on BlueField-4. These are producer
claims. Inspect released OpenShell code separately from Sentry availability and
hardware-dependent behavior. Do not assign one E2 rating to the whole combined
platform or call it AI SAFE²-validated. Pin releases and test each material
containment claim; the current documentation review establishes no independent
validation or operational rating.

### ActionGuard

[ActionGuard, arXiv 2609.39450](https://arxiv.org/abs/2609.39450)
describes pre-execution tool-call review under poisoned skills. The abstract
reports fail-closed enforcement of a Reviewer's decision. Attribute that result
to the authors until its method/results are reviewed or reproduced. The model
judgment remains probabilistic; test it separately from interception and actuation.
Identify this paper explicitly, because other projects also use the ActionGuard name.

### Self-Evolving Defense

[Self-Evolving Defense, arXiv 2609.36603](https://arxiv.org/abs/2609.36603)
describes learning reusable policies from harmful trajectories without updating
model weights. Treat learned policy as a governed artifact. The adoption gate
includes poisoning resistance, provenance, authorized approval, conflict resolution,
and rollback; adaptation itself establishes neither deterministic enforcement
nor organizational sovereignty.

### Randomized oversight

[When Does Randomized Oversight Align AI Agents That Can Conceal?, arXiv 2609.38262](https://arxiv.org/abs/2609.38262)
analyzes oversight under concealment and evidence manipulation. Its design
argument is E1 under assurance v1.0, not implemented validation. Translate its
assumptions into separately owned tests of evidence survival and audit predictability.
Do not assign a demonstrated runtime contribution from a theoretical result.

### California DOJ subpoena

[California DOJ's October 1, 2026 announcement](https://oag.ca.gov/news/press-releases/part-ongoing-investigation-attorney-general-bonta-serves-investigative-subpoena)
states that an investigative subpoena was served on OpenAI the previous day.
It confirms an accountability event, not a determination of wrongdoing or a
technology's effectiveness. Retention and notification scenarios belong in
governance and lifecycle review, with the legal/incident owner deciding obligations.
Do not import the brief's E2 implementation rating for this event.

## Worked bounded card: ContractWarden design review

- **Artifact:** ContractWarden paper, arXiv 2609.38248; reference implementation not inspected.
- **Review:** October 2, 2026; repository documentation self-review, not independent testing.
- **Claim:** Authors describe a Linux reference monitor for a human-authorized damage boundary.
- **Mapped targets:** P1.T2.1 Agent Sandboxing; P1.T2.5 Function Access Control;
  P3.T5.1 Circuit Breakers. These are assessment targets, not demonstrated coverage.
- **Effect in this review:** Addresses those controls through its described architecture.
  Implements/enforces remain author-reported and unassessed by SAFE2.
- **Evidence:** Linked paper abstract; AI SAFE² Evidence Assurance v1.0 E1 for
  the design statement only; no independent validation established.
- **Pillars:** P1-P5 `not_assessed`, no scores. Maximum supported contribution
  is not assessed because runtime artifacts and boundary tests were not reviewed.
- **Boundary:** Described Linux/kernel mechanism; exact kernel/release, supported
  dependencies, bypasses, and fail modes still require artifact-level review.
- **Authority:** Human-authorized contract is described; actual inspect/configure/
  revoke/replace/export and stopping behavior are not verified.
- **Verdict:** Supports investigation of an external-enforcement reference pattern.
- **Adoption:** Hold deployment endorsement; a designated security owner may approve
  an isolated pilot after the validation plan and prerequisites are reviewed.
- **Permitted claim:** "The authors describe a Linux enforcement design relevant
  to Shield and Circuit Breaker controls; SAFE2 has not validated it."
- **Prohibited overclaim:** "ContractWarden is AISM Level 4" or "SAFE2-certified."
- **Next tests:** Independent side-effect observation, supported IPC propagation,
  direct bypass, outage, revocation, and legitimate-task utility.
- **Review trigger:** Pinned implementation, raw results, material version change,
  new bypass, or independent evaluation. Withdraw any claim whose support expires.

## Delivery backlog and ownership

The methodology, reusable card, validation guide, incident guide, navigation,
and discovery pointers are provided as v1.0 assessment methods.
Runtime integrations and live experiments remain proposed work:

| Work | Proposed owner role, to be assigned | Completion evidence |
|---|---|---|
| Complete artifact-specific cards | Research assessor | Pinned versions, per-claim sources/ratings, boundaries, reviewed mappings |
| Composed-service and process-mimicking experiments | Challenge maintainer | Separate preregistration, isolated harness, clean/attacked results, utility, bypasses |
| Kernel/runtime/authorization candidate validation | Runtime security owner | Supported-platform matrix, side-effect tests, fail-mode results, independent review |
| Learned-policy integrity experiment | Policy and memory owner | Poisoning/conflict tests, approved changes, provenance, rollback receipts |
| Incident retention/notification tabletop | Incident lead and legal owner | Reconstruction, custodian/hold decisions, approved notification trail, regression owner |
| TCP machine schema/CLI and presentation | CLI and dashboard maintainers | Versioned contract, separation from current grades, negative tests, migration and UI review |

No owner is assigned by implication. No candidate has been installed, executed,
certified, or granted production authority by this documentation change.

---

[Technology Profile](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Validation](../docs/TECHNOLOGY-VALIDATION.md) | [Incident Evidence](../docs/INCIDENT-EVIDENCE.md) | [Repository coverage review](../docs/TECHNOLOGY-PROFILE-REPO-REVIEW.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
