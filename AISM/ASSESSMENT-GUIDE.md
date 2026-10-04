# AISM assessment guide: maturity, contribution, and evidence

### Choose the right instrument and use its results together

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Layer](https://img.shields.io/badge/Layer-AISM-820F1A?style=flat-square)](./README.md)
[![Status](https://img.shields.io/badge/Status-Methods_v1.0-808080?style=flat-square)](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](./README.md) | [NEXUS](../NEXUS/README.md)

**Documentation updated:** 2026-10-02. This guide clarifies the existing
organizational score and explains two v1.0 companion methods. It does
not change organizational scoring formulas or implement new CLI commands.

## What changed

The October 2026 documentation update separates three questions that should be
answered independently. The Sovereignty Score already existed. The Technology
Contribution Profile (TCP) and Evidence Assurance Level are v1.0 additions,
supported by a reusable Technology Card, validation guidance, and review examples.

| Instrument | What it assesses | When to use it | Method and record |
|---|---|---|---|
| AISM Sovereignty Score | Organizational maturity across five pillars and six dimensions | Baseline governance, prioritize organizational improvements, and reassess progress | [Scoring methodology](./AISM-Scoring-Matrix-Methodology.md), [self-assessment](./AISM-Self-Assessment-Tool.md) |
| AISM Technology Contribution Profile, v1.0 | What an exact product, technique, paper, or other artifact contributes to specific controls in a stated boundary | Review candidates, compare control fit, or define adoption conditions | [TCP method and contribution rubric](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md), [Technology Card](../docs/templates/TECHNOLOGY-CARD.md) |
| AI SAFE² Evidence Assurance Level, v1.0 | How strongly each claimed contribution has been demonstrated | Judge whether evidence supports a claim and identify the next validation step | [Evidence Assurance rubric](../docs/EVIDENCE-ASSURANCE.md), the card's claim and control register |

The Technology Card is the record used for TCP and assurance review, not a fourth
score. It is also distinct from the executable
[AISM Decision Card](../examples/aism-decision-card/README.md).

## How to use the three instruments

1. **Establish the organizational baseline.** Use the self-assessment and scoring
   methodology to assess the organization's actual deployed governance. Identify
   weak cells and their required controls. Preserve missing evidence as unknown.
2. **Define a technology review.** Copy the Technology Card for one artifact,
   exact version, assessor, date, and deployment or test boundary. Name the
   required canonical controls, enforcement planes, and excluded paths.
3. **Record contribution.** For each claim, distinguish addresses, implements,
   enforces, validates, evidences, and challenges. Use the TCP contribution rubric
   for each supported pillar entry. Record coverage, denominator, gaps, and the
   evidence that supports the contribution. Use `not_assessed` for unreviewed
   entries; a maximum contribution does not describe complete pillar coverage.
4. **Review assurance claim by claim.** Trace the exact claim to dated, versioned
   artifacts. Apply the Evidence Assurance rubric and separately record
   origin, independence, failures, and limits. A source being public does not
   establish independent validation. Leave unknown claims unrated with a reason.
5. **Make an adoption decision.** Use the
   [TCP adoption rule](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md#purchasing-and-adoption-rule)
   to name an owner, complementary controls, acceptance tests, residual risk,
   and reassessment triggers. A completed card does not authorize deployment.
6. **Reassess organizational maturity after deployment.** Evidence from an adopted
   technology may support specific organizational cells once local coverage,
   robustness, and sovereignty assurance have been assessed. Retain separate
   TCP, assurance, and organizational records. Do not transfer a product score
   directly into the organizational score.

## Worked example: a proposed tool-call authorization gate

This is an illustrative review scenario, not a measured product result or a
validated implementation. For a source-attributed design review, see the
[bounded ContractWarden card](../research/technology-contribution-examples.md#worked-bounded-card-contractwarden-design-review).

Suppose an organization identifies a gap in permission enforcement for one
agent-to-tool path and considers a gate that checks each call against policy.

| Review step | What the assessor records | Permitted conclusion |
|---|---|---|
| Organizational baseline | Existing organizational evidence and the affected assessment cells | There is a governance gap; buying a gate does not resolve it by itself |
| TCP | Exact gate version, control IDs, interception point, policy ownership, coverage, bypass paths, outage behavior, and evidence | A design can describe a contribution; runtime enforcement requires supporting implementation and tests |
| Evidence Assurance | A reviewable design only, under the v1.0 rubric | E1 supports the design claim; it does not establish effective runtime blocking |
| Acceptance work | Positive and negative cases, unauthorized side effects, bypasses, revocation, restart, and legitimate task completion | A later E3 assessment requires a defined harness, reviewable results, and a bounded claim |
| Organizational reassessment | Local deployment, measured coverage, operators' retained authority, and complementary controls | Reassess only the cells supported by the organization's actual evidence |

See the [validation guide](../docs/TECHNOLOGY-VALIDATION.md) for test planning and
the [incident evidence guide](../docs/INCIDENT-EVIDENCE.md) for failures and
reconstruction. Neither guide claims these tests have been performed.

## Read and report the result

Report the organizational result with its methodology, scope, date, and assessor.
Report technology contribution with its version, mapped claims, per-pillar
coverage, evidence, and limits. Report assurance for each claim with the named
**AI SAFE² Evidence Assurance v1.0** rubric and independent-review attribution.

Do not multiply contribution by assurance, average technology scores into an
organizational score, or treat assurance as certification. E5 operational
evidence does not automatically establish E4 independent validation.

The organizational methodology's **Sovereignty Assurance** metric, current CLI
E0-E5 numeric `grade` fields, claim-level **Evidence Assurance**, and
Challenge Lab C0-C5 have different meanings. The new methods change no CLI grade
weights, verification caps, schemas, or previous results. There is no implemented
TCP command or dashboard view. Use the Markdown card for this workflow.

## Methodology and research status

A separate research note is optional for announcing these documentation changes.
The linked methods already provide the rubrics, scope, and limitations.
A future research note could explain the design rationale, alternatives, and
validation plan. It should distinguish hypotheses from observed results and
link the exact assessed revision. A completed study needs its own method,
evidence, and review; publication alone does not validate these instruments.

---

[AISM Home](./README.md) | [Technology Profile](../docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Evidence Assurance](../docs/EVIDENCE-ASSURANCE.md) | [Technology Card](../docs/templates/TECHNOLOGY-CARD.md) | [Nine review examples](../research/technology-contribution-examples.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
