
<div align="center">
  <img src="../assets/AISM Compliance Crosswalk v2.png" alt="AISM Compliance Crosswalk" width="100%" />
</div>

# AISM Scoring Matrix Methodology
## AI Sovereignty Maturity Scoring Framework for the Agentic AI Era

**Version:** 1.0  
**Date:** March 2026  
**Organization:** Cyber Strategy Institute  
**Framework:** AI SAFE2 v2.1 — AI Sovereignty Matrix (AISM)  
**Status:** Proposed Methodology

---

## 1. Purpose & Scope

This document establishes a rigorous, quantitative scoring methodology for the AI Sovereignty Matrix (AISM), enabling organizations to measure, benchmark, and advance their maturity across all five pillars of the AI SAFE2 Framework v2.1. The methodology is purpose-built for the **agentic AI era** — where autonomous multi-agent systems, non-human identities (NHI), and distributed AI architectures create governance challenges that no existing framework fully addresses.

### 1.1 Design Principles

| Principle | Description |
|---|---|
| **Sovereignty-First** | Every metric ties back to organizational control over AI systems — not mere compliance |
| **Agentic-Native** | Scoring accounts for multi-agent orchestration, swarm behaviors, and autonomous decision chains |
| **Evidence-Based** | All scores require verifiable artifacts, not self-reported assertions |
| **Multi-Dimensional** | Combines coverage, robustness, and stakeholder diversity — adapted from IEEE/NIST AI RMF maturity research |
| **Lifecycle-Aware** | Scores differentiate pre-deployment, deployment, and post-deployment maturity |

---

## 2. Evaluation of Scoring Methodology Options

Five candidate scoring approaches were evaluated against criteria critical to the agentic AI era.

### 2.1 Candidate Options

#### Option A: IEEE/NIST AI RMF Flexible Maturity Model (Dotan et al., 2024)
- **Source:** arXiv:2401.15229v1; IEEE USA ebook
- **Structure:** 1–5 scale across 3 metrics (Coverage, Robustness, Input Diversity); 9 topics / 66 statements mapped to NIST AI RMF pillars (MAP, MEASURE, MANAGE, GOVERN)
- **Scoring Rubric:** HHH=5, HHM=4, HMM/HHL/HML/MMM=3, MML/MLL/HLL=2, LLL=1
- **Strengths:** Evidence-based; flexible granularity; supports multiple maturity trajectories
- **Weaknesses:** No agentic AI controls; no NHI dimension; no supply chain model signing; no sovereignty framing

#### Option B: NIST CSF Dual-Survey Weighted Maturity (Bernardo et al., 2025)
- **Source:** Electronics 2025, 14, 1364 (attached PDF)
- **Structure:** Expert panel (1–10 importance weighting) + organizational survey (5-point Likert); weighted maturity per NIST CSF function
- **Scoring Rubric:** Maturity 0–5 scale: ≤1.99 Very Poor → 5.00 Excellent
- **Strengths:** Expert-calibrated weights; multi-audience (Board, IT, Others); cross-org benchmarking
- **Weaknesses:** Cybersecurity-only; no AI-specific controls; requires expert panel infrastructure; no agentic coverage

#### Option C: Sandia Maturity-Based Certification with Measurement Mechanisms (Darling et al., 2026)
- **Source:** arXiv:2601.03470
- **Structure:** 5-level maturity (Ad-hoc → Formal Verification); 4 measurement properties (Quantifiable, Actionable, Formal Properties, Lifecycle Integration); multi-objective optimization for trade-offs
- **Scoring Rubric:** Level-specific criteria with required evidence; UQ-based thresholds
- **Strengths:** Quantitative measurement mechanisms; formal verification at highest levels; multi-objective trade-off handling
- **Weaknesses:** Focused on embodied AI (drones/UAS); no governance/policy dimensions; research-stage only

