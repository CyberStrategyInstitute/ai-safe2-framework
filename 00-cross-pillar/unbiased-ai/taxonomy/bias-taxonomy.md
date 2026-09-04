# UAS Bias Taxonomy v1.0
**7 bias classes | UAS regulatory profile v1.0**

Each class maps to an AI SAFE² source, a CSF domain, and a GSAR 552.239-7001 (j)(1) trigger.

## UAS-B1: Factual Distortion
Systematic deviation from verifiable facts, including omission of contradictory evidence, selective citation, and false precision in uncertainty claims.
Source: P5 eval gates, P2 lineage | CSF: Domain 2 Cognitive | Trigger: (j)(1)(i) Truthfulness
Detection: UAS-S1, UAS-S13 | Risk: Critical. Directly degrades government decision quality.

## UAS-B2: Political/Ideological Framing
Systematic tendency to frame neutral topics through a consistent political or ideological lens regardless of prompt framing.
Source: P4 monitoring, P5 eval gates | CSF: Domain 4 Social | Trigger: (j)(1)(ii) Neutrality
Detection: UAS-S2, UAS-S9 | Risk: High. Mission neutrality and procurement integrity.

## UAS-B3: Commercial Interest Skew
Systematic favoring of products, services, or vendors in which the developer, operator, or integrator holds a financial interest.
Source: P2 audit trail, P1 isolation | CSF: Domain 5 Purpose-Moral | Trigger: (j)(1)(ii), (f)(7)(ix)
Detection: UAS-S3, UAS-S7 | Risk: High. Procurement integrity; potential False Claims Act exposure.

## UAS-B4: Emotional Manipulation
Affective language, urgency framing, fear or reward appeals, or simulated empathy used to move operator emotional state toward compliance with AI recommendations.
Source: P1 isolation, P4 monitoring | CSF: Domain 3 Emotional | Trigger: (j)(1)(ii)
Detection: UAS-S11, UAS-H2 | Risk: High. Operator autonomy degradation under sustained deployment.

## UAS-B5: Training Data Contamination
Bias introduced through unrepresentative, skewed, or commercially curated training data that shifts outputs without visible prompt influence.
Source: CP.8 model lineage, P2 | CSF: Domain 6 Digital-AI Symbiosis | Trigger: (j)(1)(i)
Detection: UAS-S8, UAS-S7 | Risk: Critical. Invisible without supply chain audit.

## UAS-B6: Cognitive Dependency Induction
Interaction patterns that, over repeated use, reduce operator independent judgment, increase AI deference, and create functional dependency impairing mission decision-making.
Source: NEXUS memory governance, CP.9 | CSF: Domain 6, Domain 2 | Trigger: (j)(1)(ii), long-horizon operator effect
Detection: UAS-H5, UAS-S14, UAS-H8 | Risk: High. Latent; emerges after roughly 6 months of sustained deployment.

## UAS-B7: Adversarial Prompt Steering
Vulnerability to adversarial inputs (injection, jailbreaks, multi-turn conditioning) that cause biased outputs contrary to the system's stated neutrality posture.
Source: CP.2 adversarial ML model, P1 fuzzing | CSF: Domain 2 | Trigger: (j)(1)(i)
Detection: UAS-S5, UAS-S10, UAS-S12 | Risk: Critical. Actively exploitable; nation-state vector against government systems.

UAS-B8 and UAS-S15 are reserved identifiers for possible future-profile work; neither is part of UAS v1.0. See `../proposals/uas-s15-jurisdictional-grounding.md`.

## Scope note applicable to all classes
UAS bias classes and controls apply to the Government-configured deployment of the LLM System, meaning the instance, configuration, and environment through which Government Data is processed under the contract. Nothing in this taxonomy governs, measures, or conditions compliance on the content of a contractor's commercial, consumer, or non-Government offerings. This scope limit is deliberate: the Government as purchaser may specify what it buys; conditions that reach a contractor's speech or products outside the funded program exceed the procurement power (ref: Agency for Int'l Development v. Alliance for Open Society Int'l, 570 U.S. 205 (2013)).
