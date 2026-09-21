# CP.5.APAY Threat Model

[← Profile](README.md) | [Controls](CONTROLS.md) | [Challenge Lab](CHALLENGE-LAB.md)

---

## Scope

The agent-to-payment plane: everything between a principal's objective and irreversible settlement, for autonomous systems that move value without a human present at each transaction.

**In scope:** compromised agent runtimes, hostile merchants and facilitators, malicious child agents, poisoned negotiation content, registry compromise, delegation escalation, protocol downgrade, economic drain, revocation races, settlement ambiguity, evidence inadequacy, consent decay.

**Out of scope:** the security of the underlying rails themselves (card network fraud systems, blockchain consensus, bank authorization), the model provider's infrastructure, and the principal's own decision to spend.

---

## The seam

The critical failure is not a single boundary. It is a chain of state transitions, each of which can be attacked independently:

```
human objective
  → agent interpretation          ← prompt injection lands here
  → merchant negotiation          ← untrusted content enters here
  → mandate rendering             ← what the human actually sees
  → human approval                ← signature covers THIS, not the objective
  → agent delegation              ← authority can widen here
  → credential release            ← key residency decides everything here
  → payment verification          ← path assurance can be downgraded here
  → settlement                    ← finality is decided here
  → fulfillment                   ← divergence surfaces here, too late
```

Two structural observations drive every control in the profile:

**Cryptography proves an object did not change. It cannot prove the object was a faithful translation of a prior intention.** The signature at "human approval" is valid, verifiable and covers exactly the wrong thing if the rendering was shaped by a compromised agent.

**Runtime attestation proves specified code loaded. It cannot alone establish that a nondeterministic model's current action is semantically authorized.** Measurement closes the host-compromise case and leaves the semantic case open, which is why deterministic constraint evaluation sits beside it rather than behind it.

---

## Adversaries

| Adversary | Capability | Primary objective | Why current protocols do not stop them |
| --------- | ---------- | ----------------- | -------------------------------------- |
| **Compromised agent host** | Full control of the agent process, its identity credentials and its mandates | Mint valid authorizations | Every signature they produce is genuine. Identity and mandate protocols verify it correctly because it is correct |
| **Prompt-injection operator** | Controls content the agent reads - catalogs, reviews, other agents' replies | Shape the mandate before it is signed | AP2's own security model concedes prompt injection cannot be assumed preventable; the mandate is signed after the influence has landed |
| **Hostile merchant** | Authentic, registered, baseline-matching | Sell the wrong thing at a permitted price; substitute destination after approval | Provenance checks confirm identity, not honesty |
| **Malicious facilitator** | Sits in the settlement path | Substitute destination, delay to force retry, manufacture ambiguity | Facilitator identity is usually a routing detail, not a trust decision |
| **Malicious child agent** | Holds a legitimately delegated grant | Widen its own authority; distribute spend below every threshold | Per-transaction limits are evaluated per transaction |
| **Insider** | Can edit policy or reach signing infrastructure | Change constraints or route around the policy engine | Separation of duties is rarely enforced across negotiate/approve/sign/settle |
| **Nation-state / organized theft** | Supply chain, developer social engineering, key theft, long dwell | Drain agent treasuries at scale | Agent wallets on irreversible rails are a softer target than exchanges, with no chargeback to unwind |

### Established theft techniques, retargeted

DPRK-linked operations have repeatedly demonstrated that custody infrastructure, third-party software, developers and signing workflows are viable paths to large-scale cryptocurrency theft. Reported 2025 losses attributed to North Korean actors exceeded $2 billion. Those techniques map onto agent-payment systems directly:

| Established technique | Agent-payment equivalent |
| --------------------- | ------------------------ |
| Software and dependency compromise | Malicious payment adapter or signer library |
| Developer social engineering | Poisoned deployment or credential broker |
| Private-key theft | Mandate, wallet, agent or facilitator impersonation |
| Supply-chain compromise | Malicious model, skill, MCP server or agent package |
| Session or token theft | Mandate replay, payment-channel takeover |
| Address substitution | Merchant or settlement-destination replacement |
| Insider placement | Trusted operator manipulating policy or signing infrastructure |
| Cross-chain laundering | Rapid movement after irreversible agent settlement |

Nation-state risk belongs in the threat model. It does not belong in the initial product thesis: the controls that stop it are the same controls that stop a misconfigured child agent, and the second case is far more common and far easier to sell against.

---

## Risk register

Likelihood and impact are assessed for an enterprise running ACT-3 agents with real spending authority. "Residual" is what remains **after** the named controls, assuming they are correctly deployed.