#### Option D: CSA AI Controls Matrix (AICM) + STAR for AI (CSA, 2025)
- **Source:** Cloud Security Alliance AICM v1.0
- **Structure:** 243 control objectives across 18 security domains; AI-CAIQ questionnaire; 3-level STAR certification (Pledge → Self-Assessment → Third-Party Audit)
- **Scoring Rubric:** Binary control implementation (Y/N/Partial) with STAR levels
- **Strengths:** Comprehensive control coverage; vendor-neutral; maps to ISO 42001, NIST AI RMF; enterprise procurement ready
- **Weaknesses:** No maturity progression within controls; binary scoring lacks granularity; no sovereignty dimension; limited agentic AI depth

#### Option E: Microsoft Responsible AI Maturity Model (RAI MM, 2023)
- **Source:** Microsoft Research Whitepaper
- **Structure:** 24 dimensions across 3 categories; 5 levels (Latent → Leading); empirically derived from 90+ interviews
- **Scoring Rubric:** Dimension-by-dimension level assessment (1–5) with criteria per level
- **Strengths:** Empirically validated; rich dimension set; interdependency awareness
- **Weaknesses:** Proprietary framing; no security/safety technical controls; explicitly "not a measurement tool for punitive purposes"; no agentic, NHI, or supply chain coverage

### 2.2 Evaluation Criteria for the Agentic AI Era

| Criterion | Weight | Description |
|---|---|---|
| **Agentic AI Coverage** | 20% | Multi-agent, swarm, A2A, orchestration controls |
| **NHI & Machine Identity** | 15% | Service accounts, AI agent identities, credential lifecycle |
| **Supply Chain Integrity** | 10% | Model signing, SBOM, provenance chains |
| **Memory & Context Security** | 10% | RAG poisoning, agent memory, context injection |
| **Quantitative Rigor** | 15% | Measurable metrics, not just Y/N checklists |
| **Evidence Requirements** | 10% | Artifact-based verification, not self-assertion |
| **Enterprise Procurement** | 10% | Compliance crosswalks, audit readiness, certification path |
| **Sovereignty Alignment** | 10% | Organizational control, autonomy, self-governance of AI |

### 2.3 Comparative Scoring Matrix

| Criterion (Weight) | Option A: IEEE/NIST | Option B: NIST CSF | Option C: Sandia | Option D: CSA AICM | Option E: MS RAI MM |
|---|---|---|---|---|---|
| Agentic AI Coverage (20%) | 1 | 1 | 2 | 2 | 1 |
| NHI & Machine Identity (15%) | 1 | 1 | 1 | 2 | 1 |
| Supply Chain Integrity (10%) | 1 | 1 | 1 | 3 | 1 |
| Memory & Context Security (10%) | 1 | 1 | 1 | 2 | 1 |
| Quantitative Rigor (15%) | 4 | 4 | 5 | 2 | 3 |
| Evidence Requirements (10%) | 5 | 3 | 4 | 3 | 3 |
| Enterprise Procurement (10%) | 3 | 3 | 1 | 5 | 2 |
| Sovereignty Alignment (10%) | 2 | 1 | 2 | 2 | 1 |
| **Weighted Score** | **2.30** | **1.90** | **2.30** | **2.55** | **1.55** |

*Scale: 1 = No coverage, 2 = Minimal, 3 = Partial, 4 = Strong, 5 = Comprehensive*

### 2.4 Key Finding

**No existing approach scores above 2.55/5.00** on agentic AI era requirements. Each excels in isolated dimensions but fails holistically. This validates the need for a **composite methodology** that synthesizes the best elements:

| Inherited Element | Source |
|---|---|
| 3-metric scoring (Coverage, Robustness, Diversity) | IEEE/NIST AI RMF MM (Option A) |
| Expert-weighted importance calibration | NIST CSF Dual-Survey (Option B) |
| 5-level maturity with measurement mechanisms | Sandia Maturity Certification (Option C) |
| Control-objective taxonomy + compliance crosswalks | CSA AICM (Option D) |
| Empirically-derived dimensions + interdependency awareness | MS RAI MM (Option E) |

