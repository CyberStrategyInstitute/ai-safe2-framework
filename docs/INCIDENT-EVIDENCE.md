# Incident evidence and accountability review
### Reconstruct activity, preserve evidence, and assign follow-up authority

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Guide](https://img.shields.io/badge/Guide-Incident_Evidence-820F1A?style=flat-square)](./INCIDENT-EVIDENCE.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Technology Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md)

---

## Evidence workflow

This proposed assessment guidance strengthens review of logging, traceability,
incident response, oversight, and learning under existing controls. It does not
add statutory deadlines, determine legal liability, or establish that a notified
organization was breached. The named legal/incident owner determines applicable
retention, legal hold, privacy, and external notification obligations.

1. **Reconstruct:** Preserve system/version identity, trusted request and approvals,
   grants/delegation, tool calls and arguments, policy decisions, side effects,
   shutdown events, timestamps, and external observations. Identify collection gaps.
2. **Identify affected parties:** Separate attempted access, public retrieval,
   suspected impact, and confirmed unauthorized state changes. Retain evidence
   for each classification and mark unknown target impact explicitly.
3. **Preserve:** Assign a custodian, restricted access, retention schedule,
   integrity/provenance records, and a documented hold decision. Minimize sensitive
   data and retain originals safely; do not confuse a digest with authenticated truth.
4. **Notify through the owner:** Record recipients, basis, facts/uncertainties,
   approval, channel, timestamp, correction, and receipt where appropriate.
   A report or repository recommendation is not authorization to contact anyone.
5. **Learn and recover:** Connect the finding to controls, containment/recovery,
   policy changes, and an isolated regression test with an owner and review date.

## Control pointers

| Purpose | Existing control references | Repository guidance |
|---|---|---|
| Reconstruction | P2.T3.1 Real-Time Activity Logging; P2.T3.7 Decision Traceability | [Ledger](../02-audit-inventory/README.md) |
| Containment and response | P3.T5.1 Circuit Breakers; P3.T5.2 Emergency Shutdown; P3.T5.10 Incident Response | [Circuit Breaker](../03-fail-safe-recovery/README.md) |
| Detection and records | P4.T8.2 Anomaly Detection; P4.T8.3 Security Logging | [Command Center](../04-engage-monitor/README.md) |
| Learning | P5.T9.1 Threat Intel Integration; P5.T9.2 Playbook Updates; CP.6 AI Incident Feedback Loop Integration | [Learning Engine](../05-evolve-educate/README.md), [Cross-Pillar Governance](../00-cross-pillar/README.md) |
| Decision authority | CP.10 HEAR Doctrine (Human Ethical Agent of Record) | [HEAR doctrine](../research/015_hear_doctrine_human_ethical_agent_of_record.md) |

Use the [Technology Card](./templates/TECHNOLOGY-CARD.md) to distinguish an incident
source that `evidences` or `challenges` a control from a product that `enforces` it.
Accountability events belong in governance/lifecycle review; they cannot be credited
as technical validation. The [example backlog](../research/technology-contribution-examples.md)
preserves source limitations and pending verification for the supplied events.

---

[Evidence Assurance](./EVIDENCE-ASSURANCE.md) | [Validation](./TECHNOLOGY-VALIDATION.md) | [Security Policy](../SECURITY.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
