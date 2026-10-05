# Governed Payment Recovery

**Human name:** Governed Payment Recovery

**Technical name:** `DeterministicReconciliationAuthority`

**Profile:** CP.5.APAY recovery extension

**Status:** Draft reference standard; not a production assurance claim

## Purpose

An unknown payment outcome is neither success nor failure. This standard keeps
uncertain value inside the economic ceiling until authenticated rail evidence
establishes what happened. It prevents an agent, operator, timeout, or repeated
callback from turning uncertainty into a second payment or restored capacity.

## Normative requirements

| ID | Required outcome |
| --- | --- |
| GPR-01 | Exactly one durable recovery case exists per execution and authorization. |
| GPR-02 | Case identity binds the execution, authorization, signing digest, and immutable recovery-policy digest. |
| GPR-03 | Opening a case and advancing `AMBIGUOUS` to `RECONCILING` are one atomic operation. |
| GPR-04 | The recovery component has no payment-submission or credential-issuance capability. |
| GPR-05 | New observations follow a fixed cadence and bounded attempt/deadline policy. |
| GPR-06 | Identical authenticated evidence is idempotent and does not consume the attempt budget. |
| GPR-07 | Only Settlement Truth Authority evidence can establish settlement or authoritative failure. |
| GPR-08 | Settlement, case closure, execution state, and exposure commit occur atomically. |
| GPR-09 | Authoritative failure, case closure, execution release, and exposure release occur atomically. |
| GPR-10 | Exhaustion or deadline escalates without releasing exposure; stale or conflicting workers fail closed. |

`ESCALATED` means governed intervention is required. It does not mean the funds
did not move, and it never restores authority automatically. Any later manual
write-off, dispute, or accounting adjustment is a separately authorized action
and must not be represented as rail truth.

## Privacy and evidence

Recovery cases store identifiers, digests, timestamps, state, and evidence
references—not raw payment payloads, credentials, human-authentication secrets,
or free-text agent explanations. Evidence retention, disclosure, deletion,
legal hold, and jurisdiction remain deployment-governance responsibilities.

## Reference verification

`test_payment_reconciliation.py` proves atomic open/settle/fail behavior,
exposure-preserving escalation, cadence enforcement, idempotent observations,
deadline handling, stale-worker rejection, and artifact-substitution denial.
The SQLite implementation demonstrates transactional semantics on one host; a
production claim requires an equivalently consistent, protected, monitored,
and recoverable store plus an independently authenticated settlement observer.