---

## 3. Recommended AISM Scoring Methodology

### 3.1 The AISM Composite Scoring Framework

The recommended methodology — the **AISM Sovereignty Score** — combines the strongest elements from all five approaches into a unified system purpose-built for AI SAFE2 v2.1.

### 3.2 Maturity Levels (5-Level Scale)

| Level | Name | Description | NIST Tier Equivalent |
|---|---|---|---|
| **1** | **Reactive** | Ad-hoc, no formal AI governance; controls are incident-driven | Partial |
| **2** | **Aware** | AI risks recognized; basic policies exist but inconsistently applied | Risk Informed |
| **3** | **Controlled** | Formalized controls across all 5 pillars; documented processes; regular audits | Repeatable |
| **4** | **Sovereign** | Organization has full visibility and control over AI systems; adaptive governance; proactive threat response | Adaptive |
| **5** | **Autonomous Governance** | Self-improving governance; formal verification of critical controls; continuous measurement mechanisms; AI sovereignty fully realized | Optimizing |

### 3.3 Scoring Dimensions (5 Pillars × 6 Dimensions)

Each AI SAFE2 pillar is assessed across **six scoring dimensions** — adapted from digital maturity research and agentic AI requirements:

| # | Dimension | DMM Equivalent | Agentic AI Application |
|---|---|---|---|
| **D1** | Governance Architecture | Organization (36) | AI oversight structures, board accountability, RACI for AI decisions, sovereignty posture |
| **D2** | Risk Strategy & Posture | Strategy (34) | AI risk appetite, threat modeling, sovereignty roadmap, regulatory alignment |
| **D3** | Technical Controls | Technology (28) | Agent sandboxing, NHI controls, memory security, supply chain signing, kill switches |
| **D4** | Safety Culture & Workforce | Culture (27) | AI safety training, prompt engineering education, agentic system awareness, red team culture |
| **D5** | Lifecycle Processes | Process (21) | AI system lifecycle management, change control, incident response, continuous monitoring |
| **D6** | Sovereignty Assurance | *NEW — AISM-native* | Organizational autonomy over AI, data sovereignty, model provenance, self-governance capability |

### 3.4 Three-Metric Evaluation (Per Dimension Per Pillar)

Each of the 30 assessment cells (5 pillars × 6 dimensions) is scored using three metrics, each rated **Low (L), Medium (M), or High (H)**:

#### Metric 1: Coverage
*How completely does the organization implement the relevant AI SAFE2 subtopics?*

| Rating | Criteria |
|---|---|
| **High** | ≥80% of applicable subtopics implemented with documented controls |
| **Medium** | 40–79% of applicable subtopics implemented |
| **Low** | <40% of applicable subtopics implemented |

#### Metric 2: Robustness
*How rigorous and resilient are the implemented controls?*

Assessed against six robustness ideals (adapted from NIST implementation tiers):

1. **Regular** — Controls executed routinely, not ad-hoc
2. **Systematic** — Organization-wide policies, not team-specific
3. **Trained Personnel** — Roles defined, staff certified/trained
4. **Sufficiently Resourced** — Budget, tools, compute allocated
5. **Adaptive** — Controls evolve with threat landscape; regular reviews
6. **Cross-Functional** — Involves security, engineering, legal, leadership

| Rating | Criteria |
|---|---|
| **High** | 5–6 robustness ideals satisfied |
| **Medium** | 3–4 robustness ideals satisfied |
| **Low** | 0–2 robustness ideals satisfied |

#### Metric 3: Stakeholder Diversity & Sovereignty Assurance
*How diverse are inputs and how sovereign is organizational control?*

This metric extends the IEEE model's "Input Diversity" to include sovereignty:

