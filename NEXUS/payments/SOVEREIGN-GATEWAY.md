# Sovereign Payment Gateway

**Human name:** Sovereign Payment Gateway  
**Technical name:** `NEXUSPaymentExecutionPlane`  
**Status:** NEXUS v0.5 draft contract; no production assurance claim

The Sovereign Payment Gateway is the protected execution boundary around the
NEXUS Payment Integrity Gateway. Its objective is simple: compromising an agent
process must not be sufficient to obtain a payment key, widen authority, replay
authorization, restore spent capacity, or hide what value moved.

## Deterministic boundary

The execution plane requires seven independently evidenced components:

1. a durable transactional authority and exposure store;
2. an atomic replay and idempotency store;
3. a compare-and-swap settlement state store;
4. a deterministic policy engine;
5. an isolated credential broker;
6. a durable evidence ledger; and
7. an independent runtime-attestation verifier.

Reference or in-process implementations do not satisfy deployment readiness.
`NEXUSPaymentExecutionPlane.readiness()` names every unbound or reference-only
boundary instead of returning an unexplained success value.

## Monotonic execution

```text
PROPOSED
  -> POLICY_ACCEPTED
  -> RESERVED
  -> CREDENTIAL_RELEASED
  -> SUBMITTED
  -> SETTLED
```

Failures terminate. An ambiguous result can only enter `RECONCILING`; it cannot
release exposure directly. Reconciliation may establish settlement, establish
safe release, or escalate for governed resolution. Terminal states cannot be
reopened.

Canonical transaction identity, idempotency key, authority grant, and
revocation epoch are immutable across the lifecycle. Durable implementations
must use compare-and-swap or equivalent transactional semantics; process-local
locks do not establish crash or multi-worker safety.

## Security invariant

Probabilistic risk signals may reduce limits, request stronger proof, or require
human review. They cannot override a failed deterministic control or authorize
credential release.

## Planned implementation stack

1. durable authority, reservation, replay, and settlement state;
2. isolated signer service and protected key backends;
3. live OPA evaluation with policy identity and divergence testing;
4. atomic gateway orchestration and governed reconciliation;
5. sandbox rail validation only after the preceding boundaries pass.

Each layer will ship with concurrency, crash-recovery, replay, revocation, and
negative-path evidence before the next layer is allowed to depend on it.

## Gateway State Vault

`SQLiteGatewayStateStore` is the first durable reference implementation. It
uses database uniqueness, immediate write transactions, and compare-and-swap
versions to preserve replay keys, revocation epochs, authority-tree exposure,
reservations, and execution state across workers and restarts.

It remains `REFERENCE` assurance rather than self-declaring deployment status.
A deployment must separately establish protected storage, access control,
backup and recovery, availability, monitoring, and operational ownership.
