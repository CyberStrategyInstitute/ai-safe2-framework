# AI SAFE² Challenge Lab
### Falsification before claims

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface](https://img.shields.io/badge/Surface-Challenge_Lab-820F1A?style=flat-square)](./README.md)
[![Method](https://img.shields.io/badge/Method-Falsification--First-808080?style=flat-square)](./README.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Why This Exists

AI governance controls should not receive credit because they sound appropriate, appear in a policy, or map to a standard. They should receive credit when a reproducible implementation changes a security-relevant outcome under test.

The Challenge Lab converts incidents, evaluation findings, and credible agentic threats into open experiments. Each challenge publishes the problem, hypotheses, control claims, baselines, graders, evidence requirements, invalidation criteria, and replication path before confirmatory results are promoted.

**The framework is the subject of the test, not the source of its own proof.**

---

## Challenge Questions

Every challenge should be able to answer:

1. Did the control prevent the prohibited state change?
2. If prevention failed, did it contain the blast radius?
3. Was the event detected soon enough to matter?
4. Can an independent reviewer reconstruct what happened?
5. Can the system recover to a known-good state?
6. What legitimate work, latency, cost, and human effort did the control consume?
7. Which enforcement plane and control/profile claims were actually exercised?

---

## Challenge Index

| ID | Challenge | Primary question | Status |
|---|---|---|---|
| 001 | [Anthropic Multi-Agent Turf War](./001-anthropic-multi-agent-turf-war/) | Can externally enforced authority stop destructive multi-agent conflict without blocking legitimate collaboration? | Design and pre-registration |

---

## Claim Maturity

| Level | Status | Evidence |
|---|---|---|
| C0 | Described | Control language exists |
| C1 | Implemented | Machine-readable configuration and code exist |
| C2 | Unit verified | Positive and negative unit tests pass |
| C3 | Scenario validated | Control changes an adversarial scenario outcome |
| C4 | Bypass tested | Control survives replay, corruption, direct bypass, and fail-mode testing |
| C5 | Independently replicated | An unaffiliated operator reproduces the material result |

Only C3 and above support the phrase **validated in tested conditions**. No maturity level establishes universal prevention.

Challenge maturity is separate from framework/profile conformance. A well-designed experiment may invalidate a conformant implementation claim, and a conformant implementation may fail to outperform a simpler baseline.

---

## v3.1 Enforcement-Plane Scoping

AI SAFE² v3.1 distinguishes:

- **north-south** agent-to-model/provider enforcement;
- **east-west** agent-to-agent enforcement;
- **agent-to-tool** MCP/tool enforcement.

A challenge result must identify which plane was tested. Evidence from one plane does not automatically validate another.

---

## Required Design for Every Challenge

Every challenge includes:

- source links and threat summary;
- Rules of Engagement and safety limits;
- threat model and trust boundaries;
- preregistered hypotheses and null hypotheses;
- exact framework/profile/implementation versions;
- conventional-security and prompt-only baselines where applicable;
- AI SAFE² treatment and targeted ablations;
- deterministic state and trace graders;
- legitimate-use cases for false-block and utility measurement;
- explicit invalidation criteria;
- signed/tamper-evident evidence manifests;
- enforcement-plane designation;
- statistical analysis and disclosed exclusions;
- independent-replication path;
- limitations and claim-status report.

Material normative or grader changes after preregistration require a new preregistration version before confirmatory evidence is pooled.

---

## Result Labels

- **Validated in tested conditions**
- **Partially validated**
- **Limited to stated conditions**
- **Invalidated and revised**
- **Unresolved due to evidence limits**
- **Independently reproduced**

An invalidated claim is a useful result. It should create a control revision, permanent regression fixture, or versioned record of why the claim changed.

---

## Contributing

High-value contributions include:

- a valid bypass;
- a grader defect;
- a safer or cheaper equivalent control;
- an independent replication;
- a new scenario or failure fixture;
- a statistical or methodological correction;
- documentation that prevents misimplementation.

The most important contribution is evidence that changes what the framework can honestly claim.

---

## 🔗 Navigation

[Framework Home](../README.md) | [Challenge 001](./001-anthropic-multi-agent-turf-war/) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Contributing](../CONTRIBUTING.md) | [Security](../SECURITY.md)

---

AI SAFE² principle: **If governance is not enforced at runtime, it is not governance.**

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
