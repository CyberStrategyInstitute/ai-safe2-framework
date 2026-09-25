# CP.5.APAY - Agentic Payments Integrity Profile

**Continuous Transaction Integrity and Authority Assurance for autonomous systems**

[Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM) | [NEXUS](../README.md) | [Adapter Guide](ADAPTER-GUIDE.md) | [Sovereign Payment Gateway](SOVEREIGN-GATEWAY.md) | [Threat Model](THREAT-MODEL.md) | [Controls](CONTROLS.md) | [Challenge Lab](CHALLENGE-LAB.md)

**Previous:** [← NEXUS](../README.md) | **Next:** [Gateway / Runtime Enforcement →](../../gateway)

---

## Status

| Component | Status |
| --------- | ------ |
| CP.5.APAY control set (APAY-01 … APAY-20) | **Draft. Non-normative until reviewed.** |
| Protocol-independent object model | Implemented, tested |
| Mandate compiler and trusted rendering surface | Implemented, tested |
| Authority graph, attenuation, aggregate containment | Implemented, tested |
| Transaction firewall (deterministic PDP) | Implemented, tested |
| Credential broker contract | Implemented; **no production signer binding ships here** |
| Evidence ledger and PTR | Implemented, tested |
| `opa/nexus-apay.rego` | Written; input contract test-enforced. **Not validated against a live OPA server in this repository's CI.** |
| Mandate Bridge (AP2 v0.2) | **Authoritative reference profile; deployment verifier required** |
| Card Trust Bridge (Visa TAP) | **Authoritative recognition profile; deployment verifier required** |
| Agent Token Bridge (Mastercard AP4M) | **Verifier-evidence profile; no public wire compatibility claimed** |
| Portable Delegation Bridge (KYA-OS) | **Authoritative authority-overlay profile; deployment verifier required** |
| x402 **SafePay Exact** (`X402V2ExactEVMUSDCBinding`) | **Narrow structural binding. Shadow mode only; no live facilitator or chain verification.** |
| Production assurance claim | **Not made.** See [MVP acceptance gates](#mvp-acceptance-gates). |

Nothing in this profile should be described as production-assured until a deployment demonstrates every acceptance gate below.

---

## The claim

> Identity proves which agent arrived.
> Mandates prove what authority was granted.
> NEXUS proves whether this measured workload may still use that authority for this transaction, at this moment - and stops the entire authority tree when it may not.

---

## Why this profile exists

The agentic payments ecosystem is standardizing quickly, and it is standardizing around two questions:

- **Recognition.** Is this a registered agent rather than a hostile bot? Visa's Trusted Agent Protocol and Mastercard's Agent Pay both answer this, both using Web Bot Auth as the authentication layer.
- **Authorization.** Did a human approve this purchase? AP2 answers this with signed mandates, and Google contributed it to the FIDO Alliance in April 2026. Mastercard contributed Verifiable Intent into the same process.

Both questions are being answered well. Neither of them is the question that decides whether money stays where it belongs.

The unanswered question is **integrity of the executing workload between authorization and settlement**. Every protocol above assumes the host signing the mandate is trustworthy. None require proof of it. An attacker who owns the agent host inherits its identity, its registrations and its mandates intact, and every signature they produce verifies correctly, because it is correct - it was made with the real key by the real credential on behalf of the real principal.

That is not a gap in any one protocol. It is a layer none of them claim.

### Four kinds of integrity, and who covers which

| Integrity | What it establishes | Covered today by |
| --------- | ------------------- | ---------------- |
| **Syntactic** | Signatures, hashes, audiences, amounts, expiry, nonce and checkout bindings match | AP2, x402, Web Bot Auth, card-network tokens |
| **Semantic** | The proposed transaction is within a deterministic reading of what the principal approved | Partially AP2 (constraint evaluation); the translation from objective to mandate is uncovered |
| **Runtime** | The agent, policy engine, tools, signer and credential broker are running in an approved state | **Nothing in general adoption** |
| **Temporal** | Authorization, delegation, attestation and revocation are all still valid at the instant of execution | **Nothing in general adoption** |

CP.5.APAY is the profile for the bottom two rows, and it binds them to the top two rather than duplicating them.

### What this profile does not claim

Stating these plainly matters more than the control list, because a profile that overclaims gets deployed as though the overclaim were true.

- **It cannot prove the principal meant what they said.** Cryptography proves an object was approved, not that the object faithfully represented an earlier intention. The mandate compiler makes the translation inspectable and refuses to let a model close an ambiguity. That is a mitigation, not a solution.
- **It cannot make an irreversible rail reversible.** Removing the chargeback removes recourse for both sides. Recourse can be layered above an irreversible rail through escrow, lock periods or contractual remedy, and the profile models that as a property of the path. It does not manufacture it.
- **It cannot detect a merchant that is authentic and malicious.** Provenance checks confirm a counterparty is who the registry says. A registered merchant with a matching baseline can still sell the wrong thing at a permitted price. Containment is what survives this case, and Challenge Lab experiment 8 exists to keep that limit visible rather than quietly assumed away.
- **It does not resolve liability.** No comprehensive US statute currently settles who pays when an agent buys autonomously, and existing electronic-agent attribution, contract, agency and consumer-payment doctrines still apply in ways that remain fact-specific. What the profile produces is evidence. Liability tends to follow whoever cannot prove their side.

---

## Position in the stack

CP.5.APAY is the **fourth enforcement plane**. It is not a wallet, an identity provider, a payment processor or a rail.

```
                       ┌──────────────────────────────────────────┐
  north-south          │  model / provider        (AI SAFE2 gateway)
  east-west            │  agent ↔ agent           (NEXUS v0.3)
  agent-to-tool        │  agent ↔ MCP/tools       (CP.5.MCP)
  agent-to-payment     │  agent ↔ VALUE           (CP.5.APAY)   ← this profile
                       └──────────────────────────────────────────┘

        agent                                      value
          │                                          │
          │   ┌──────────────────────────────────┐   │
          └──►│  NEXUS Payment Integrity Gateway │◄──┘
              ├──────────────────────────────────┤
              │ identity adapters                │  Entra · KYA-OS · SPIFFE · Web Bot Auth
              │ mandate compiler + trusted surface│ deterministic constraints, recorded ambiguity
              │ runtime verifier                 │  measurement, freshness, baseline
              │ authority graph                  │  attenuation, lineage, subtree exposure
              │ transaction firewall (PDP)        │  no model participates
              │ credential broker                │  keys the agent cannot reach
              │ risk engine                      │  velocity, micro-drain, dispersion
              │ evidence ledger (PTR)            │  hash-chained, selectively disclosed
              │ revocation plane                 │  one epoch severs the whole tree
              └──────────────────────────────────┘
                              │
       credential providers · x402 facilitators · card-token services
       bank APIs · stablecoin wallets
```

The gateway is deployable by the spend-side enterprise **alone**. That is the point of the beachhead: an organization running agents that spend money already controls the runtime, the identity system, the policy and the wallet integration. It does not need merchants, card networks or registries to adopt anything first.

---

## Protocol independence

Controls bind to framework-owned constructs, never to protocol-owned sessions or vendor tokens. Seven canonical identifiers:

| Identifier | Answers |
| ---------- | ------- |
| `principal_id` | Who is ultimately accountable |
| `authority_grant_id` | The framework-owned mandate |
| `delegation_chain_id` | Lineage root for the authority tree |
| `runtime_measurement_id` | What workload is executing right now |
| `policy_id` | Which deterministic ruleset decided |
| `transaction_intent_id` | What this movement of value is for |
| `revocation_epoch` | Monotonic counter; a stale epoch is not authority |

AP2 mandates, x402 payloads, Visa TAP signatures, Mastercard Agentic Tokens and KYA-OS delegations are **adapters onto** these objects. `APAY` deliberately avoids naming any one of them, so the profile survives the protocol war rather than picking a side in it.

---

## Standards landscape

What each system contributes, and what it does not establish. This table is the reason the profile targets the layer it does.

| System | Strongest contribution | Does not establish |
| ------ | ---------------------- | ------------------ |
| **AP2 v0.2** (FIDO, Apr 2026) | Signed open/closed mandates, cart binding, constraint evaluation, receipts, selective disclosure. Security model explicitly treats the agent and LLM as potential attackers | Independent measurement of the executing host, model, memory, policy engine or tool chain |
| **Mastercard Verifiable Intent** | Tamper-evident record of user-approved agent activity, into the same FIDO process | Cross-rail runtime attestation or independent enforcement |
| **Visa TAP** | Signed agent-to-merchant HTTP interaction; browse-versus-pay intent | Workload software state, memory integrity, or mandate conformance |
| **Web Bot Auth** (IETF I-D, not an RFC) | Per-request cryptographic authentication of automated HTTP clients | Authorization scope, principal intent, runtime state, spend-policy conformance |
| **Mastercard Agent Pay / AP4M** | Agentic tokens scoped to agent, merchant and consent; high-frequency machine transactions across rails | Publicly testable end-to-end runtime-integrity controls |
| **x402** (Linux Foundation, Apr 2026) | HTTP-native payment negotiation; verification and settlement schemes | Principal intent semantics, agent-runtime integrity, dispute protection |
| **KYA-OS** (DIF, from MCP-I, Mar 2026) | DID identity, scoped and revocable delegation, holder-of-key proof, consent gating | Payment settlement invariants, workload-behavior assurance |
| **Entra Agent ID** | Enterprise ownership, sponsorship, lifecycle, agent token issuance | Cross-tenant portability; agent identities receive tokens only in their home tenant |
| **ERC-8004** | Portable on-chain identity, reputation and validation registries | Non-transferable reputation continuity; identity tokens are transferable, so reputation can separate from the operator that earned it |

**The leverage point is FIDO.** AP2 and Verifiable Intent are both in that process now, before the authorization model is entrenched. Runtime-assurance evidence, revocation semantics, cumulative constraints and standardized execution receipts are far cheaper to introduce as profile requirements today than as retrofits later.

---

## The control set

Twenty controls. Full text, AI SAFE² mapping and test references in [CONTROLS.md](CONTROLS.md).

| ID | Control | Normative outcome |
| -- | ------- | ----------------- |
| APAY-01 | Principal and owner binding | Every payment-capable agent links to a verified principal, owner of record, ACT tier and applicable HEAR |
| APAY-02 | Trusted mandate rendering | Consequential terms render through an integrity-protected surface outside the nondeterministic agent's control |
| APAY-03 | Intent translation evidence | Original instruction, normalized constraints, assumptions and unresolved ambiguities are preserved and separately hashed |
| APAY-04 | Independent constraint evaluation | A deterministic engine, not the LLM, validates amount, payee, item, category, geography, rail, expiry, recurrence and cumulative exposure |
| APAY-05 | Runtime-bound authorization | Credential release requires a fresh, approved workload measurement |
| APAY-06 | Non-exportable signing authority | Payment keys stay in an HSM, TEE, secure element or managed signer; the model never receives key material |
| APAY-07 | Separation of duties | Negotiation, evaluation, approval, signing, settlement and reconciliation are independently authorized capabilities |
| APAY-08 | Monotonic delegation | Every child grant is equal to or narrower than its parent on every axis |
| APAY-09 | Aggregate economic ceiling | Limits aggregate across agents, descendants, merchants, facilitators, rails, currencies and rolling windows |
| APAY-10 | Velocity and micro-drain defense | Detects salami theft, split transactions, merchant dispersion and cumulative sub-threshold spend |
| APAY-11 | Freshness and replay resistance | Mandates, authorizations, quotes, carts and receipts are nonce-bound, expiring, idempotent and replay-resistant |
| APAY-12 | Transaction continuity | Material change between approved checkout and execution forces re-evaluation |
| APAY-13 | Revocation effectiveness | Revocation invalidates credentials, grants, mandates, channels, cached decisions and descendant authority within a declared objective |
| APAY-14 | Downgrade resistance | An agent cannot reach guest checkout, bearer credentials, alternate facilitators or weaker rails to bypass controls |
| APAY-15 | Counterparty provenance | Merchant identity, catalog provenance, destination and settlement contract validate against trusted baselines |
| APAY-16 | Settlement atomicity | Verification, credential release, execution, settlement and receipt state cannot silently diverge |
| APAY-17 | Privacy-preserving evidence | Verifiers receive only required attributes; withheld fields are committed by digest, not dropped |
| APAY-18 | Fail-safe financial response | Ambiguous verification, timeout, partial settlement, policy conflict or unavailable revocation status fails closed or enters governed reconciliation |
| APAY-19 | Dispute-grade evidence | An independently reconstructable package links intent, authority, runtime, delegation, execution and settlement |
| APAY-20 | Continuous adversarial validation | Changes to agents, models, prompts, policies, adapters, signers or rails trigger payment-integrity tests |

### New AISM invariants

Two architectural invariants are added alongside the existing six ([`opa/nexus-aism-invariants.rego`](../opa/nexus-aism-invariants.rego)):

- **I-7 Runtime-Bound Authority.** Authority to take a consequential action binds to a fresh measurement of the workload exercising it, not only to the identity presenting it.
- **I-8 Aggregate Economic Containment.** Consumable authority aggregates across the authority tree; every descendant's consumption counts against every ancestor's ceiling.

---

## Execution sequence

1. The principal states an objective and an explicit authority envelope.
2. The **mandate compiler** derives deterministic constraints and records what the instruction did not determine. Open-ended spend language becomes a recorded ambiguity, never an inferred number.
3. The agent discovers and negotiates. All external content - catalogs, offers, reviews, other agents' replies - is untrusted payment-influencing input.
4. A **trusted surface** renders material terms from constraints alone, consequence first. The rendering digest binds into the grant.
5. The gateway verifies principal identity, delegation lineage, policy, runtime measurement, merchant provenance and revocation epoch.
6. The **deterministic firewall** evaluates transaction-level and aggregate constraints. No model participates.
7. The **credential broker**, isolated from the agent runtime, signs only the canonical transaction the policy engine approved - after re-reading the revocation epoch, because a decision made microseconds ago is not authority if the kill switch fired in between.
8. Verification and settlement results produce linked receipts and update cumulative exposure atomically. Exposure is committed for ambiguous settlements too: a timeout that counts as zero spend is how a rail failure becomes free money.
9. Any material discrepancy enters fail-closed reconciliation rather than blind retry.

---

## Quick start

```python
from nexus_sdk.payments import (
    AuthorityGraph, MandateCompiler, Money, PaymentIntegrityGateway,
    PrincipalBinding, RuntimeMeasurement, TransactionFirewall,
    TransactionIntent, PaymentRail, AssuranceLevel, SettlementFinality,
)

# 1. Compile an instruction into deterministic constraints.
compiler = MandateCompiler()
mandate = compiler.compile(
    "Buy cloud capacity from our approved vendors, up to $500 a time",
    explicit={
        "allowed_merchants": {"vendor-a", "vendor-b"},
        "max_aggregate": Money.parse("5000.00"),
        "allowed_rails": {PaymentRail.CARD_NETWORK},
        "max_finality": SettlementFinality.REVERSIBLE,
        "hear_above": Money.parse("400.00"),
    },
)

# 2. Render for human approval. Generated from constraints, not agent prose.
rendering = compiler.render(mandate)
print("\n".join(rendering.lines))

# 3. Issue. Refuses while ambiguities are open.
grant = compiler.issue(
    mandate, principal_id="principal-1",
    agent_did="did:nexus:agent:buyer",
    approved_by="owner@example.org", rendering=rendering,
)

graph = AuthorityGraph()
graph.register_root(grant)

# 4. Gateway. The default broker REFUSES everything until a signer is bound.
gateway = PaymentIntegrityGateway(graph, firewall=TransactionFirewall(graph))
gateway.register_principal(PrincipalBinding(
    principal_id="principal-1", owner_of_record="owner@example.org",
    agent_did="did:nexus:agent:buyer", act_tier=3,
))

# 5. Authorize. Requires a fresh, attested runtime measurement.
outcome = gateway.authorize(intent, runtime=measurement)
if not outcome.authorized:
    print(outcome.verdict.codes)   # stable machine reason codes

# 6. Kill the whole tree, and measure what still moved afterwards.
gateway.revoke_principal("principal-1")
print(gateway.exposure_after_revocation("principal-1"))
```

Delegation narrows and never widens:

```python
child = graph.delegate(
    grant.authority_grant_id,
    agent_did="did:nexus:agent:sub-buyer",
    max_transaction=Money.parse("50.00"),
)
graph.delegate(grant.authority_grant_id, max_transaction=Money.parse("5000.00"))
# AttenuationError: delegation would widen parent authority on: max_transaction
```

---

## Required metrics

Identity match rates and fraud losses measure outcomes after the fact. These measure whether the controls were load-bearing. `GatewayMetrics` emits them directly.

| Metric | Definition |
| ------ | ---------- |
| Revocation effectiveness time | Time from authoritative kill decision until no descendant, credential, mandate, cache, channel or facilitator can create new exposure |
| Unauthorized exposure after revocation | Total attempted and settled value after the revocation timestamp. **Not** API acknowledgement latency |
| Runtime-binding coverage | Share of protected transactions tied to a fresh, policy-accepted runtime measurement |
| Delegation attenuation rate | Share of delegation edges proven not to increase authority |
| Aggregate-limit coverage | Share of spend visible to cross-agent, cross-merchant, cross-rail ceilings |
| Mandate-to-settlement continuity | Share of settled transactions with verified binding across approved terms and final payment |
| Downgrade-block rate | Share of weaker-path attempts denied or explicitly reauthorized |
| Evidence completeness | Share of required evidence fields present and cryptographically linked |
| Ambiguous-state fail-closed rate | Share of timeout, conflict or unknown states that do not produce uncontrolled settlement |
| Human interrupt effectiveness | Time from HEAR intervention to cessation of economically consequential actions |
| False-block cost | Legitimate transaction value and workflow time lost to control decisions |
| Dispute reconstruction time | Time to reconstruct principal, authority, runtime, decision and settlement state |

False-block cost is on this list deliberately. A control set measured only on what it stops will be tuned until it stops everything, and a payment gateway that blocks legitimate spend gets switched off.

---

## MVP acceptance gates

A release does not claim production assurance unless it demonstrates **all** of the following:

- [ ] The agent and LLM cannot read, export or directly invoke unrestricted payment keys
- [ ] Every protected transaction is evaluated by a deterministic policy engine
- [ ] Parent and child spending aggregate under one enforceable authority tree
- [ ] Child authority cannot exceed parent authority on any axis
- [ ] Runtime evidence is checked immediately before credential release
- [ ] Material cart or destination change forces re-evaluation
- [ ] Duplicate authorization and settlement attempts are idempotently rejected
- [ ] Revocation invalidates cached and descendant authority within a measured objective
- [ ] Weaker protocol paths cannot bypass the minimum-assurance policy
- [ ] Every settlement produces a linked, independently reconstructable evidence package
- [ ] Timeout, partial settlement, missing attestation, unknown revocation state and policy conflict fail closed or enter governed reconciliation
- [ ] External reviewers can reproduce the decision from evidence without trusting the agent's explanation

The reference implementation in `nexus_sdk.payments` demonstrates each of these **in test**. Narrow adapter profiles are implemented, but none is demonstrated against a live rail in this repository. That is the gap between a reference profile and a deployable product, and it is stated rather than papered over.

Ambiguous post-submission outcomes are governed by the draft
[Governed Payment Recovery](RECOVERY.md) extension. It requires durable,
authorization-bound cases, bounded observation, authoritative truth, atomic
exposure accounting, and exposure-preserving escalation rather than blind retry.

---

## Buyer position

The beachhead is **enterprises deploying agents that spend money**, not merchant acquirers.

The spend-side enterprise controls the runtime, identity, policy, wallet integration, delegated authority and incident response. It can ship a working integrity gateway without ecosystem adoption. Initial use cases: autonomous cloud and API purchasing, agent-operated procurement, machine-to-machine infrastructure payments, travel and expense agents, stablecoin treasury and service-payment agents, defense and critical-infrastructure logistics, agent marketplaces with delegated subcontracting.

The merchant and acquirer product follows as a verification service that validates runtime assurance, delegation, mandate continuity, cumulative risk and evidence before accepting an agent transaction. That side sells bot acceptance, fraud reduction, authorization confidence, dispute evidence and protection from protocol downgrade - but it requires counterparty adoption, which is why it is second.

---

## Standards engagement

CSI participates as the **execution-integrity and assurance profile** contributor, not as another identity issuer. That market is contested by Visa, Mastercard, Microsoft and DIF, and winning it is neither necessary nor likely.

| Venue | Proposal |
| ----- | -------- |
| **FIDO Payments WG** | Runtime-assurance evidence, revocation semantics, cumulative constraints, trusted-rendering requirements and standardized execution receipts for AP2 and Verifiable Intent |
| **IETF Web Bot Auth** | Distinguish operator authentication from workload-instance assurance; optional references to workload identity, attestation, policy and delegation, preserving privacy |
| **DIF KYA-OS** | Payment-oriented attenuation dimensions, runtime-measurement credentials, reputation-continuity requirements, descendant-revocation evidence |
| **x402 Foundation** | Pre-settlement policy hooks, idempotency, revocation epochs, aggregate ceilings, facilitator assurance, reconciliation receipts |
| **Card networks** | Position as the independent control and evidence layer operating *before* agentic-token presentation |
| **NIST / federal** | Frame agentic payments as an NHI, runtime-integrity, delegated-authority, evidence and resilience problem, not merely financial fraud |

---

## Files

```
NEXUS/payments/
├── README.md                      this profile
├── ADAPTER-GUIDE.md               human and agent integration path
├── THREAT-MODEL.md                risks, adversaries, and stated limits
├── CONTROLS.md                    APAY-01..20 with AI SAFE2 mapping and test refs
└── CHALLENGE-LAB.md               twelve falsifiable experiments

NEXUS/sdk/python/nexus_sdk/payments/
├── objects.py      protocol-independent object model
├── mandate.py      compiler, trusted rendering surface, consequence classification
├── authority.py    authority graph, aggregate containment, revocation plane
├── firewall.py     deterministic policy decision point
├── broker.py       isolated signing authority (NullCredentialBroker is the default)
├── evidence.py     PTR and hash-chained evidence ledger
├── gateway.py      orchestration and conformance metrics
├── opa_input.py    single input contract shared with the Rego policy
└── adapters.py     identity normalizer (implemented) + rail bindings (fail-closed)

NEXUS/opa/nexus-apay.rego                       out-of-process enforcement
NEXUS/schemas/apay-authority-grant-v0.4.schema.json
NEXUS/schemas/apay-ptr-v0.4.schema.json
NEXUS/sdk/python/tests/test_apay.py             95 control and attack tests
NEXUS/sdk/python/tests/test_apay_opa_contract.py  policy/builder drift guard
```

---

*AI SAFE² v3.1 · CP.5.APAY draft profile · NEXUS v0.4 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com)*
