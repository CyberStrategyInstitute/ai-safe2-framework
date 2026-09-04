# Unbiased AI Standard (UAS) Regulatory Profile
### Cross-pillar compliance overlay for truthfulness, neutrality, and continuous improvement

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Profile](https://img.shields.io/badge/Profile-UAS_1.0-820F1A?style=flat-square)](./STANDARD.md)
[![Status](https://img.shields.io/badge/Status-Compliance_Overlay-808080?style=flat-square)](../README.md)

[Framework Home](../../README.md) | [Cross-Pillar Governance](../README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Position in AI SAFE² v3.1

UAS is maintained as an explicitly identified **regulatory profile extension**. It composes and tests controls drawn from AI SAFE², NEXUS, and the Cognitive Sovereignty Framework (CSF) against Unbiased AI procurement and due-diligence requirements.

It is **not** counted as 27 new independent controls added to the 161-control AI SAFE² core taxonomy. The module's 27 requirements are an overlay/control-composition surface.

This distinction keeps the framework count coherent:

- AI SAFE² v3.1 core framework: **161 controls**;
- core Cross-Pillar Governance: **CP.1 through CP.10**;
- CP.5.MCP profile: **MCP-1 through MCP-19**;
- UAS regulatory profile: **27 profile requirements composed from mapped controls**.

AI SAFE² remains 161 controls and CP.1 through CP.10. UAS does not create a
new core control or extend the Cross-Pillar control range.

---

## Why This Module Exists

The UAS module was created to provide an inspectable way to evaluate truthfulness, neutrality, and continuous-improvement obligations in federal AI procurement contexts, including the GSAR 552.239-7001 Unbiased AI requirements that motivated the module.

The module addresses a recurring implementation gap: policy language can define an obligation without specifying how a contractor should measure, test, evidence, challenge, and attest to that obligation.

UAS provides a technical and governance structure for doing that work.

UAS does not claim government recognition or legal safe harbor. Applicability and contractual interpretation remain the responsibility of the relevant parties and counsel.

---

## Why Cross-Pillar, Not a Sixth Pillar

UAS is a governance output layer rather than a new operational security domain. Existing AI SAFE² pillars already provide the technical controls that support the overlay.

| Source | Contribution to UAS |
|---|---|
| **P1 Sanitize & Isolate** | Semantic isolation, manipulation resistance, trusted/untrusted boundary controls |
| **P2 Audit & Inventory** | Corpus/model provenance, evidence, source attribution, change tracking |
| **P3 Fail-Safe & Recovery** | Drift thresholds, rollback, suspension and recovery |
| **P4 Engage & Monitor** | Behavioral telemetry, anomaly detection, human intervention |
| **P5 Evolve & Educate** | Evaluation gates, testing cadence, reusable findings |
| **Cross-Pillar Governance** | ACT tier, control plane, incident feedback, HEAR, evidence governance |
| **NEXUS** | Reference implementation for identity, delegation, memory governance, receipts |
| **CSF** | Human-layer influence and cognitive-sovereignty controls |

---

## The Dual-Layer Model

A technically neutral system can still influence or degrade the human operating it. A protected operator cannot compensate for a technically biased or manipulated system.

UAS therefore combines:

- **System layer:** 14 requirements, UAS-S1 through UAS-S14;
- **Human layer:** 8 requirements, UAS-H1 through UAS-H8;
- **Bridge layer:** 5 requirements, UAS-X1 through UAS-X5.

Total: **27 overlay requirements**.

Normative text: [STANDARD.md](./STANDARD.md)

---

## Bias Taxonomy

| ID | Bias class | Primary governance source | Human-layer connection |
|---|---|---|---|
| UAS-B1 | Factual Distortion | Evaluation and evidence controls | Cognitive accuracy |
| UAS-B2 | Political/Ideological Framing | Monitoring and decision traceability | Social influence |
| UAS-B3 | Commercial Interest Skew | Audit trail and conflict disclosure | Purpose and decision agency |
| UAS-B4 | Emotional Manipulation | Semantic isolation and interaction controls | Emotional autonomy |
| UAS-B5 | Training/Data Contamination | Model/data lineage and provenance | Digital/AI symbiosis |
| UAS-B6 | Cognitive Dependency Induction | Memory and interaction governance | Digital/AI symbiosis |
| UAS-B7 | Adversarial Prompt Steering | Threat modeling and input governance | Cognitive integrity |

Full taxonomy: [taxonomy/bias-taxonomy.md](./taxonomy/bias-taxonomy.md)

---

## Module Structure

```text
00-cross-pillar/unbiased-ai/
├── README.md
├── STANDARD.md
├── taxonomy/
│   └── bias-taxonomy.md
├── controls/
│   ├── uas-controls-system.md
│   ├── uas-controls-human.md
│   └── uas-controls-crossdomain.md
├── testing/
│   └── bias-test-protocol.md
├── compliance/
│   ├── gsar-552-239-7001-mapping.md
│   └── due-diligence-attestation.md
└── examples/
    └── vendor-attestation-sample.md
```

---

## Relationship to Core Cross-Pillar Controls

| Core control | UAS interaction |
|---|---|
| **CP.1** | Classifies relevant AI failure modes and evidence context |
| **CP.2** | Supplies adversarial manipulation and temporal threat analysis |
| **CP.3** | Scales testing/governance by ACT tier |
| **CP.4** | Governs ownership, authorization, decision rights, and evidence |
| **CP.6** | Feeds material findings into incident/control improvement |
| **CP.8** | Defines emergency suspension thresholds where consequences warrant |
| **CP.9** | Governs delegated/replicated agents that may inherit behavior or policy |
| **CP.10** | Connects high-consequence human authority and stop decisions |

UAS references those controls. It does not replace or renumber them.

---

## Federal Procurement Use

A UAS evidence package can help a contractor or agency document how it evaluated applicable truthfulness, neutrality, testing, and disclosure obligations.

A complete assessment should identify:

- the system/model/version evaluated;
- applicable UAS requirements;
- test methodology and thresholds;
- source and corpus provenance;
- material findings and remediation;
- independent-review status where used;
- limitations and unresolved questions;
- signed attestation artifacts where contractually required.

The standard is designed to be independently inspectable and comparable if an agency later publishes formal recognition or equivalency criteria.

---

## Companion Framework: CSF

UAS is the explicit bridge between AI system governance and human cognitive-sovereignty concerns.

AI SAFE² governs the system and its authority. CSF addresses the human operator's capacity to remain capable of governing that system. UAS evaluates obligations that can span both layers.

---

## Start Here

1. [Read the normative UAS standard](./STANDARD.md).
2. [Review the bias taxonomy](./taxonomy/bias-taxonomy.md).
3. [Review system controls](./controls/uas-controls-system.md).
4. [Review human-layer controls](./controls/uas-controls-human.md).
5. [Run the testing protocol](./testing/bias-test-protocol.md).
6. [Review the procurement mapping](./compliance/gsar-552-239-7001-mapping.md).
7. [Prepare the due-diligence attestation](./compliance/due-diligence-attestation.md).

---

## 🔗 Navigation

[Framework Home](../../README.md) | [Cross-Pillar Governance](../README.md) | [UAS Standard](./STANDARD.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 · UAS 1.0 regulatory profile extension · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
