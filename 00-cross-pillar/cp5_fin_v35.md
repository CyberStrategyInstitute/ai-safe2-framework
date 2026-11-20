# CP.5.FIN | v3.5 profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## CP.5 | C29

Preserve transaction intent, merchant conflicts, cumulative limits and settlement truth. Add a distinct finance profile only for verified institutional duties beyond APAY. Quorum should depend on consequence and applicable policy.

- **CP.5.R09** For commerce, bind buyer, merchant, amount, terms, destination, recurring commitments and settlement authority.
- **CP.5.R10** Disclose configured incentives and verify settlement and refund outcomes through independent evidence.

**Acceptance** Agent commerce, conflicts and obligations. Compare purchase, recurring commitment, refund and settlement cases.

[Research](../research/053_v35_c29.md)

## A2.7 | C35

C18 compressed ledger semantics into general transaction safety. Reservation, commitment and unknown outcomes warrant an explicit reusable requirement. P2 records evidence; the P3 mechanism prevents duplicate effects. Central state adds collision and availability risks.

- **A2.7.R03** Bind each idempotency key to task, operation, destination and canonical action parameters.
- **A2.7.R04** Reserve and commit the operation atomically where supported; reject key reuse for a different action.
- **A2.7.R05** Reconcile ambiguous results against destination state before retrying an irreversible effect.
- **A2.7.R06** Define retention, collision handling, timeout, partial completion and compensation semantics.
- **A2.7.R07** Return the recorded result for a completed identical request without executing it again.

**Acceptance** Exercise concurrent duplicate requests, key collision, timeout after commit and ledger outage. Document external services where exact duplicate suppression cannot be established.

[Research](../research/059_v35_c35.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
