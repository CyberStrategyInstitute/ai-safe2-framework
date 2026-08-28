# AI SAFE² Challenge Lab

> Open experiments designed to validate, limit, or invalidate AI SAFE² control claims.

[Main Framework](../README.md) | [Challenge 001](./001-anthropic-multi-agent-turf-war/) | [Contributing](../CONTRIBUTING.md) | [Security](../SECURITY.md)

---

## Why this exists

AI governance controls should not receive credit because they sound appropriate, appear in a policy, or map to a standard. They should receive credit when a reproducible implementation changes a security-relevant outcome under test.

The AI SAFE² Challenge Lab converts public incidents, evaluation findings, and credible agentic threats into open-source experiments. Each challenge publishes the problem, hypotheses, control claims, baselines, graders, evidence requirements, invalidation criteria, and replication path before confirmatory results are released.

The Challenge Lab is designed to answer six questions:

1. Did the control prevent the prohibited state change?
2. If prevention failed, did it contain the blast radius?
3. Was the event detected soon enough to matter?
4. Can an independent reviewer reconstruct what happened?
5. Can the system recover to a known-good state?
6. What useful work, latency, cost, and human effort did the control consume?

## Challenge index

| ID | Challenge | Primary question | Status |
|---|---|---|---|
| 001 | [Anthropic Multi-Agent Turf War](./001-anthropic-multi-agent-turf-war/) | Can externally enforced authority stop destructive multi-agent conflict without blocking legitimate collaboration? | Design and pre-registration |

[Read the Challenge 001 announcement](./001-anthropic-multi-agent-turf-war/ANNOUNCEMENT.md).

## Claim maturity

| Level | Status | Evidence |
|---|---|---|
| C0 | Described | Control language exists |
| C1 | Implemented | Machine-readable configuration and code exist |
| C2 | Unit verified | Positive and negative unit tests pass |
| C3 | Scenario validated | Control changes an adversarial scenario outcome |
| C4 | Bypass tested | Control survives replay, corruption, direct bypass, and fail-mode testing |
| C5 | Independently replicated | An unaffiliated operator reproduces the material result |

Only C3 and above support the phrase **validated in tested conditions**. No maturity level establishes universal prevention.

## Required design for every challenge

Every challenge must include:

- primary and secondary source links;
- a concise incident or threat summary;
- Rules of Engagement and safety limits;
- threat model and trust boundaries;
- pre-registered hypotheses and null hypotheses;
- prompt-only and conventional-security baselines where applicable;
- AI SAFE² treatment and targeted ablations;
- deterministic state and trace graders;
- legitimate-use cases to measure false blocks and utility;
- explicit invalidation criteria;
- signed or tamper-evident evidence manifests;
- statistical analysis and disclosed exclusions;
- an independent-replication path;
- a limitations and claim-status report.

## Result labels

- **Validated in tested conditions**
- **Partially validated**
- **Limited to stated conditions**
- **Invalidated and revised**
- **Unresolved due to evidence limits**
- **Independently reproduced**

An invalidated claim is a useful result. It should generate a control revision, a permanent regression fixture, and a versioned record of what changed.

## Contributing

High-value contributions include:

- a valid bypass;
- a grader defect;
- a safer or cheaper equivalent control;
- an independent replication;
- a new scenario or failure fixture;
- a statistical or methodological correction;
- documentation that prevents misimplementation.

The most important contribution is not confirmation. It is evidence that changes what the framework can honestly claim.

---

AI SAFE² principle: **If governance is not enforced at runtime, it is not governance.**
