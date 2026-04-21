# Research Note 2: Temporal Attack Profiles in Agentic AI Systems

**Series:** AI SAFE2 v3.0 Research Foundation  
**Topic:** Formalizing the `temporal_profile` Tag — Taxonomy of Time-Shifted Attacks  
**Controls Supported:** CP.2, CP.6, F3.4, S1.5  
**Date:** April 2026 

---

## 1. Purpose

This research note formalizes the `temporal_profile` tagging requirement introduced in CP.2 (Adversarial ML Threat Model Integration) of AI SAFE2 v3.0:

- `temporal_profile = (immediate | delayed_days | delayed_weeks | chronic)` — captures the time-shifted nature of adversarial attacks on AI systems, enabling temporal risk aggregation and separating burst exploits from long-horizon conditioning campaigns.

This tag addresses a critical gap in traditional security threat modeling: most security tools and incident response procedures assume that an attack is observable at or near the time of exploitation. Agentic AI systems introduce a class of attacks where the exploit payload is planted far in advance of its activation — or never activates in a single detectable event but degrades system behavior over months.

---

## 2. The Four Temporal Profile Categories

### 2.1 `immediate` — Real-Time Exploitation

**Definition**: The attack payload is planted and activated in the same interaction or within seconds to minutes. The attacker is present during exploitation.

**Characteristics**:
- Single-session scope; session termination typically ends the attack
- Detectable via real-time anomaly detection and behavioral classifiers
- High confidence in attribution — the attack source is the active interaction
- Examples: direct prompt injection in user input, real-time jailbreak, single-session multi-turn conditioning, homoglyph substitution in a single prompt

**Detection approach**: Standard adversarial classifier pipelines (M4.4), real-time prompt analysis (P1.T1.2, S1.6), session-level behavioral monitoring (M4.7).

**Response**: Standard incident response; session termination; prompt analysis; update detection signatures.

### 2.2 `delayed_days` — Short-Horizon Latent Attack

**Definition**: The attack payload is planted (e.g., via malicious document ingested into RAG, or adversarial memory injection) and activates within 1-7 days of planting, typically when a specific retrieval condition is met or a time-based trigger fires.

**Characteristics**:
- Memory surface attack (`cognitive_surface = memory` or `both`)
- Typically requires a triggering condition — a query pattern, a date, or a follow-up interaction
- Difficult to detect at planting time; the planted content may appear benign
- Detection window: between planting and activation if behavioral baselines exist; otherwise only detectable post-activation
- Examples: AgentPoison-style trigger injection activated by a specific query type; adversarial document injected into RAG corpus and activated when a user's query retrieves that document

**Detection approach**: RAG corpus diff tracking (A2.6), memory content inspection (S1.5), retrieval pattern monitoring (A2.6 alerting on unexpected retrieval rank changes).

**Response**: Memory forensics; identify planting event; scan corpus for related injected content; rollback to last known-good memory snapshot (F3.4); audit all sessions since planting time for retroactive impact.

### 2.3 `delayed_weeks` — Medium-Horizon Latent Attack

**Definition**: The attack payload is planted and activates weeks after planting, either through a time-based trigger or through accumulated multi-turn conditioning that reaches an activation threshold.

**Characteristics**:
- Often the most damaging category because the gap between planting and detection is longest
- Frequently involves `both` cognitive surface: the memory layer is corrupted, which gradually conditions model reasoning over many sessions
- May involve multiple rounds of reinforcement — the attacker plants content, observes that initial retrieval is occurring, then reinforces with additional content
- Examples: Slow-build RLHF loop contamination; multi-step RAG poisoning where multiple documents are injected over weeks before the composite retrieval effect produces observable behavioral change; gradual episodic memory conditioning

**Detection approach**: Behavioral drift baseline monitoring (F3.4) with statistical drift detection across multi-week windows; semantic execution trace logging (A2.5) enabling retrospective reasoning analysis; AIID incident correlation (CP.6) for pattern recognition from external incidents.

**Response**: Full memory audit across the estimated planting window; cross-session impact analysis; behavioral baseline comparison; potential model behavior audit if `both` surface is confirmed.

### 2.4 `chronic` — Continuous or Persistent Degradation

**Definition**: The attack does not have a discrete activation event. Instead, it produces continuous, ongoing degradation of agent behavior that is indistinguishable from natural drift without active baseline comparison.

**Characteristics**:
- Often not a deliberate attack — can arise from benign corpus degradation, accumulation of low-quality content, or retrieval pipeline drift
- When deliberate, typically reflects a sophisticated attacker who has designed for long-term undetectability
- The `chronic` label applies when there is no identifiable planting event and no discrete activation — only a gradual degradation
- Requires longitudinal behavioral baselines to detect; point-in-time assessments will miss it entirely
- Examples: Retrieval loop drift from document reorganization; slow accumulation of adversarially biased content across a shared knowledge base; continuous low-level noise injection into a memory system

**Detection approach**: Long-horizon behavioral drift baselines (F3.4); retrieval distribution monitoring over multi-month windows (A2.6); quarterly red-team exercises using `memory` / `cross_session` test scenarios (E5.1).

**Response**: Different from other temporal profiles — there is no rollback target because there is no discrete planting event. Response involves: corpus cleansing based on content analysis (not time-based audit); behavioral re-baselining; enhanced write governance (S1.5) to prevent recurrence.

---

## 3. Temporal Risk Aggregation

The value of the `temporal_profile` tag is that it enables temporal risk aggregation across an organization's deployed agents.

