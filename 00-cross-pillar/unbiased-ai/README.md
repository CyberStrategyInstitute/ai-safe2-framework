# CP.11: Unbiased AI Standard (UAS)

**Cross-Pillar Governance Module | AI SAFE² v3.0+ | Cyber Strategy Institute | July 2026**
**Dual license: MIT (code, tooling, templates) + CC-BY-SA 4.0 (normative text, taxonomy, documentation)**

UAS operates as CP.11 in the Cross-Pillar Governance OS, alongside CP.1 through CP.10. Like all CP controls, UAS does not belong to any single pillar. It synthesizes outputs across all five pillars, NEXUS, and the Cognitive Sovereignty Framework (CSF) into a single, auditable compliance surface for "Unbiased AI" obligations in federal procurement, specifically GSAR 552.239-7001 paragraph (j)(1).

## Why this module exists

GSA's draft GSAR clause 552.239-7001 (j)(1) makes three "Unbiased AI Principles" contractually enforceable for any LLM processing Government Data:

1. **Truthfulness**: factual accuracy, historical accuracy, acknowledgment of uncertainty
2. **Neutrality**: no manipulation of responses in favor of ideological dogmas, no intentionally embedded partisan judgment via training data, fine-tuning, RAG, or system prompts
3. **Continuous improvement**: ongoing detection and mitigation of bias and trustworthiness failures

The clause attaches suspension rights and decommissioning cost liability to these principles, and provides no test method, no threshold, no measurement standard, and no independent review mechanism. That is a governance vacuum. UAS fills it with an open, inspectable, quantified standard that any contractor, agency, or evaluator can apply today.

## Why cross-pillar, not a sixth pillar

UAS is a governance output layer, not a security domain. Each pillar already contributes controls that feed bias detection, manipulation resistance, and truthfulness assurance:

| Pillar | Contribution to UAS |
|---|---|
| P1 Sanitize & Isolate | Semantic isolation of adversarial framing; system prompt immutability; injection resistance |
| P2 Audit & Inventory | RAG corpus provenance; model lineage; cross-session influence tracking; source attribution |
| P3 Fail-Safe & Recovery | Behavioral drift baselines; automated rollback on threshold breach; change notification triggers |
| P4 Engage & Monitor | Emotional priming detection; adversarial behavioral telemetry; routing decision audit |
| P5 Evolve & Educate | Evaluation gates on model updates; demographic parity testing; red-team artifact repository |
| NEXUS | Memory governance; non-repudiable audit chain; cryptographic agent identity |
| CSF (companion) | Human-layer influence controls (UAS-H series), Domains 1 through 6 |

## The dual-layer model

Neither layer alone is sufficient. A technically neutral system can still manipulate its operator through interaction patterns. A protected operator cannot compensate for a technically biased system.

- **System layer** (14 controls, UAS-S1 to S14): what the AI system does or does not do
- **Human layer** (8 controls, UAS-H1 to H8): what the AI system does to the human operating it, sourced from CSF Domains 1 through 6
- **Bridge layer** (5 controls, UAS-X1 to X5): the interface, escalation gates, and attestation automation between the two

27 controls total. Full definitions in `controls/`. Normative requirements in `STANDARD.md`.

## The 7 bias classes

| ID | Bias class | Primary source | CSF domain | GSAR (j)(1) trigger |
|---|---|---|---|---|
| UAS-B1 | Factual Distortion | P5 eval gates | D2 Cognitive | (j)(1)(i) Truthfulness |
| UAS-B2 | Political/Ideological Framing | P4 monitoring | D4 Social | (j)(1)(ii) Neutrality |
| UAS-B3 | Commercial Interest Skew | P2 audit trail | D5 Purpose-Moral | (j)(1)(ii) Neutrality |
| UAS-B4 | Emotional Manipulation | P1 isolation | D3 Emotional | (j)(1)(ii) Neutrality |
| UAS-B5 | Training Data Contamination | CP.8 lineage | D6 Digital-AI Symbiosis | (j)(1)(i) Truthfulness |
| UAS-B6 | Cognitive Dependency Induction | NEXUS memory gov | D6 Digital-AI Symbiosis | (j)(1)(ii) Neutrality |
| UAS-B7 | Adversarial Prompt Steering | CP.2 + P1 | D2 Cognitive | (j)(1)(i) Truthfulness |

Full taxonomy with definitions, detection controls, and risk levels: `taxonomy/bias-taxonomy.md`.

## Module structure

```
00-cross-pillar/unbiased-ai/
├── README.md                          <- this file (CP.11 overview)
├── STANDARD.md                        <- normative standard, Sections 1-8
├── taxonomy/
│   └── bias-taxonomy.md               <- 7 UAS-B bias classes
├── controls/
│   ├── uas-controls-system.md         <- 14 AI SAFE² sourced controls
│   ├── uas-controls-human.md          <- 8 CSF sourced controls
│   └── uas-controls-crossdomain.md    <- 5 bridge controls
├── testing/
│   └── bias-test-protocol.md          <- 7 test types, quantified pass thresholds
├── compliance/
│   ├── gsar-552-239-7001-mapping.md   <- clause crosswalk and gap-fill table
│   └── due-diligence-attestation.md   <- prime contractor attestation template
└── examples/
    └── vendor-attestation-sample.md   <- completed reference example
```

## Relationship to existing CP controls

| CP | Interaction with CP.11 |
|---|---|
| CP.2 Adversarial ML Threat Model | Supplies adversarial bias vectors (UAS-B7) |
| CP.3 Governance Roles (ACT tiers) | Scales UAS testing frequency by autonomy tier |
| CP.4 Control Plane Governance | UAS attestation package is a CP.4 governed artifact |
| CP.6 Incident Integration | UAS-X2 escalation gate triggers CP.6 workflow |
| CP.8 Model Lineage | UAS-S8 consumes CP.8 SHA-verified lineage artifacts |
| CP.9 Delegation Bounds | UAS-H8 enforces minimum human override health |
| CP.10 HEAR Doctrine | UAS-X5 attestation triggers integrate with HEAR events |

## Federal procurement use

A contractor implementing the applicable UAS controls, running the Section 5 test protocol, and producing the five-document attestation package (Section 6) holds documented, inspectable evidence of due diligence with respect to GSAR 552.239-7001 (j)(1) and the bias testing and disclosure obligations at (f)(7)(viii) and (f)(7)(ix). UAS does not claim regulatory recognition. It is built so that if GSA publishes framework-recognition or equivalency criteria, this standard, and any other framework meeting those criteria, can be evaluated against them in the open.

Independent review: STANDARD.md Section 8 defines qualification criteria for independent evaluation bodies (technical AI evaluation capability, no financial interest in the system under review, published methodology). Bodies meeting these criteria may include NIST NCCoE, qualified public-private evaluation programs such as IT-AAC's Tech Proving Ground, or mutually agreed third parties.

## Companion framework: CSF

CP.11 is the first cross-pillar control with an explicit human-protection companion layer. CSF cross-connections:

- `cognitive-sovereignty/research/005_uas_federal_standard.md`
- `cognitive-sovereignty/06-digital-ai-symbiosis/federal-procurement-alignment.md`

AI SAFE² secures the system. CSF protects the human. CP.11 proves both.
