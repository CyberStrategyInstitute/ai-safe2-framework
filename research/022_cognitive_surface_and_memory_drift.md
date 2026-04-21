# Research Note 1: Cognitive Surface and Memory Drift in Agentic AI Systems

**Series:** AI SAFE2 v3.0 Research Foundation  
**Topic:** Grounding the `cognitive_surface` and `memory_persistence` Incident Tags  
**Controls Supported:** S1.5, S1.6, M4.4, M4.6, CP.1, CP.2  
**Date:** April 2026 

---

## 1. Purpose

This research note grounds the two cross-pillar incident tagging requirements introduced in CP.1 (Agent Failure Mode Taxonomy) of AI SAFE2 v3.0:

- `cognitive_surface = (model | memory | both)` — indicates whether a failure rooted in model behavior, persistent memory state, or the interaction between both
- `memory_persistence = (session | cross_session)` — indicates whether the effect was limited to a single session or persisted across sessions and users

These are not metadata additions. They encode a structural distinction that changes incident response, root cause analysis, control prioritization, and long-term threat modeling.

---

## 2. The Cognitive Surface Distinction

### 2.1 What "Cognitive Surface" Means

An agentic AI system has two distinct sites where adversarial influence can land:

**The model surface**: The transformer weights and inference-time reasoning process. An attack at this surface succeeds if the model is induced to reason incorrectly or produce harmful output *given its current input context*. The effect is limited to the inference turn — when the input changes, the behavior changes.

**The memory surface**: The persistent storage layer — vector databases, episodic memory, procedural memory caches, retrieval corpora, and any state carried across sessions. An attack at this surface does not need to subvert the model's reasoning in real time. It only needs to persist adversarial content into the memory layer; the model then faithfully executes against that content on future turns, often behaving exactly as designed.

**The combined surface**: The most dangerous category. Attacks that exploit the interaction between model and memory — conditioning the model's reasoning through gradual memory corruption, using model-generated outputs to contaminate future memory retrievals, or using memory state to reinforce model-level behavioral drift over time.

### 2.2 Why This Distinction Matters for Incident Response

A production incident where an agent returns a harmful response has different root causes and different response procedures depending on which surface was attacked:

| Cognitive Surface | Root Cause Category | Response Procedure | Scope of Impact |
|---|---|---|---|
| `model` | Prompt injection, jailbreak, reasoning manipulation | Revoke session; analyze prompt; update detection signatures | Single session; no persistence |
| `memory` | RAG poisoning, memory injection, episodic corruption | Quarantine agent; audit memory state; rollback to known-good snapshot; scan for affected content | All future sessions retrieving affected content |
| `both` | Slow-drift attack; conditioning campaign | Full memory audit; model behavior baseline comparison; multi-session forensics | Potentially cross-user; requires broadest scope investigation |

Without this tag, an organization responding to a `memory` or `both` incident using `model`-scope procedures will terminate the immediate session while leaving the root cause active in persistent memory — resulting in recurrence.

### 2.3 Research Foundation

The cognitive surface distinction is grounded in three research lineages:

**AgentPoison (July 2025)**: Demonstrated persistent trigger injection into RAG memory that caused sleeper-agent behaviors across future sessions. Critically, standard prompt-layer defenses did not detect AgentPoison because the injection surface was the memory layer, not the prompt. This is the canonical `memory` surface attack.

**MINJA (August 2025)**: Memory injection attack against LLM agents showing that content persisted in episodic memory can override explicit user instructions in future sessions. Demonstrated `both` surface dynamics — the injected memory conditioned model behavior in ways the model could not distinguish from legitimate user preferences.

**PajaMAS (September 2025)**: Multi-agent memory laundering — one agent contaminates its memory, a second agent retrieves from that memory, and the second agent's contamination is attributed to a different source than the original. Classic `both` surface attack with cross-agent propagation.

---

## 3. The Memory Persistence Dimension

### 3.1 Session vs. Cross-Session Persistence

`memory_persistence` captures a separate dimension from cognitive surface: temporal scope.

**Session persistence**: The adversarial effect is active only within a single agent session. When the session ends, the effect ends. This is characteristic of classic context-window attacks: jailbreaks, role-play conditioning, and multi-turn conversation manipulation where the attacker must be actively present.

**Cross-session persistence**: The adversarial effect survives session termination and affects subsequent sessions — potentially other users' sessions in multi-tenant environments. This is characteristic of memory-layer attacks, RAG corpus contamination, procedural memory poisoning, and episodic memory injection.

### 3.2 Cross-Session Impact Categories

Cross-session attacks have four distinct impact patterns:

1. **Single-user continuation**: Affected memory is partitioned to one user; only that user's future sessions are affected (low blast radius)
2. **Multi-user shared corpus**: Affected content is in a shared RAG corpus or knowledge base; all users whose queries retrieve the affected content are exposed (high blast radius)
3. **Swarm propagation**: Affected memory is in an agent's state that is consulted by other agents; contamination propagates through the multi-agent network
4. **Model fine-tuning loop contamination**: In systems where agent outputs feed back into model fine-tuning or RLHF pipelines, cross-session contamination can escalate to the model surface, converting a `memory` attack into a `both` attack over time

### 3.3 Control Mapping by Tag Combination

