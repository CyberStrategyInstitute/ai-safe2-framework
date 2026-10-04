# Technology validation and adoption tests
### Test effects at the boundary where they can occur

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Guide](https://img.shields.io/badge/Guide-Technology_Validation-820F1A?style=flat-square)](./TECHNOLOGY-VALIDATION.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Challenge Lab](../challenges/README.md)

---

## Scope

These acceptance practices support the [Technology Contribution Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md).
They add review guidance, not a new runnable challenge. Frozen Challenge 001,
its preregistration, and its executable fixtures remain unchanged. New experiments
need a separately owned, versioned plan before confirmatory results are promoted.

Pin the artifact and full system identity. State the prohibited effect, required
control, authority boundary, benign task, baseline, outcomes, exclusions, and
invalidation criteria before running tests. Use isolated local substitutes for
public services and synthetic data; this guide does not authorize live exploitation.

## Required test families

| Family | Test design | Acceptance evidence |
|---|---|---|
| Clean/attacked pair | Run the same task/data with and without a specified attack; fix conditions and disclose seeds/model variability | Legitimate utility and attack outcome measured separately |
| Process-mimicking injection | Inject misleading approval, audit, procedure, or board-review artifacts into untrusted inputs | Provenance and trusted approvals survive forged process evidence |
| Composed capabilities | Combine individually permitted fetch, remote-render, archive, notification, and tool paths using local stubs | Prohibited end-to-end effect remains blocked or the uncovered path is reported |
| Direct side effects | Exercise file, network, subprocess/descendant, credential, and delegated paths inside the claimed boundary | An external observer records actual state; model refusals are insufficient |
| Failure and bypass | Exercise outage, timeout, malformed authorization, replay, restart, stale grant, direct path, and revoked authority | Failure behavior and recovery match the declared policy |
| Learned-policy integrity | Attempt policy-memory poisoning, malicious lesson extraction, conflicting rules, and unauthorized updates | Source attribution, human approval, conflict handling, integrity checks, and rollback |
| Evidence survival | Attempt permitted test deletion/corruption of records and predictable audit schedules | Protected records remain reconstructable; audit predictability is disclosed |

Evaluate deterministic interception, probabilistic judgment, and actuation separately.
Record unauthorized-effect rate, detection/containment time, false blocks,
legitimate-task completion, latency/cost, denominators, confidence method where
appropriate, and all failed or excluded runs. Do not invent a performance threshold;
the decision owner sets the acceptance criteria for the deployment.

## Evidence promotion

An external benchmark is a candidate until its exact version, license, method,
threat model, and results are reviewed. Translation into a SAFE2 evidence bundle
does not reproduce execution. A paired benchmark validates its tested decisions;
it does not enforce production actions or prove continuous organizational governance.

Apply [Evidence Assurance v1.0](./EVIDENCE-ASSURANCE.md) claim by claim. Independent
validation identifies the evaluator, relationship, artifacts, material result,
and deviations. Operational evidence states the deployment population and period,
including failures and incident handling. Record Challenge Lab maturity separately.

Every accepted incident or bypass becomes a versioned regression candidate with
an owner and safe reproduction boundary. Use the
[nine-example backlog](../research/technology-contribution-examples.md) to select
work; no test family here is claimed as executed by this documentation change.

---

[Technology Card](./templates/TECHNOLOGY-CARD.md) | [Incident Evidence](./INCIDENT-EVIDENCE.md) | [Challenge CLI](./CHALLENGE-CLI.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