| Rating | Criteria |
|---|---|
| **High** | Diverse internal/external stakeholders inform controls; organization maintains full autonomous control over AI governance decisions; no single vendor lock-in |
| **Medium** | Some stakeholder diversity; partial organizational control; moderate vendor dependencies |
| **Low** | Minimal stakeholder input; governance decisions driven by single team or vendor; significant sovereignty gaps |

### 3.5 Score Calculation

#### Cell Score (1–5)

Each cell uses the HHH rubric from the IEEE/NIST AI RMF model:

| Score | Metric Combination | Point Total (L=1, M=2, H=3) |
|---|---|---|
| **5** | HHH | 9 |
| **4** | HHM | 8 |
| **3** | HMM, HHL, HML, MMM | 6–7 |
| **2** | MML, MLL, HLL | 4–5 |
| **1** | LLL | 3 |

#### Pillar Score

Each pillar score is the **weighted average** of its 6 dimension scores, with weights calibrated by expert panel (adapted from Bernardo et al. methodology):

```
Pillar Score = Σ (Dimension Score × Dimension Weight) / Σ Dimension Weights
```

Default weights (adjustable per organizational context):

| Dimension | Default Weight | Rationale |
|---|---|---|
| D1: Governance Architecture | 0.20 | Foundation — without governance, controls are ad-hoc |
| D2: Risk Strategy & Posture | 0.18 | Direction — strategy determines investment priorities |
| D3: Technical Controls | 0.25 | Execution — largest subtopic coverage in AI SAFE2 |
| D4: Safety Culture & Workforce | 0.12 | Enablement — people execute controls |
| D5: Lifecycle Processes | 0.15 | Operations — day-to-day process maturity |
| D6: Sovereignty Assurance | 0.10 | Differentiation — unique to AISM |

#### Overall AISM Sovereignty Score

```
AISM Score = Σ (Pillar Score × Pillar Weight) / Σ Pillar Weights
```

Default pillar weights (equal by default, adjustable):

| Pillar | Default Weight |
|---|---|
| P1: Sanitize / Isolate | 0.20 |
| P2: Audit / Inventory | 0.20 |
| P3: Fail-Safe / Recovery | 0.20 |
| P4: Engage / Monitor | 0.20 |
| P5: Evolve / Educate | 0.20 |

### 3.6 Combined Risk Score Integration

For organizations also tracking technical vulnerabilities, AISM integrates with CVSS (as defined in AI SAFE2 v2.1):

```
Combined Risk = CVSS Base Score × ((100 - Pillar Score as %) / 10)
```

**Example:** CVSS 8.5 (High) + AISM Pillar Score 3.8/5.0 (76%) = 8.5 × (24/10) = 20.4 → High Risk  
**Example:** CVSS 8.5 (High) + AISM Pillar Score 4.5/5.0 (90%) = 8.5 × (10/10) = 8.5 → Moderate Risk

---

## 4. AI Sovereignty Matrix Visualization

### 4.1 Sovereignty Matrix Plot

The AISM Sovereignty Score is visualized as a **radar chart** (spider diagram) with:
- **5 axes** = 5 AI SAFE2 Pillars
- **5 concentric rings** = Maturity Levels 1–5
- **Color coding** = Red (1–2), Yellow (3), Green (4–5)

Additionally, a **heatmap matrix** plots:
- **Rows** = 5 Pillars (P1–P5)
- **Columns** = 6 Dimensions (D1–D6)
- **Cell values** = Score (1–5) with color gradient

### 4.2 Maturity Classification

| AISM Score Range | Classification | Action Required |
|---|---|---|
| 4.50 – 5.00 | **Sovereign** | Maintain excellence; share best practices |
| 3.50 – 4.49 | **Controlled** | Close specific gaps; advance to sovereign |
| 2.50 – 3.49 | **Developing** | Prioritize critical pillars; formalize controls |
| 1.50 – 2.49 | **Emerging** | Establish baseline governance immediately |
| 1.00 – 1.49 | **Exposed** | Critical risk — immediate intervention required |

