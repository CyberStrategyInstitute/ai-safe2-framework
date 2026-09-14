# Agentic AI security brief: CLI implementation triage

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Decision](https://img.shields.io/badge/Decision-Evidence_adoption_first-820F1A?style=flat-square)](./TASK-RECEIPTS.md)

[Framework Home](../README.md) | [CLI](../safe2/README.md) | [Task Receipts](./TASK-RECEIPTS.md) | [Challenge Lab](./CHALLENGE-CLI.md)

## Decision

The September 6–13 brief is an input to prioritization, not normative framework
evidence. Its strongest sources support the existing plan: make SAFE2 a portable
evidence and acceptance layer around agent harnesses. No article, survey, or
participant claim in the brief automatically changes a control, score, challenge,
or product capability.

## Ranked against the current plan

| Rank | Insight | Fit | Current action |
| ---: | --- | --- | --- |
| 1 | Declared environment differs from effective authority | Direct | Add provider-neutral harness evidence intake with explicit observed, declared, and missing coverage. Do not infer isolation from prompts or configuration. |
| 2 | Evidence searches and logs can have coverage gaps | Direct | Make collection coverage and missing sources first-class receipt fields; never translate absence into a clean result. |
| 3 | Agent telemetry cannot be the only source of truth | Direct | Preserve source attribution and support external test, tool, infrastructure, and third-party evidence without treating translation as independent reproduction. |
| 4 | Capability combinations create nonlinear risk | Near-term | Apply after reliable harness/environment inventory exists. Keep file, execution, credentials, egress, shared state, and delegation as separate observed capabilities before evaluating combinations. |
| 5 | Persistent tasks need campaign/task lineage | Near-term | Extend the existing parent-task and usage-event ownership model before adding swarm-wide decisions. |
| 6 | Persistent memory is a governed artifact | Near-term | Add memory provenance/expiry evidence through adapters after the common intake contract is stable. |
| 7 | Control confidence exceeds deployed evidence | Supporting | Use as positioning for receipts, not as a new score or universal market statistic. |
| 8 | Reproducible external benchmarks are valuable | Later validation | Evaluate as an independent fixture candidate only after legal/safety review, preregistration, benign utility criteria, and isolated execution exist. |
| 9 | Component inspection is expanding | Supporting | Continue SkillSpector and provider-neutral supply-chain evidence; do not claim external inspection quality without reproducible methodology. |

## Pinned outside the active release path

The following require separate proposals and version review. They must not delay
harness evidence adoption or silently enter AI SAFE² v3.1:

- A new Challenge 002 or changes to frozen Challenge 001.
- New or amended framework controls and control totals.
- New AISM evidence grades or maturity-scoring semantics.
- Swarm-wide circuit-breaker enforcement before trustworthy aggregate telemetry exists.
- A production persistent-memory governor.
- Reproduction of an external offensive-security benchmark.
- Claims based on vendor surveys, selected telemetry, press reports, or unverified statistics.

Pinned does not mean rejected. Each item needs an owner, threat model, evidence
contract, acceptance criteria, and release boundary before implementation.

## Active delivery sequence

1. Provider-neutral harness evidence intake and coverage gaps.
2. Opt-in Codex and Claude Code adapters using supported export/hook surfaces.
3. One human-readable finished-work card from the common evidence.
4. Task lineage, retries, time, tokens, and declared/verified usage distinctions.
5. Cross-harness comparison against the same acceptance criteria.
6. Independently observed source/environment state and isolated execution.
7. Hermes, OpenClaw, Grok, and additional adapter expansion.

## Evidence cautions from source review

Anthropic's September 9 report directly supports environment-state reconciliation:
it reports four incidents in misconfigured evaluation environments, a broadened
transcript search after an initially missed set, and continuing uncertainty about
generalization. It also states these incidents involved single model instances and
found no agent coordination. Do not use that source to substantiate swarm or covert
coordination claims.

Vendor surveys and reports can motivate evaluation questions but do not establish
the state of a particular deployment. External benchmark percentages remain the
authors' results until SAFE2 independently reproduces the exact artifacts and
conditions. Press claims require their own source and attribution review.

## Product value test

Every active addition must answer at least one immediate user question:

- What was asked, and what counts as done?
- What actually ran, changed, passed, failed, or remained unseen?
- Which source supports each conclusion?
- What did the task consume, and which values are reported, estimated, or unknown?
- What should the human or agent do next?

If a proposal cannot improve one of these answers without demanding a new runtime,
new policy regime, or large integration commitment, it remains pinned.
