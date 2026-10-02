# AI SAFE² Challenge CLI
### Run fixtures or authorized evaluators, preserve receipts, and compare without overclaiming

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Challenge Lab](https://img.shields.io/badge/Module-Challenge_Lab-820F1A?style=flat-square)](../challenges/README.md)
[![Scope](https://img.shields.io/badge/Scope-Bounded_process_evidence-808080?style=flat-square)](./CHALLENGE-HARNESS-DESIGN.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

[CLI Home](../safe2/README.md) | [Challenge 001](../challenges/001-anthropic-multi-agent-turf-war/README.md) | [Design](./CHALLENGE-HARNESS-DESIGN.md) | [Rules of Engagement](../challenges/001-anthropic-multi-agent-turf-war/ROE.md)

[Validation results and remaining limits](./CHALLENGE-CLI-VALIDATION.md)

---

## Technology profiles and claim separation

Use the [Technology Contribution Profile](./TECHNOLOGY-CONTRIBUTION-PROFILE.md)
to record what imported or executed challenge evidence supports. Bundle integrity
and reproduced grading do not establish independent execution or production
enforcement. The [validation candidates](./TECHNOLOGY-VALIDATION.md) are proposed
experiments outside the current frozen pack. Their contribution and
[assurance ratings](./EVIDENCE-ASSURANCE.md) are not calculated by this CLI.

## What this adds

`safe2 challenge` provides two deliberately distinct paths. `run` and `quickstart`
remain inert, offline fixtures. `plan` and `execute` add an operator-authorized,
bounded process boundary for an external Challenge 001 evaluator. The external
process receives one frozen scenario as JSON and returns decision and state
observations as JSON. The CLI independently grades those observations and binds
the plan, source, run, optional system identity, executable digest, and per-episode
request/response digests into a receipt.

Controlled execution is **not containment**. The executable runs with the current
user's operating-system authority and may possess network or filesystem access.
Timeouts terminate the direct child only; descendant-process containment is not
established by this portable runner. Use an OS/container boundary that can stop
the whole process tree.
Use a disposable, separately isolated environment for untrusted code or real
targets. AI SAFE² neither silently discovers nor automatically starts providers.
The authorization flag is required, and failures remain visible as incomplete
episodes instead of disappearing from the result.

The workflow runs known cases, independently recomputes grades from recorded
before/after state, retains provider originals, checks experiment compatibility,
and produces readable Decision Cards. "Independently" here means the grader does
not accept provider-authored scores; it does not mean an independent organization
observed the run. Imported observations remain assertions.

AI SAFE² remains 161 core controls and CP.1 through CP.10. UAS remains a separate
27-requirement regulatory profile. A fixture result does not confer framework or
profile conformance, an AISM rating, or independent replication.

## Quick start

### One command to produce the evidence

After installing this build, use a new folder name:

```console
safe2 challenge quickstart 001 --output-dir my-first-run
safe2 challenge verify-bundle my-first-run
```

Open `my-first-run/decision-card.html` for the human result. The receipt includes
the manifest SHA-256 fingerprint. Share that fingerprint through a separately
trusted channel if a recipient needs to detect an entirely rewritten bundle:

```console
safe2 challenge verify-bundle my-first-run --expected-sha256 TRUSTED_MANIFEST_HASH
```

Replace the placeholder with the exact 64-character fingerprint. Without it,
verification establishes internal consistency, not trusted origin. Keep the nine
artifacts and `bundle.json` together; move the folder without changing its contents.
This verifier accepts only the fixed offline starter-bundle contract, not arbitrary
provider exports or archives. It does not execute instructions or code from bundles.
Use the producing CLI version recorded in `bundle.json`; verification pins the
fixture/grader identity and regenerates that version's reports rather than silently
reinterpreting an older bundle with changed logic.
If creation fails partway through, the directory is retained for diagnosis; use
a new name for another attempt. Do not reuse it as a completed result.

### Individual commands and integration checks

Use a checkout containing this capability and install the CLI as described in
the [CLI README](../safe2/README.md). Run these commands from an existing writable
directory. Every output filename must be new; files are never overwritten and
parent directories are not implicitly created.

```console
safe2 challenge list
safe2 challenge validate 001
safe2 challenge run 001 --output native-run.json
safe2 challenge verify native-run.json
safe2 challenge report native-run.json --output native-card.md
safe2 challenge report native-run.json --format html --output native-card.html
safe2 challenge example --provider tenir --output tenir-synthetic-source.json
safe2 challenge import tenir-synthetic-source.json --adapter tenir --output tenir-import.json
safe2 challenge verify tenir-import.json --source-export tenir-synthetic-source.json
safe2 challenge run 001 --treatment safe2-reference --output reference-run.json
safe2 challenge compare reference-run.json tenir-import.json --output comparison.json
safe2 challenge verify comparison.json --left-run reference-run.json --right-run tenir-import.json
safe2 challenge report comparison.json --output comparison-card.md
```

### Controlled external evaluator

Use an absolute executable path and literal arguments. This example assumes
`my-evaluator` already implements the documented JSON request/response seam:

```console
safe2 challenge plan 001 --executable /absolute/path/to/python --arg /absolute/path/to/my-evaluator.py --provider-name "My evaluator" --provider-version 1.0 --producer-id my-team --treatment external-reference --system-identity system-identity.json --output execution-plan.json
safe2 challenge execute execution-plan.json --output-dir controlled-result --authorize-process-execution
safe2 challenge verify-execution controlled-result --plan execution-plan.json --system-identity system-identity.json
safe2 challenge verify controlled-result/challenge-run.json --source-export controlled-result/challenge-source.json
safe2 challenge report controlled-result/challenge-run.json --output controlled-card.md
```

On Windows, use the absolute path to `python.exe`; on Linux/WSL, use the absolute
interpreter or executable path. The plan hashes the executable and every argument
that resolves to a regular file at planning time, including a Python script. Other
arguments remain literal strings and are not interpreted as files. File symlinks
are resolved once during planning; the stored command uses and later rechecks the
exact regular-file target instead of executing the mutable link path.

The CLI sends one compact JSON object to stdin with schema version
`safe2.challenge-executor-request.v1`, challenge/protocol/scenario/trial/treatment
identity, the requested `action`, scenario `conditions`, and `initial_state`.
The process must exit `0`, write no more than the configured combined stdout/stderr
cap, and emit exactly this JSON shape on stdout:

```json
{
  "schema_version": "safe2.challenge-executor-response.v1",
  "decision": {
    "raw": "ALLOW",
    "mode": "enforce",
    "constraints": [],
    "constraints_applied": null
  },
  "observation": {
    "status": "observed",
    "before": {"protected": "protected:initial", "shared": "shared:initial"},
    "after": {"protected": "protected:initial", "shared": "candidate:0:0"}
  },
  "metrics": {"cost_usd": null, "human_interventions": 0}
}
```

`raw` is translated by the selected generic adapter; unknown labels remain
unknown. State observations, not the provider's label, drive independent grading.
Malformed JSON, extra/missing fields, nonzero exits, timeouts, truncated streams,
and output-limit events become explicit incomplete episodes. Stderr is bounded
but is neither retained nor printed because it may contain sensitive material.

The TENIR specimen is authored for this repository. It is an **illustrative
adapter contract, not a real TENIR execution or an upstream export standard**.
No endorsement, partnership, ledger verification, or agreement with TENIR is
implied. The specimen mirrors the six reference-treatment fixture outcomes to
test translation. Compare it with `reference-run.json`, not the 18-episode
all-treatment run: mismatched treatment coverage must be refused. Real provider
evidence may disagree; disagreement is useful evidence, not an integration failure.

## Command reference

| Command | Purpose and important options |
|---|---|
| `challenge quickstart 001 --output-dir DIRECTORY` | Create a new portable offline bundle and verify it; includes all-treatment and matched reference runs, synthetic source/import, comparison, and human reports. |
| `challenge verify-bundle DIRECTORY` | Check fixed file inventory, hashes, source binding, regraded/replayed results and derived reports. Optional `--expected-sha256` pins the manifest to a separately trusted fingerprint. |
| `challenge list` | Discover the packaged offline study as JSON. |
| `challenge validate 001` | Check packaged protocol identity and show pinned experiment hashes; not an assessment of a deployment. |
| `challenge run 001 --output FILE` | Run all six cases under three treatments. Optional `--seed` (0–2147483647), `--repetitions` (1–100), repeated `--treatment`. |
| `challenge plan 001 --executable FILE ... --output PLAN` | Pre-register the exact executable digest, literal arguments, provider declaration, treatment, bounds, and optional system-identity byte hash without executing it. |
| `challenge execute PLAN --output-dir DIRECTORY --authorize-process-execution` | Run the six frozen scenarios as separate bounded process calls and write source, normalized run, and receipt. The process is not sandboxed. |
| `challenge verify-execution DIRECTORY --plan PLAN` | Recheck schemas and plan/source/run/receipt bindings without re-running the executable. Supply `--system-identity` when the plan bound one. |
| `challenge example --provider tenir --output FILE` | Write the explicitly synthetic provider source envelope. |
| `challenge import FILE --adapter generic --output RUN` | Translate `generic-v1` or, with `--adapter tenir`, `tenir-example-v1`. Preserve source records and hash the original input bytes. |
| `challenge compare LEFT RIGHT --output FILE` | Compare compatible experiments and coverage. Record incompatibilities instead of pooling unmatched runs. |
| `challenge verify FILE` | Regrade a run and verify its seal, or check a comparison artifact. |
| `challenge verify IMPORT --source-export ORIGINAL` | Check an imported run against the original export bytes and retained source envelope. |
| `challenge verify COMPARISON --left-run LEFT --right-run RIGHT` | Reconstruct a comparison from its two original run artifacts. Both source options are required together. |
| `challenge report FILE --format markdown` | Render a run or comparison as Markdown; `html` is also supported. Optional `--output` writes a new file. |
| `challenge sign FILE --key PRIVATE.pem --signer-id ID --output SIGNED` | Sign a valid run with an unencrypted Ed25519 PKCS8 PEM private key. Optional signing dependency required. |
| `challenge verify SIGNED --public-key PUBLIC.pem --require-signature` | Authenticate against a caller-trusted Ed25519 SubjectPublicKeyInfo PEM public key. |

Machine workflows receive JSON artifacts or JSON command receipts. Human reports
are Markdown or self-contained, escaped HTML with no external scripts or assets.
Successful commands exit `0`; invalid verification and incompatible comparison
exit `1`; malformed/unsafe input or output operations exit `2`. Incompatible
comparisons still write their explanation artifact. Click usage errors also exit
`2` and may use ordinary CLI text rather than JSON. Validation errors omit raw
input values. Never put credentials in arguments, paths, or evidence records.

JSON inputs/outputs are bounded to 20 MB. Duplicate keys, non-finite numbers,
non-object input, symlinks/reparse paths, existing output files, and unsupported
contracts are rejected. Special files such as named pipes are rejected; Windows
device names, alternate streams and network-share paths are also rejected. Use
a local directory whose parents are not writable by untrusted processes: these
portable checks are not an OS sandbox against concurrent parent-directory swaps.
Treat imported source files as potentially sensitive:
the adapter intentionally retains their original records, not automatic redaction.

## Treatments and useful tradeoffs

| Treatment | Fixture policy | What a result can tell you |
|---|---|---|
| `uncontrolled` | Permissive execution | Confirms the fixture exposes unauthorized changes. |
| `conventional` | Basic authorized principal/target controls | Provides a simpler baseline that may be the right solution for some cases. |
| `safe2-reference` | Narrow scope/approval/replay checks with fail-closed outage behavior | Exercises selected governance mechanics and their false-block cost. Not full T4, NEXUS, or production enforcement. |

Cases are unauthorized write, legitimate write, missing approval, valid approval,
replayed approval, and enforcement outage. The outage case deliberately includes
a legitimate action: stopping it can be fail-closed yet reduce utility. Examine
per-treatment results instead of treating an all-treatment average as a safety
score. Deterministic repetitions are not independent statistical samples.

Decision Cards show provenance, applicable denominators, unknowns, conflicts,
episode history, safety/utility impacts, alternatives, limitations, and next
actions. They distinguish recorded facts from assumptions and do not invent
probabilities of real-world success or failure. History is within the artifact,
not a claim of ongoing deployment monitoring.

## Third-party evidence, not mandatory integration

### Outage scope and external-provider feedback

The frozen `enforcement-outage` fixture uses an **authorized shared write**.
Its reference treatment returns HOLD, but the state grader does not demand that
every provider reproduce this label or separately certify enforcement availability.
A valid record of an allowed shared write is not proof of the broader C7 claim
that protected actions fail closed during an enforcement outage. Missing state
observations remain incomplete; kernel verdicts alone do not establish execution.
Do not change inputs, thresholds, or the frozen challenge to obtain agreement.

`tenir-example-v1` accepts `synthetic: false` under the existing contract; this is
an external-source declaration, not authentication. Record runtime versions in
`provider.version`. A different adapter ID needs implemented translation and
verification support, not just an enum addition. The shipped example remains
synthetic. No TENIR ledger-proof verifier is provided: retain any sidecar as
unverified supplementary evidence, preserving original source bytes and hashes.

See the [provider-feedback decision record](CHALLENGE-PROVIDER-FEEDBACK.md) for
the distinction between translation, scope coverage, and independent evidence.

Start with the provider-neutral source contract. Adapt only the necessary data
seam: experiment identity, episode identity, requested action, raw verdict,
enforcement mode, constraints, and authoritative state observations. Keep the
source export and translated artifact together. No provider needs to adopt the
AI SAFE² runtime for evidence to be examined.

Translation maps meaning, not marketing labels. Unknown labels remain unknown.
A `HARD_VETO` in shadow mode is not evidence that a write was prevented.
`CONSTRAINED` does not mean unrestricted permission; constraints and evidence of
their application must survive translation. A periodic human signature does not
automatically prove action-specific approval. A claimed Merkle ledger is not
verified merely by importing its output.

| Evidence step | Supports | Does not establish |
|---|---|---|
| Translation | A bounded source can be represented without silently losing decision semantics. | Provider correctness, enforcement, or observation authenticity. |
| Regrading/replay | The pinned grader reproduces recorded outcomes from supplied state. | A fresh execution or a second independent observer. |
| Matched comparison | Protocol identity and case/trial coverage match; outcomes can be compared. | Real conditions were identical, causal superiority, or independent replication. |
| Independent replication | Separate operators execute the preregistered study with independently checked evidence. | Automatic universal validity or conformance outside the tested scope. |

Two adapters processing one export are still one source. Two synthetic runs
authored here are not independent replications. Even distinct producer IDs are
declarations until supported by independently verified provenance.

## Integrity and optional signatures

Unsigned SHA-256 seals provide change detection relative to a recorded digest,
not trusted provenance. An attacker can rewrite an unsigned artifact and compute
a new digest. Semantic verification additionally checks grades, summaries and
known protocol identity; it cannot prove that external observations happened.

For optional Ed25519 signing, install the local package's `challenge` extra:

```console
python -m pip install ".[challenge]"
safe2 challenge sign native-run.json --key operator-private.pem --signer-id operator-01 --output native-signed.json
safe2 challenge verify native-signed.json --public-key operator-public.pem --require-signature
```

Obtain/manage keys through your organization's trusted process. The tool does
not generate keys or trust an embedded public key. Protect the private key and
keep it outside evidence exports. A signer label is not proof of organizational
authority. Signing an imported run authenticates the importer artifact against
your key, not the upstream provider, a human approval event, or factual truth.
Comparison signing is not supported; retain and verify its source runs.

## Bring the evidence into AISM

```console
safe2 evidence manifest native-run.json tenir-import.json comparison.json --subject-id challenge-fixture --output evidence-manifest.json --strict
safe2 aism ingest native-run.json tenir-import.json --subject-id challenge-fixture --subject-name "Challenge fixture" --output assessment.json
```

Use new output filenames. Ingestion rejects invalid Challenge runs, ambiguous JSON,
unsafe paths and overwrites. All 30 AISM cells stay unscored; a human must decide
which evidence supports each applicable metric. These fixtures alone cannot justify
an AISM maturity rating or deployment approval.

## What must happen before broader live-system claims

1. Agree a real provider export and documented semantic mapping with its owner.
2. Freeze the study protocol, implementation versions, grader, policy and
   preregistration; materially changed conditions need a new study version.
3. Run this controlled process seam inside an authorized isolated environment
   with external stop controls, disposable targets, resource caps and the Lab's
   Rules of Engagement. The CLI's timeout and byte cap are not an OS sandbox.
4. Capture authoritative state, bypass attempts, legitimate utility, costs and
   human-intervention evidence without relying on agent prose.
5. Run independent operators against the same published study before claiming
   independently reproduced results. Keep Challenge maturity separate from
   framework/profile conformance and AISM maturity.

---

[CLI Home](../safe2/README.md) | [Challenge Lab](../challenges/README.md) | [Framework Home](../README.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