---

## 5. Evidence Requirements

Every score must be substantiated with verifiable evidence. The AISM requires three categories of evidence per assessment cell:

| Evidence Type | Description | Examples |
|---|---|---|
| **Documentary** | Written policies, procedures, architecture documents | AI governance policy, agent inventory, SBOM records |
| **Operational** | Logs, dashboards, audit trails demonstrating active controls | SIEM logs showing NHI monitoring, kill switch test records |
| **Attestation** | Third-party or cross-functional verification | Penetration test reports, red team findings, compliance audit results |

---

## 6. Comparison: AISM vs. Current Approaches

| Capability | AISM (Recommended) | IEEE/NIST MM | CSA AICM | MS RAI MM | NIST CSF MM |
|---|---|---|---|---|---|
| Maturity levels | 5 (Reactive→Autonomous) | 5 (1–5 scale) | 3 (STAR levels) | 5 (Latent→Leading) | 5 (Very Poor→Excellent) |
| Scoring metrics | 3 (Coverage, Robustness, Sovereignty) | 3 (Coverage, Robustness, Diversity) | Binary (Y/N/Partial) | Level criteria | Weighted surveys |
| Agentic AI controls | ✅ 35 sub-domains | ❌ None | ⚠️ Limited | ❌ None | ❌ None |
| NHI governance | ✅ 10 dedicated controls | ❌ None | ⚠️ Minimal | ❌ None | ❌ None |
| Supply chain signing | ✅ OpenSSF OMS | ❌ None | ⚠️ General | ❌ None | ❌ None |
| Memory security | ✅ 6 sub-domains | ❌ None | ❌ None | ❌ None | ❌ None |
| Sovereignty dimension | ✅ Native | ❌ None | ❌ None | ❌ None | ❌ None |
| Compliance crosswalks | ✅ 7+ frameworks | ⚠️ NIST AI RMF only | ✅ ISO 42001, NIST | ❌ None | ⚠️ NIST CSF only |
| Evidence requirements | ✅ 3 categories | ✅ Evidence-based | ⚠️ Questionnaire | ❌ Guidance only | ⚠️ Survey-based |

---

## 7. References

1. Dotan, R., Blili-Hamelin, B., Madhavan, R., Matthews, J., & Scarpino, J. (2024). "Evolving AI Risk Management: A Maturity Model based on the NIST AI Risk Management Framework." arXiv:2401.15229v1.
2. IEEE USA. (2025). "A Flexible Maturity Model for AI Governance Based on the NIST AI Risk Management Framework."
3. Bernardo, L., Malta, S., & Magalhães, J. (2025). "An Evaluation Framework for Cybersecurity Maturity Aligned with the NIST CSF." Electronics 2025, 14, 1364.
4. Darling, M.C., et al. (2026). "Toward Maturity-Based Certification of Embodied AI." arXiv:2601.03470.
5. Cloud Security Alliance. (2025). "AI Controls Matrix (AICM) v1.0." 243 control objectives, 18 security domains.
6. Vorvoreanu, M., et al. (2023). "Responsible AI Maturity Model." Microsoft Research.
7. NIST. (2025). "Cybersecurity Framework Profile for Artificial Intelligence." NIST IR 8596 iprd.
8. NIST. (2023). "AI Risk Management Framework (AI RMF 1.0)." NIST AI 100-1.
9. Peixoto, E.C., et al. (2025). "Clarifying Core Dimensions in Digital Maturity Models." arXiv:2602.07569v1.
10. Cyber Strategy Institute. (2025). "AI SAFE2 Framework Version 2.1 — Advanced Agentic Distributed AI Edition."
11. RAI Institute. (2024). "Responsible AI Maturity Model." Five stages: Aware → Transformative.
12. iQomply. (2026). "ISO 42001 Maturity Model." Five levels: Initial → Mature.

---

*© 2026 Cyber Strategy Institute. Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).*