| # | Risk | Likelihood | Impact | Controls | Residual |
| - | ---- | ---------- | ------ | -------- | -------- |
| R1 | **Poisoned mandate rendering.** Compromised agent shapes what the human approves while preserving valid signatures | High | Critical | APAY-02, APAY-03, APAY-04 | **Medium.** Rendering is derived from constraints and ambiguity cannot be model-resolved, but a principal who approves a correctly rendered bad bargain is not protected by any of this |
| R2 | **Runtime substitution.** Valid identity and mandate replayed from an unauthorized workload | Medium | Critical | APAY-05, APAY-06, I-7 | **Low** where hardware attestation is available; **High** where it is not, and the profile says so rather than accepting a declared measurement |
| R3 | **Checkout TOCTOU.** Merchant, item, price, shipping, recurrence or destination changes after approval | High | High | APAY-12, APAY-11, APAY-15 | **Low.** Canonical-field binding is mechanical |
| R4 | **Revocation race.** Cached grants, facilitators, child agents or open channels permit spend after the kill decision | High | Critical | APAY-13, I-8, epoch re-read at credential release | **Medium.** In-path components are covered; a facilitator holding an authorization it has not yet submitted is not, and no protocol currently lets us reach it |
| R5 | **Salami drain.** Spend distributed across children, merchants, rails and time so every individual check passes | Medium | High | APAY-09, APAY-10, I-8 | **Low** for in-tree spend; **Medium** across rails the gateway does not sit in front of |
| R6 | **Delegation escalation.** Child gains authority through translation, default inheritance or protocol conversion | Medium | High | APAY-08, APAY-07, lineage re-verification at execution | **Low** |
| R7 | **Protocol downgrade.** Agent selects guest checkout, bearer auth, an alternate facilitator or a weaker rail | High | High | APAY-14, min_assurance floor | **Low** in-path; **High** if the agent has any network path that bypasses the gateway entirely. Network-level enforcement is a deployment requirement, not a profile control |
| R8 | **Catalog poisoning.** Signed, authentic merchant content that is semantically adversarial | High | Medium | Containment only: APAY-09, APAY-04 | **High. Not solved.** Provenance cannot detect this. Containment bounds the loss; it does not prevent the purchase |
| R9 | **Registry compromise.** Valid registry entries direct agents to hostile keys, endpoints or destinations | Low | Critical | APAY-15, destination allow-lists, baseline digests | **Medium.** Baseline drift is detectable; a registry compromised *before* baselining is not |
| R10 | **Settlement ambiguity.** Timeout or partial failure causes duplicate settlement or service-without-payment | High | Medium | APAY-16, APAY-18, APAY-11 | **Low.** Ambiguous is a first-class state and commits exposure |
| R11 | **Evidence inadequacy.** Logs cannot distinguish agent error, principal authorization, host compromise and merchant manipulation | High | High | APAY-19, APAY-17 | **Low** where PTR is complete. Note this is a *liability* control: there is no industry consensus on who pays when an agent transaction goes wrong, and liability tends to follow whoever cannot prove their side |
| R12 | **Consent decay.** Repeated approvals lead principals to accept progressively broader scope | High | High | APAY-02 rendering order, APAY-03 ambiguity surfacing | **High. Partially mitigated at best.** This is a human-factors failure. Making breadth legible is not the same as preventing habituation |
| R13 | **Key residency failure.** Payment keys reachable from the agent process | Medium | Critical | APAY-06, NullCredentialBroker default | **Low** if a real signer is bound; **Critical** if someone replaces the refusing default with a permissive stub. This is the single most damaging change available in the codebase |
| R14 | **Cross-currency ceiling evasion.** Spend routed through a currency the ceiling does not cover | Medium | High | Money refuses cross-currency comparison; unmatched currency denies | **Medium.** Requires operators to declare converted ceilings per currency; the profile makes the gap explicit rather than silently converting at an attacker-influenced rate |

---

## Design decisions that follow from this model

**Fail-closed is the default path, not the error path.** Missing runtime measurement, unreachable revocation authority, expired quote, unverified merchant - none produce "allow with a warning". A control that degrades to permissive under load is load-bearing only when nothing is wrong.

**Unknown is not the same as revoked.** An unreachable revocation authority produces `reconcile`, not `deny`. Value does not move, but a human resolves the state rather than the caller retrying into a duplicate settlement.

**Ambiguous settlement commits exposure.** A timeout counted as zero spend is how a rail failure becomes free money. Exposure is reversed by reconciliation, not assumed away.

**No language model participates in a payment decision.** A policy engine an attacker can talk to is a policy engine an attacker can talk out of.

**Money is integer minor units.** Floating point in a spend ceiling is not a rounding quirk. Accumulated error is exactly the signal a micro-drain attack hides inside.

**The broker repeats checks the firewall already made.** Not redundancy: the assumption that the caller might be the compromised component.

**Attenuation is re-derived at execution, not trusted from mint time.** Checking only at delegation trusts that nothing edited a grant afterwards.

---

## Known limits

Restated together, because a threat model that only lists wins is marketing.

1. **Semantic intent integrity is mitigated, not solved.** No control here proves the principal meant what they said.
2. **Catalog poisoning is not addressed.** An authentic merchant selling the wrong thing passes every provenance check.
3. **Consent decay is a human-factors problem.** Legibility helps; habituation is not engineered away.
4. **Out-of-path spend is invisible.** The gateway contains what flows through it. Any rail the agent can reach directly is outside every ceiling in this profile.
5. **Hardware attestation availability governs R2.** Where it is unavailable, runtime binding degrades to a declared measurement, which the firewall refuses rather than accepts - meaning the honest outcome is reduced functionality, not reduced assurance.
6. **No rail binding is implemented.** Every claim in this document about AP2, x402, TAP, Agent Pay or KYA-OS behavior is about what the binding *must* verify, not about tested integration.
7. **The Rego policy is not validated against a live OPA server in this repository's CI.** Its input contract is test-enforced against the Python builder; its evaluation semantics are not.

---

*CP.5.APAY draft · NEXUS v0.4 · AI SAFE² v3.1*
