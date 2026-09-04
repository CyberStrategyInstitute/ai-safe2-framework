# Unbiased AI Standard Regulatory Profile: Normative Text

**AI SAFE² Cross-Pillar Governance OS | UAS v1.0 | July 2026 | Cyber Strategy Institute**

## Preamble

This Standard provides normative requirements for demonstrating implementation of "Unbiased AI Principles" as defined in GSAR 552.239-7001 paragraph (j)(1) and equivalent AI governance obligations. It is technology neutral, applies to any LLM or AI system processing Government Data, and produces documented, inspectable evidence of due diligence.

The Standard operates at two layers simultaneously. System layer: what the AI system does or does not do (AI SAFE² P1 through P5 plus NEXUS). Human layer: what the AI system does to the human operating it (CSF Domains 1 through 6). Neither alone is sufficient.

## Section 1: Scope and Applicability

1.1 This Standard applies to any LLM or AI system that: (a) processes Government Data as defined in GSAR 552.239-7001 (b); (b) is deployed under a government-wide contract vehicle or equivalent; (c) involves human operators who receive AI outputs as inputs to government decisions.

1.2 This Standard supplements, and does not replace, GSAR 552.239-7001 and NIST AI RMF 1.0. Where this Standard exceeds minimum clause requirements, the higher standard governs.

1.3 Testing frequency obligations in Section 5 scale with ACT Capability Tier as defined in CP.3.

## Section 2: Normative Definitions

**Unbiased AI**: an AI system and its operational deployment that, taken together: (a) generates outputs with factual accuracy proportionate to available evidence; (b) does not systematically favor any political, ideological, commercial, or personal interest; (c) does not employ techniques that impair the cognitive autonomy, emotional sovereignty, or independent judgment of human operators.

**Bias**: any systematic deviation from factual accuracy, ideological neutrality, or cognitive non-interference, whether originating in training data, fine-tuning, RAG corpus composition, system prompt design, interaction pattern effects, or adversarial manipulation.

**Cognitive Sovereignty**: the human operator's capacity to maintain autonomous reasoning, emotional independence, and value-coherent decision-making free from AI-induced manipulation or dependency (ref: CSF, Domains 1 through 6).

**Due-Diligence Evidence Package**: the documented showing defined in Section 6 that a contractor has implemented applicable UAS controls and conducted Section 5 testing.

## Section 3: System-Layer Requirements

### 3.1 Truthfulness (UAS-B1, B5, B7; maps to (j)(1)(i))
The AI system SHALL:
(a) attribute factual claims to verifiable sources when operating in RAG or retrieval mode [UAS-S1];
(b) maintain tested accuracy against verified fact corpora, updated no less than quarterly [UAS-S13];
(c) demonstrate adversarial framing resistance via red-team scenario testing [UAS-S5];
(d) provide SHA-verified model lineage from base training through all fine-tuning stages, consuming CP.8 artifacts [UAS-S8].

### 3.2 Neutrality (UAS-B2, B4, B6; maps to (j)(1)(ii))
The AI system SHALL:
(a) pass political neutrality probe testing with a neutral classification rate of 85 percent or higher, inter-rater reliability Cohen's kappa 0.7 or higher [UAS-S2];
(b) demonstrate statistically equivalent response quality across matched political framings (p > 0.05) [UAS-S9];
(c) maintain audit trails of model routing decisions with rationale [UAS-S6];
(d) detect and flag emotional priming patterns in multi-turn interactions [UAS-S11];
(e) maintain cross-session influence tracking via NEXUS memory governance [UAS-S14].

### 3.3 Non-Partisan Integrity (UAS-B3; maps to (j)(1)(ii) and (f)(7)(ix))
The AI system SHALL:
(a) implement commercial interest filtering preventing sponsored or vendor-favorable content from influencing factual outputs [UAS-S3];
(b) maintain behavioral drift baselines with automated rollback when drift exceeds defined thresholds [UAS-S4];
(c) audit RAG retrieval corpus for representativeness and commercial skew no less than quarterly [UAS-S7];
(d) maintain system prompt immutability controls resistant to injection-based neutrality compromise [UAS-S10];
(e) demonstrate authority simulation resistance against social engineering probes [UAS-S12].

Jurisdictional-grounding concepts are future-profile work and are not normative UAS v1.0 requirements. See `proposals/uas-s15-jurisdictional-grounding.md`.

## Section 4: Human-Layer Requirements

### 4.1 Cognitive autonomy preservation
Operators SHALL have access to: (a) CTSS (Cognitive Threat Severity Score) assessments for their operational AI environment [UAS-H1]; (b) documented AI dependency induction markers and threshold alerts [UAS-H5]; (c) decision autonomy metrics demonstrating override rates within healthy operational ranges [UAS-H8, integrates CP.9].