| cognitive_surface | memory_persistence | Primary Controls | Response Priority |
|---|---|---|---|
| `model` | `session` | P1.T1.2, S1.6 | Standard incident response |
| `model` | `cross_session` | M4.4, M4.6, M4.7 | Elevated; audit trigger history |
| `memory` | `session` | S1.5, A2.6 | Medium; audit write event |
| `memory` | `cross_session` | S1.5, F3.4, A2.5, A2.6 | High; full memory forensics + rollback |
| `both` | `session` | S1.5, S1.6, M4.4 | High; full incident scope analysis |
| `both` | `cross_session` | All memory + model controls; CP.8 CRT evaluation | Critical; evaluate against Catastrophic Risk Thresholds |

---

## 4. Drift: When Memory and Model Interact Over Time

The most difficult operational challenge is detecting drift — the gradual, non-discrete degradation of agent behavior that arises from the accumulation of small memory contaminations over time.

### 4.1 Types of Drift

**Retrieval drift**: RAG corpus content changes gradually (document reorganization, document updates, new content additions) causing retrieval rankings to shift, causing agent responses to degrade. Not adversarial, but indistinguishable in effect from adversarial RAG poisoning. Addressed by A2.6 (RAG Corpus Diff Tracking) and F3.4 (Behavioral Drift Baseline and Rollback).

**Episodic memory drift**: An agent with persistent memory accumulates conversational context that gradually shifts its behavioral baseline — either through adversarial multi-turn conditioning or through a large volume of low-quality interactions. Addressed by S1.5 (Memory Governance Boundary Controls) and M4.6 (Emergent Behavior Anomaly Detection).

**Belief drift (cognitive surface)**: The model's effective beliefs — as expressed in its reasoning chains — shift over time because the retrieved context it consistently receives has drifted. The model is not compromised, but it is reasoning faithfully against contaminated context. This is the canonical `both` / `cross_session` scenario.

### 4.2 Detecting Drift vs. Attack

Three detection indicators help distinguish adversarial attack from benign drift:

1. **Temporal profile**: Adversarial attacks have deliberate temporal profiles (see Research Note 2). Benign drift has a smooth, gradual profile without inflection points.
2. **Semantic coherence**: Adversarial memory injection tends to insert semantically anomalous content relative to surrounding corpus content. Benign drift produces semantically coherent degradation.
3. **Query specificity**: Adversarial injection often targets specific query patterns that activate the injected content. Benign drift affects a broad cross-section of queries.

---

## 5. Control Implications

### 5.1 Controls Directly Grounded in This Research

**S1.5 — Memory Governance Boundary Controls**: The memory write policy requirement exists specifically to prevent cross-session contamination before it enters persistent state. The tier classification (ephemeral/session/persistent) maps directly to the `memory_persistence` tag values.

**S1.6 — Cognitive Injection Sanitization Layer**: The few-shot conditioning detection requirement addresses the multi-turn build-up that leads to `model` surface compromise and, in sustained campaigns, `both` surface compromise.

**M4.4 — Adversarial Behavior Detection Pipeline**: Must be designed to detect adversarial signals at both the model and memory surface — requiring different detection methodologies (prompt analysis vs. retrieval content analysis).

**M4.6 — Emergent Behavior Anomaly Detection**: The behavioral drift baseline requirement is the primary control for detecting `both` / `cross_session` scenarios before they escalate to incident status.

**CP.1 — Agent Failure Mode Taxonomy**: The `cognitive_surface` and `memory_persistence` tags are mandatory on every agentic incident precisely because the response procedure depends critically on these values.

**CP.2 — Adversarial ML Threat Model Integration**: The temporal tagging requirement (`temporal_profile`) is a companion to `cognitive_surface` — together they describe what was attacked and when.

### 5.2 Organizational Procedures Implied

Organizations implementing these controls should:

1. Update their incident response runbooks to branch on `cognitive_surface` at triage time — before any other investigation step
2. Maintain memory rollback snapshots at a cadence that makes `memory` / `cross_session` rollback feasible (daily minimum for ACT-3+ agents with high-sensitivity memory)
3. Conduct quarterly `memory` / `cross_session` red-team exercises specifically, not only standard prompt injection testing
4. Audit their detection coverage: most detection pipelines have strong `model` / `session` coverage and weak `memory` / `cross_session` coverage

---

## 6. References

- AgentPoison: Memory Poisoning Attack Against LLM Agents (July 2025). Mapped to MITRE ATLAS AML.T0000.001.
- MINJA: Memory Injection Attack Against LLM Agents (August 2025).
- PajaMAS: Multi-Agent Memory Laundering Attack Pattern (September 2025).
- OWASP AIVSS v0.8, Risk #6: Agent Memory and Context Manipulation.
- OWASP AIVSS v0.8, Risk #9: Agent Untraceability.
- MITRE ATLAS (October 2025), Memory tactic additions.
- CSA Zero Trust for LLMs (micro-segmentation per agent session).
- AI SAFE2 v3.0 Framework, Sections CP.1, S1.5, S1.6, M4.4, M4.6.

---

*This research note is part of the AI SAFE2 v3.0 research foundation series. All content is derived exclusively from the source frameworks reviewed for v3.0. Cyber Strategy Institute, 2026.*
