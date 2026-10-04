# Method reference

## Two-axis classification

Classify delivery shape and risk separately. A small diff can be architectural;
a large generated change can still be bounded. Use repository policy to set the
risk floor, then escalate when the affected trust boundary warrants it.

| Shape | Purpose | Required design | Production output |
| --- | --- | --- | --- |
| Spike | Answer a bounded unknown | Hypothesis and discard plan | No |
| Bounded | Deliver a contained change | Outcome, acceptance, scope, exclusions | Yes |
| Architectural | Change a durable boundary | Written design and implementation plan | Yes, after approval |

## Evidence modes

- `tdd`: demonstrate the requested behavior fails before implementation and passes after.
- `characterization-first`: capture current behavior before deliberately changing it.
- `contract-first`: establish schema/API/policy rejection and acceptance boundaries first.
- `schema-validation`: validate structured configuration without claiming runtime behavior.
- `render-validation`: inspect the rendered or interactive result, not only source text.
- `approved-spike`: collect learning evidence only; do not promote probe code.
- `not-applicable`: research-only work with no implementation claim.

## Systematic debugging

Reproduce, narrow the failing boundary, compare the failing path with a known-good
path, form one falsifiable hypothesis, change one cause, and verify. If evidence
contradicts the hypothesis, discard it. Do not accumulate unverified fixes.

## Verification and receipts

Verification must be fresh, scoped to the final revision, and distinguish local
results from hosted CI. Evidence files are hash-bound by the receipt. Hashes prove
which bytes were evaluated, not that a command genuinely ran or that the result is
correct. Human approval and release authority remain external to the receipt.
