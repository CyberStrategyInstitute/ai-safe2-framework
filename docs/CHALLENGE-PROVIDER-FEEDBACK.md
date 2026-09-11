# AI SAFE² Challenge provider-feedback decision record

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)

[Framework Home](../README.md) | [CLI](../safe2/README.md) | [Challenge guide](CHALLENGE-CLI.md) | [Challenge 001](../challenges/001-anthropic-multi-agent-turf-war/README.md)

## Decision: preserve the challenge, improve evidence interpretation

Participant feedback supplied during release review described six TENIR kernel
verdicts, including PASS for enforcement-outage instead of the reference HOLD.
The participant attributed this to an admissibility vector without an enforcement
availability signal and declined to retune inputs merely to match the reference.
These are participant-reported observations, not an independently verified run.
The source export and ledger proofs were not available for this review. No
provider efficacy, partnership, certification, or endorsement is established.

The feedback exposed an interpretation risk in our system: the frozen outage
fixture concerns an authorized shared write, while C7 concerns protected actions.
The current state grader does not separately measure fail-closed availability.
Neither a valid import nor a completed shared write establishes C7 assurance.

## Closed in this release

- Clarify this scope boundary in the CLI guide and harness entry point.
- Regression-test external declarations under the existing TENIR contract.
- Preserve PASS as raw evidence and translate it to allow, without rewriting it.
- Keep missing state observations incomplete and external maturity unverified.
- Reject an unimplemented provider contract rather than silently accepting it.
- Record the clarification in release notes and the deployment PR.

The frozen protocol, grader, reference outcomes, contract enum, framework controls,
and provider scoring formulas are unchanged. These tests are locally constructed
regression probes, not imported participant results or independent replication.

## Evidence intake boundaries

Request the original export bytes, actual observed state, declared policy/runtime
identity, outage injection mechanism, and evidence of the execution boundary.
Do not synthesize state transitions from a kernel verdict. Freeze the original
run; any provider policy change creates a separately identified run.

`tenir-example-v1` permits a nonsynthetic declaration if its semantics match.
Use provider version metadata for implementation versions. A new translation
contract requires coordinated implementation, validation, and reconstruction.

Ledger sidecars remain unverified supplementary evidence. A future verifier would
need agreed byte canonicalization, leaf construction and order, hash algorithms,
episode/source binding, trusted-root authentication, and adversarial tests.
Merkle inclusion alone proves neither observation truth nor complete logging.

Any future provider-neutral expansion of coverage requires separate review and
versioning. It is not a commitment to alter Challenge 001 for a particular tool.
