# AISM Technology Contribution Profile
### Assess a technology's contribution without assigning it organizational maturity

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Method](https://img.shields.io/badge/Method-AISM_TCP-820F1A?style=flat-square)](./TECHNOLOGY-CONTRIBUTION-PROFILE.md)
[![Status](https://img.shields.io/badge/Status-Proposed_v1.0-808080?style=flat-square)](../EVOLUTION.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Research](../research/README.md) | [Challenge Lab](../challenges/README.md)

---

## Purpose and status

An organization earns an AISM maturity level. A product, paper, benchmark,
investigation, or technique contributes evidence toward specific controls.
The organizational model's full name is **AI Sovereign Maturity (AISM) Model**.
This proposed v1.0 review instrument, AISM-TCP, separates that contribution from
organization-wide scoring. It is documentation guidance pending governance
review, not a certification, implemented CLI feature, or new framework control.

The primary reader is the security leader deciding which control gap to address.
The new decision is whether a candidate supplies the needed mechanism and evidence,
not whether its vendor has the highest aggregate score. This extends existing
runtime-control and research guidance with a scoped adoption method.

| Instrument | Subject | Result | Does not establish |
|---|---|---|---|
| [AISM Sovereignty Score](../AISM/AISM-Scoring-Matrix-Methodology.md) | Organization across five pillars and six dimensions | Maturity using coverage, robustness, and sovereignty assurance | Product certification or framework conformance |
| AISM Technology Contribution Profile, proposed v1.0 | Exact artifact and deployment/test boundary | Control effects, pillar contribution, coverage, limitations | Vendor or adopting organization maturity |
| [AI SAFE² Evidence Assurance Level, proposed v1.0](./EVIDENCE-ASSURANCE.md) | Each attributed claim and supporting artifacts | E0 through E5 under the named assurance rubric | Control completeness, independence by default, or universal prevention |

Report all three independently. Do not multiply contribution by assurance, average
pillars to rank purchases, or substitute the maximum pillar contribution for an
organizational level. Existing assessment formulas, 161 core controls, profile
counts, and component versions remain unchanged.

## Assessment workflow

1. Identify artifact type, owner, exact version/commit, assessment date, assessor,
   source artifacts, and whether evidence is self-reported or independently reviewed.
2. Define the [complete agent system](./SYSTEM-IDENTITY.md) and
   [assessment scope](./ASSESSMENT-SCOPE.md): model, harness, tools, skills, memory,
   policy, credentials, OS/kernel, infrastructure, and external services.
3. Select actual required controls from the [core dataset](../skills/mcp/data/ai-safe2-controls-v3.0.json)
   and applicable profiles. Record canonical ID, name, document, and version.
   Declare north-south, east-west, and agent-to-tool scope separately.
4. Classify the effect of each claim. Link artifacts and the assurance rating to
   that claim, not to the artifact's reputation or the vendor's whole portfolio.
5. Record contribution, control coverage, failure behavior, bypasses, and gaps.
   Separate demonstrated, author-reported, intended, contradicted, and unknown facts.
6. Choose an adoption decision with a named owner, complementary controls,
   acceptance tests, residual risk, and a review trigger.
7. Publish a [Technology Card](./templates/TECHNOLOGY-CARD.md) and preserve the
   source/version trail. Reassess after changes to any component or dependency.

## Contribution rubric

Each pillar entry contains a score and status, specific mapped claims, coverage,
evidence references, and reasoning. Scores describe the highest demonstrated
capability **within that stated boundary**; they do not imply pillar-wide coverage.

| Score | Contribution | Required demonstration |
|---:|---|---|
| 0 | None | Reviewed artifact has no material relationship to this pillar |
| 1 | Conceptual | Identifies a risk, principle, or proposed approach |
| 2 | Visibility | Produces inventory, telemetry, analysis, or threat evidence |
| 3 | Governance | Supplies repeatable policy, procedure, assessment, or validation |
| 4 | Control | Enforces or verifies a runtime control with measured outcomes |
| 5 | Sovereignty | Demonstrates continuous adaptation, formal verification of critical behavior within scope, and durable evidence while retaining organizational authority |

The names parallel the [maturity ladder](../AISM/maturity-model.md), but contribution
1 means Conceptual, not organizational Level 1 Chaos. Use `contribution 4`, not
`AISM Level 4`, for technology results.

Use `not_assessed` with no numeric score when evidence is missing. Use
`not_applicable` with a reviewed reason when the pillar is outside the review's
purpose. Neither state is 0. Scores 4 and 5 require reviewable measured results
under [assurance v1.0](./EVIDENCE-ASSURANCE.md), at least E3 for the claimed behavior;
E4 and E5 cannot be inferred from the contribution score. A paper's proposed
runtime architecture alone supports a design claim, not demonstrated contribution 4.

For contribution 5, provide repeated challenge/update history, the formal property
and its proof boundary, protected evidence retention, named change/stopping
authority, and inspect/configure/revoke/replace/export capability. Continuous
benchmarking alone or an adaptive model alone is insufficient. A verifier may
support contribution 4 without preventing an action itself; its effect remains
`validates`, and an enforcement partner must be identified.

## Control effects and coverage

| Effect | Meaning | Required distinction |
|---|---|---|
| Addresses | Relevant to the control | Relevance is not implementation |
| Implements | Contains a functioning mechanism | Source availability alone does not prove operation |
| Enforces | Prevents or terminates the prohibited effect within scope | Identify interception point, decision mechanism, actuator, and bypass paths |
| Validates | Tests another control's operation | A test is not the enforcement mechanism |
| Evidences | Produces records of operation or failure | Logging does not establish prevention |
| Challenges | Shows an assumption or control is insufficient | A finding is not a containment product |

Multiple effects are allowed when each is supported separately. Coverage is
`full`, `partial`, `none`, `unknown`, or `not_applicable` for the **named control and
boundary**, with an explicit denominator where quantified. One enforced path does
not cover other tools, kernels, cloud APIs, descendants, delegated agents, or planes.
Keep required-control applicability distinct from artifact relevance.

Record deterministic interception, probabilistic authorization judgment, and
deterministic actuation separately. A model-based ALLOW/DENY decision does not
become deterministic merely because its result is enforced outside the agent.
Identify failure on timeout, malformed output, policy unavailability, revocation,
restart, and enforcement outage. Do not infer fail-closed behavior from normal tests.

## Validation and incident evidence

Apply the [validation guidance](./TECHNOLOGY-VALIDATION.md) before claiming measured
runtime control. Use clean/attacked pairs, independent observation of side effects,
direct and composed bypasses, outage cases, and legitimate-task utility measures.
Keep [Challenge Lab C0-C5](../challenges/README.md#claim-maturity) distinct from
assurance E0-E5 and contribution 0-5. There is no automatic conversion among them.

Incident sources may challenge a control or drive governance improvements. Preserve
activity reconstruction, affected-party identification, retention/hold decisions,
notification ownership, and regression tests through the
[incident evidence workflow](./INCIDENT-EVIDENCE.md). A notification or investigative
subpoena does not prove a breach, misconduct, or control effectiveness.

## Purchasing and adoption rule

Evaluate candidates in this order, preserving unknowns as decision conditions:

1. **Required-control fit:** Which actual gap is covered, and how much?
2. **Enforcement location:** Is the boundary outside the governed component's authority?
3. **Evidence strength:** Which named claims are designed, implemented, tested,
   independently reproduced, or observed in representative operation?
4. **Failure behavior:** Does the mechanism fail closed, fail safe, or disappear?
5. **Sovereignty:** Can the organization inspect, configure, revoke, replace, and
   export evidence without vendor permission?
6. **Residual risk:** Which attack paths and dependencies remain uncovered?
7. **Integration value:** Which other pillars improve, and which new dependencies appear?

A narrow point solution may be the right choice. An unknown prerequisite or
critical uncovered path can block adoption regardless of its maximum contribution.
Record the resulting decision as adopt, pilot, hold, or reject, with conditions,
decision owner, review date, and withdrawal/rollback plan.

## Permitted claims and examples

Permitted after supporting tests: "This version supplies contribution 4 evidence
for the named Shield and Circuit Breaker controls within the tested Linux boundary."
Include the assurance rubric, assessor, test artifacts, date, coverage, and limits.

Prohibited: "ContractWarden is AISM Level 4," "DGF-Bench proves Level 5 governance,"
"open source means independently validated," or "a passing vendor test establishes
our organization's maturity."

The [nine-example review and adoption backlog](../research/technology-contribution-examples.md)
uses the supplied recommendations to frame acceptance work. Those examples are
source-attributed candidates, not scored certifications or completed integrations.

## Compatibility and implementation boundary

The CLI already uses `E0` through `E5` as numeric weights in
[`aism-model-v1.json`](../safe2/data/aism-model-v1.json). Its evidence summary also
applies verification caps and category completeness. Assurance v1.0 is a separate
claim-level rubric; it does not redefine those weights or the existing `grade`
field. Do not put a Technology Card or its contribution into an assessment cell.

Existing `safe2 aism ingest` imports attributed evidence with cells unscored for
review. Assessors still supply organization-specific coverage, robustness, and
sovereignty assurance under the current methodology. A future TCP schema, command,
adapter, dashboard view, or grade translation requires a separate versioned contract,
explicit migration policy, and tests. This proposal delivers the review method and
documentation, not those runtime features.

---

[Technology Card](./templates/TECHNOLOGY-CARD.md) | [Evidence Assurance](./EVIDENCE-ASSURANCE.md) | [Validation](./TECHNOLOGY-VALIDATION.md) | [Examples](../research/technology-contribution-examples.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
