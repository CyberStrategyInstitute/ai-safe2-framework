# Technology evidence request

### Collect the evidence needed to evaluate a product, solution, or technique

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Layer](https://img.shields.io/badge/Layer-AISM-820F1A?style=flat-square)](./README.md)

[AISM Home](./README.md) | [Technology Contribution Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Evidence Assurance Level](./EVIDENCE-ASSURANCE.md) | [Technology Card](./templates/TECHNOLOGY-CARD.md)

**Documentation updated:** 2026-10-13. This request supports AISM-TCP v1.0 and
AI SAFE² Evidence Assurance v1.0. Use it during procurement, a pilot, an internal
engineering review, or reassessment after a product change.

## Start a technology evaluation

1. Define the control gap, exact product or solution version, intended use, and
   deployment boundary using the [TCP assessment workflow](./TECHNOLOGY-CONTRIBUTION-PROFILE.md#assessment-workflow).
2. Copy the [Technology Card](./templates/TECHNOLOGY-CARD.md) and send the request
   below to the provider or internal owner. Ask for artifacts against each claim.
3. Review the supplied artifacts with the
   [Evidence Assurance Level rubric](./EVIDENCE-ASSURANCE.md#rubric-and-status).
   Record source, date, version, origin, independence, exclusions, and conflicts.
4. Map supported contributions to controls and pillars. Plan missing tests with
   the [validation guide](./TECHNOLOGY-VALIDATION.md), then record an adopt, pilot,
   hold, or reject decision with conditions and a named decision owner.

The output is a completed Technology Card containing a scoped contribution
profile, claim-level assurance assessments, evidence gaps, and an adoption
recommendation. It does not assign organizational maturity or authorize deployment.

## Copyable request to a provider or internal owner

> We are evaluating your product, solution, or technique using the AISM Technology
> Contribution Profile v1.0 and AI SAFE² Evidence Assurance v1.0. Please provide
> dated, versioned evidence for each claimed control contribution, scoped to the
> deployment we are considering. Identify what is unavailable, untested, or outside
> the supported boundary. Separate your own results from independent evaluations.
> Redact secrets, personal information, and customer data. For restricted material,
> identify a secure review route and access conditions rather than sharing it publicly.

Copy this table into the evaluation request. The assessor selects the actual
canonical control IDs; a provider's mapping is attributed input for review.

| Request | Evidence to supply | How the evaluator uses it |
|---|---|---|
| Identity and intended use | Product/solution name, owner, exact version or commit, deployment diagram, components and dependencies | Establish the reviewed subject, scope, and reassessment triggers |
| Claimed contribution | Exact claim, mapped control IDs/names, affected pillars, and whether the artifact addresses, implements, enforces, validates, evidences, or challenges the control | Separate capability claims from evidence and full control coverage |
| Architecture and mechanism | Design records, interception/enforcement location, trust boundaries, policy ownership, supported platforms and tool paths | Review whether the claimed mechanism covers the intended boundary |
| Implementation | Inspectable versioned implementation or controlled inspection evidence; configuration and prerequisites | Trace design claims to the actual mechanism without treating availability as effectiveness |
| Controlled tests | Harness/version, environment, method, positive and negative cases, baseline, sample sizes, denominators, reviewable outcomes and raw or redacted artifacts | Assess the bounded tested claim and identify missing validation |
| Independent evaluation | Named evaluator, relationship/conflicts, method, exact evaluated version and claims, reproduced results and limitations, or an explicit statement that none exists | Record independence separately from the assurance rating |
| Operational evidence | Deployment scope, observation period, usage denominators, failures, incidents, interventions, changes, and coverage gaps | Assess representative operation without inferring universal prevention |
| Failure and bypass behavior | Outage, timeout, restart, revocation, unsupported paths, descendants, direct bypass, rollback, and observed side effects | Evaluate fail-open, fail-closed, fail-safe, and unknown behavior |
| Retained authority and integration | Who can inspect, configure, revoke, stop, replace, and export; complementary controls, retention and incident owners; dependencies, latency, cost, and false blocks | Support adoption conditions and preserve organizational decision authority |

## Review the evidence, then rate each claim

Use the full [E0-E5 rubric](./EVIDENCE-ASSURANCE.md), not a vendor-wide rating.
A design claim and a runtime effectiveness claim may have different evidence.
Source availability does not establish independent validation. Operational
evidence at E5 does not automatically establish E4 independence.

If evidence has not been reviewed or is unavailable, record `not_assessed`, no
rating, and a reason. E0 means an observed unsupported assertion; it is not the
default for an unperformed assessment. Preserve contradictions and failed tests.
Ask for the specific missing artifact rather than rounding up a rating.

For an agent-assisted review, use this instruction:

> Review the supplied artifacts against AISM-TCP v1.0 and AI SAFE² Evidence
> Assurance v1.0. Produce a Technology Card with exact source/version references,
> scoped control effects, coverage, claim-level assurance, independent-review
> attribution, conflicts, and missing evidence. Read only the supplied material;
> request approval before accessing remote or restricted sources. Do not execute
> provider code, access credentials, overwrite existing records, deploy changes,
> contact others, or accept residual risk. Separate observed facts from assertions
> and assumptions. Report the next human decision and the evidence needed for it.

## Keep the three results separate

- **AISM Sovereignty Score:** the organization's maturity across its pillars and dimensions.
- **AISM Technology Contribution Profile:** the artifact's scoped contribution to specific controls.
- **AI SAFE² Evidence Assurance Level:** the strength of evidence for each claimed contribution.

After deployment, verified local evidence may support specific organizational
assessment cells. A product's contribution or assurance rating cannot be copied
directly into the organizational score. Current CLI E0-E5 numeric grades remain
separate from assurance v1.0; this workflow uses the Markdown Technology Card.

---

[Assessment guide](./ASSESSMENT-GUIDE.md) | [TCP method and adoption rule](./TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Evidence Assurance Level](./EVIDENCE-ASSURANCE.md) | [Validation](./TECHNOLOGY-VALIDATION.md) | [Incident evidence](./INCIDENT-EVIDENCE.md)