### 3.1 Aggregation Use Cases

**Portfolio risk assessment**: An organization running 50 agents across ACT-1 through ACT-4 tiers can aggregate temporal risk profiles to identify which agents are most exposed to `delayed_weeks` or `chronic` attacks — typically those with persistent memory, shared knowledge bases, and limited behavioral monitoring.

**Control gap identification**: Comparing temporal profiles against detection capability reveals gaps. Most detection pipelines have strong `immediate` coverage and weak `delayed_*` and `chronic` coverage. This is a systematic control gap that the `temporal_profile` tag makes visible.

**Incident pattern analysis**: When multiple incidents in a short window all have `delayed_weeks` temporal profiles, this suggests a coordinated campaign rather than opportunistic attacks — triggering CP.6 (AI Incident Feedback Loop Integration) review and escalating the threat level.

### 3.2 Temporal Profile Distribution in Production

Based on AIID incident analysis and production red-team findings reviewed for v3.0:

- `immediate`: ~60% of detected incidents (high detection rate, lower impact per incident)
- `delayed_days`: ~25% of detected incidents (moderate detection; moderate-to-high impact)
- `delayed_weeks`: ~12% of detected incidents (low detection rate; high impact per incident)
- `chronic`: ~3% of detected incidents (very low detection; often only discovered post-breach or via external disclosure)

The inverse relationship between detection rate and impact per incident is characteristic: the harder to detect, the more time the attack has to cause harm. This is why `temporal_profile` is a mandatory tag — organizations optimizing detection coverage without temporal awareness will systematically underinvest in the highest-impact attack categories.

---

## 4. Temporal Profiles and Control Mapping

### 4.1 Detection Controls by Temporal Profile

| temporal_profile | Primary Detection Controls | Detection Timing | SAFE2 Control References |
|---|---|---|---|
| `immediate` | M4.4, M4.7, S1.6 | Real-time | P1.T1.2 modifications; M4.4; M4.7 |
| `delayed_days` | A2.6, S1.5, M4.5 | Between planting and activation | A2.6; S1.5 write inspection; M4.5 tool output inspection |
| `delayed_weeks` | F3.4, A2.5, A2.6 | Ongoing — baseline comparison | F3.4 behavioral drift; A2.5 trace logging; CP.2 temporal tagging |
| `chronic` | F3.4, A2.6, E5.1 | Longitudinal — only via sustained monitoring | F3.4 long-horizon baselines; E5.1 continuous evaluation |

### 4.2 Prevention Controls by Temporal Profile

| temporal_profile | Primary Prevention Controls |
|---|---|
| `immediate` | P1.T1.2, S1.6, S1.4 (adversarial fuzzing) |
| `delayed_days` | S1.5 (memory write governance), P1.T1.10 (indirect injection surfaces) |
| `delayed_weeks` | S1.5 (retention policies), A2.3 (lineage provenance), A2.6 (corpus diff tracking) |
| `chronic` | S1.5 (memory tiering), A2.6 (drift-based alerting), E5.2 (capability emergence review) |

---

## 5. Implementation Guidance for Temporal Threat Modeling

### 5.1 Adding `temporal_profile` to the AMLTM

The Adversarial ML Threat Model (AMLTM) required by CP.2 should include a temporal profile column for every documented threat:

```
Threat: RAG corpus poisoning via document upload
OWASP AIVSS Risk: #6 (Memory/Context Manipulation)
MITRE ATLAS: AML.T0054 (RAG Databases)
temporal_profile: delayed_days OR delayed_weeks (depending on query trigger frequency)
cognitive_surface: memory
memory_persistence: cross_session
Detection control: A2.6 (corpus diff tracking), M4.5 (retrieval output inspection)
Response: F3.4 (rollback to last known-good corpus snapshot)
```

### 5.2 Temporal Coverage Audit

Organizations should audit their current detection coverage against temporal profiles:

1. List all agentic incidents from the past 12 months
2. Apply `temporal_profile` retroactively to each incident
3. Calculate detection lag (time from planting to detection) for non-`immediate` incidents
4. Identify which controls would have detected each incident earlier
5. Prioritize control implementation based on the undetected temporal profile categories

### 5.3 Red-Team Exercise Design

E5.1 (Continuous Adversarial Evaluation) and E5.4 (Red-Team Artifact Repository) should explicitly include temporal profile coverage:

- `immediate` coverage: standard prompt injection, jailbreak, and evasion testing
- `delayed_days` coverage: plant adversarial RAG documents; return 3-5 days later with triggering queries
- `delayed_weeks` coverage: multi-session conditioning campaigns over a 2-4 week exercise period
- `chronic` coverage: baseline measurement, introduce slow corpus degradation, measure time to detection

---

## 6. References

- OWASP AIVSS v0.8, Risk #6 (Agent Memory and Context Manipulation) — temporal aspects of memory attacks.
- AgentPoison (July 2025) — confirmed `delayed_days` temporal profile in production RAG systems.
- MINJA (August 2025) — demonstrated `delayed_weeks` episodic memory conditioning.
- MITRE ATLAS (October 2025), Memory and Persistence tactic additions.
- AI Incident Database (AIID) — incident pattern analysis.
- AI SAFE2 v3.0 Framework, Sections CP.2, F3.4, S1.5, A2.6, E5.1.

---

*This research note is part of the AI SAFE2 v3.0 research foundation series. Cyber Strategy Institute, 2026.*