### 4.2 Emotional and social sovereignty
AI systems SHALL NOT: (a) employ interaction patterns that systematically alter operator emotional state toward compliance or agreement [UAS-H2]; (b) simulate social pressure, group consensus, or authority signals to influence operator judgment [UAS-H3]; (c) engage in persona blurring or role-boundary erosion [UAS-H7].

### 4.3 Value alignment integrity
Operators SHALL maintain: (a) value coherence scoring baselines established at contract commencement [UAS-H4]; (b) attention capture metric monitoring for AI interaction sessions [UAS-H6].

## Section 5: Testing Requirements

| Test | Frequency | ACT-1/2 | ACT-3/4 | Trigger events |
|---|---|---|---|---|
| Factual accuracy corpus | Quarterly | Yes | Yes | Major model version change |
| Political neutrality probe | Quarterly | Yes | Yes | Any system prompt change |
| Demographic parity | Semi-annual | No | Yes | Fine-tuning, RAG corpus change |
| Red-team scenario catalog | Annual | Yes | Yes | Significant capability change |
| Cognitive dependency (CTSS) | Semi-annual | No | Yes | Sustained deployment over 6 months |
| RAG corpus bias audit | Quarterly | Yes | Yes | New corpus sources added |
| Cross-session influence audit | Quarterly | No | Yes | Any NEXUS memory governance event |

Full methodology and pass thresholds: `testing/bias-test-protocol.md`.

5.2 Independence. Tests SHALL be conducted or reviewed by personnel with no financial interest in the AI system's commercial success. Review by a body meeting Section 8 qualification criteria satisfies this requirement.

5.3 Retention. Test results SHALL be retained for contract duration plus 3 years and be producible to the Contracting Officer within 72 hours of request. Test records are CP.4 governed artifacts.

## Section 6: Due-Diligence Evidence Package

| Doc ID | Description | Responsible party |
|---|---|---|
| UAS-ATTEST-001 | 27-control implementation evidence matrix | Prime contractor |
| UAS-TEST-001 | Bias test results per Section 5 | Developer / Integrator |
| UAS-SCORE-001 | CTSS-adapted bias scoring report | Operator |
| UAS-HUMAN-001 | Operator cognitive sovereignty assessment (CSF D6 checklist) | Operator |
| UAS-CHANGE-001 | Change notification trigger log, GSAR (i) linkage via CP.10 | Prime contractor |

The package SHALL be updated within 30 days of any Material Change as defined in GSAR 552.239-7001 (b), and is automatically triggered by CP.10 HEAR events via UAS-X5. This package constitutes documented evidence of due diligence for purposes of GSAR 552.239-7001 (d)(3) and the disclosure obligations at (f)(7)(viii) and (f)(7)(ix). It does not by itself constitute regulatory recognition or a presumption of compliance; recognition criteria are a matter for the cognizant agency.

## Section 7: NIST AI RMF Mapping

| NIST function | UAS controls | Artifact |
|---|---|---|
| GOVERN | UAS-X4, UAS-X5, CP.4 governance | UAS-ATTEST-001 |
| MAP | UAS-B taxonomy, UAS-H taxonomy | taxonomy/ |
| MEASURE | Section 5 testing, CTSS scoring | UAS-SCORE-001, UAS-TEST-001 |
| MANAGE | Evidence package, UAS-X2 escalation to CP.6 | UAS-CHANGE-001 |

## Section 8: Independent Review

8.1 Where an agency proposes adverse action for non-compliance with unbiased AI principles, sound acquisition practice supports independent technical review before suspension or termination for cause.

8.2 A qualified independent evaluation body is one that: (a) demonstrates technical AI evaluation capability, including benchmark administration and statistical scoring; (b) holds no financial interest in the AI system under review or its competitors' selection; (c) publishes its evaluation methodology; (d) operates under documented conflict-of-interest controls.

8.3 Bodies capable of meeting these criteria may include the NIST National Cybersecurity Center of Excellence, qualified public-private evaluation programs (for example, IT-AAC's Tech Proving Ground), federally funded research and development centers, or mutually agreed third-party technical panels. The criteria, not any named body, are normative.

8.4 Due process baseline: the agency should provide the specific benchmark results forming the basis of adverse action, under appropriate confidentiality protections, no less than 30 calendar days before implementing suspension, consistent with GSAR 552.239-7001 (j)(3)(ii)(B).

---
*UAS regulatory profile v1.0 | Cross-references: GSAR 552.239-7001 | NIST AI RMF 1.0 | CSF v1.0 | OMB M-25-21*
