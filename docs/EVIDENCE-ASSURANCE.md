# AI SAFE² Evidence Assurance Level
### Attribute evidence strength to a specific claim

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Method](https://img.shields.io/badge/Method-Evidence_Assurance-820F1A?style=flat-square)](./EVIDENCE-ASSURANCE.md)
[![Status](https://img.shields.io/badge/Status-Method_v1.0-808080?style=flat-square)](./TECHNOLOGY-CONTRIBUTION-PROFILE.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Technology Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md)

---

**Method version:** 1.0

**Documentation updated:** 2026-10-02

**Status:** CSI assessment method for use and feedback

Start with the [AISM assessment guide](../AISM/ASSESSMENT-GUIDE.md) for a practical workflow.

## Rubric and status

This v1.0 evidence rubric is separate from organizational maturity,
contribution capability, framework conformance, and Challenge Lab claim maturity.
Always name it **AI SAFE² Evidence Assurance v1.0** with each E rating.

| Rating | Evidence class | Minimum record |
|---|---|---|
| E0 | Assertion | Attributed marketing or unsupported description; no supporting artifact |
| E1 | Design | Identifiable architecture, paper, or control specification supporting the design claim |
| E2 | Implemented | Inspectable implementation/released code with version and mechanism traced to the claim |
| E3 | Controlled test | Defined harness, positive and negative cases, environment, reviewable results, and explicit outcome/coverage |
| E4 | Independent validation | Named independent evaluator and reproduced/evaluated material claim, artifacts, method, and limitations |
| E5 | Operational evidence | Representative production evidence over a stated period, failures, incident handling, and coverage gaps |

Record the highest class substantiated for the **specific claim**. These classes
are not a universal quality ordering: operational evidence may be self-reported,
and a controlled test can be narrow. E5 does not imply E4 independence. Preserve
independence as a separate field. A paper can contain E3 evidence only when its
test method and material results are reviewable; publication alone supports E1.
Evidence of a failure can qualify as E3 or E5 without validating prevention.

Unknown or unreviewed evidence has `not_assessed`, no rating, and a reason. E0 is
an observed unsupported assertion, not a substitute for an unperformed review.
Different claims about the same technology may receive different ratings.

## Required provenance

For each claim retain:

- Claim ID, exact wording, canonical mapped control, and claimed effect.
- Artifact URL/path, source owner, artifact version/commit and date, and actual review date.
- Assessor, method, environment, threat model, tested plane, and boundary.
- Evidence class and origin: author-reported, reviewer-observed, or independently evaluated.
- Positive/negative results, sample size/denominator, exclusions, known failures,
  missing artifacts, contradictions, and remaining dependencies.
- Independence and any evaluator relationship/conflict, separate from the rating.
- Permitted wording, prohibited inference, expiry/review trigger, and decision owner.

Preserve superseded evidence with its status. Do not upgrade a rating because a
source is popular, open source, signed, translated into SAFE2, or vendor-published.
A digest establishes byte consistency; it does not establish truthful observation.
Generalizing from one environment requires additional evidence.

## Existing CLI grades and Challenge Lab

The current [AISM CLI model](../safe2/data/aism-model-v1.json) maps E0-E5 to numeric
weights. [`scoring.py`](../safe2/aism/scoring.py) combines those weights with
verification caps and evidence-category completeness. Those input and summary
grades are not automatically assurance-v1.0 ratings. This method changes no
weights, caps, formulas, schemas, or previously issued results.

Store assurance assessments in the separate [Technology Card](./templates/TECHNOLOGY-CARD.md).
Do not copy their ratings into existing CLI `grade` fields without a separately
reviewed translation. A derived CLI evidence-summary grade must not be relabeled
as an independently assessed assurance level.

[Challenge Lab C0-C5](../challenges/README.md#claim-maturity) describes progression
of a control claim through implementation, scenario testing, bypass testing, and
replication. Record the applicable challenge result alongside assurance, preserving
its own criteria. Neither C5 nor E4 establishes an organization's AISM Level 5.

---

[Technology Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md) | [Validation](./TECHNOLOGY-VALIDATION.md) | [Examples](../research/technology-contribution-examples.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
