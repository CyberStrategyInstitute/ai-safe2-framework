# AI SAFE² Challenge Lab executable evidence workflow

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Design](https://img.shields.io/badge/Docs-Challenge_Harness-820F1A?style=flat-square)](./CHALLENGE-CLI.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) | [CLI guide](./CHALLENGE-CLI.md)

---

The first implementation extends `safe2` with an offline Challenge 001 shared-state
pilot and provider-neutral import contracts. It validates experiment mechanics;
it does not establish real-agent effectiveness or independent replication.

## Implementation boundary

- Native runner: deterministic inert dictionary state; no processes, networks,
  real accounts, third-party code, or personal files are targets.
- Six cases: unauthorized-write, legitimate-write, missing-approval,
  valid-approval, replayed-approval, enforcement-outage.
- Treatments: uncontrolled, conventional, safe2-reference. The reference is a
  narrowly scoped fixture policy, not the complete T4 architecture or NEXUS.
- TENIR example: a synthetic export illustrating an adapter contract. It is
  not an upstream TENIR export standard or an execution of TENIR software.
- Translation, comparable conditions, reproduced grader results, and independent
  replication are distinct results. No automatic C3/C5 or conformance promotion.

## Shared implementation contract

Core lives in `safe2/challenge/`, commands in `safe2/commands/challenge.py`, and
versioned schemas/packs/fixtures in packaged `safe2/data/` resources. The existing
`challenges/001-anthropic-multi-agent-turf-war/` remains the study documentation.

`bundle.py` orchestrates the existing functions for `quickstart` and verifies the
fixed `safe2.challenge-bundle.v1` starter contract. Bundle paths are fixed basenames,
not executable or traversable provider instructions. The completion manifest is
written last. Verification pins the producing CLI version, replays fixture episodes,
reconstructs translations/comparisons, and regenerates reports. A caller-supplied
manifest fingerprint is optional and distinct from internal consistency checks.

`safe2/challenge/protocol.py` provides `protocol()` (the packaged protocol dict),
`experiment(seed=0)` (the pinned experiment identity), and `scenario(id)`.
Protocol fields: id, version, framework_version, enforcement_plane, scenarios.
Scenario fields: id, principal, target, requires_approval, approval,
control_available, authorized, initial_state. State has protected/shared strings.

Experiment fields: challenge_id, protocol_version, scenario_set_sha256,
grader_version, grader_sha256, environment, seed, model_id, enforcement_plane,
framework_version. Fixed fixture environment is `inert-shared-state-v1`, model_id
is `none`. Comparisons match the entire experiment plus episode case/trial coverage.

An episode has id, scenario_id, trial (integer >=0), treatment, action
{principal, operation: write, target, value}, decision {raw, mode, verdict,
constraints: [{operation, target}], constraints_applied: bool|null}, observation
{status: observed|missing, before: state|null, after: state|null}, metrics
{elapsed_ms: number|null, cost_usd: number|null, human_interventions: integer|null}.
Normalized verdicts: allow, deny, constrained, hold, unknown. Modes: enforce,
shadow, unknown. Provider originals stay in optional source_record.

`grading.py`: `grade_episode(episode)` independently uses the frozen scenario
specification and state change; returns {status: valid|incomplete|conflict,
unauthorized_change: bool|null, legitimate_completed: bool|null,
false_block: bool|null, decision_state_conflict: bool|null}. `summarize(episodes)`
regrades all episodes and returns counts/rates with denominators and unknowns.
No metric accepts producer-supplied success scores or expected authorization.

`model.py`: `make_run(episodes, experiment, provenance, provider)` returns a sealed
run; `validate_run(run)` raises ValueError for invalid schema/identity, duplicate
episodes or forged summaries/grades; `verify_run(run, public_key=None,
require_signature=False)` returns {valid, errors, signature_status}.

Run fields: schema_version=safe2.challenge-run.v1, run_id, created_at, experiment,
provider {name, version}, provenance {kind: native_fixture|synthetic_import|
external_import, producer_id, adapter_id, adapter_version, source_sha256: str|null,
source_hash_basis: original_bytes|canonical_json|null,
source_run_id: str|null}, episodes (with grade), summary, claims, limitations,
integrity_sha256, optional signature. Claims always retain challenge_maturity=C2,
framework_profile_conformance=not_assessed, aism_maturity=not_assessed,
independent_replication=not_established for fixture runs; external imports must
retain challenge_maturity=unverified and source evidence unverified.

`runner.py`: `run_challenge(challenge_id='001', seed=0, repetitions=1,
treatments=None)` produces a run. Run_id/time vary, but experiment, episodes,
and graded counts are repeatable. No fabricated wall-clock/cost estimates.

`adapters.py`: `import_source(source, adapter='generic', source_sha256=None)`.
Source envelope: schema_version=safe2.challenge-source.v1, provider {name,
version}, producer_id, run_id, synthetic: bool, experiment, episodes. Required
adapter_contract: generic-v1|tenir-example-v1. Input episodes share the same
structure, except decision has raw, mode, constraints, constraints_applied (no
normalized verdict). Adapter computes verdict and preserves every original
episode in source_record. Unknown meanings remain unknown; constrained/shadow
results cannot be silently promoted to unconstrained permission or prevention.

`compare.py`: `compare_runs(left,right)` verifies both runs and emits
safe2.challenge-comparison.v1 with comparable, mismatches, outcome_agreement,
independent_replication=not_established, limitations. Do not pool dissimilar
experiments or report a synthetic import as a second independent producer.

`io.py`: `read_json(path)` bounded strict JSON (no duplicate keys/nonfinite floats),
`write_json(path,value)` and `write_text(path,text)` reject existing outputs,
symlink/reparse parent paths, and bound size. CLI catches ValueError/OSError.
`integrity.py`: SHA-256 change detection plus optional Ed25519 signing via
`sign_run(run,key_path,signer_id)`; verifier trusts only an explicitly supplied
public key, not an embedded one. Signing importer output authenticates the
importer artifact, not the upstream provider, observation, or approval.

## CLI and validation

Commands: challenge list, validate 001, run 001, import FILE --adapter,
compare LEFT RIGHT, verify FILE, report FILE --format markdown|html,
sign FILE --key FILE --signer-id ID. JSON remains canonical; errors have stable
exit codes. Signing is optional for fixture mechanics and is not human approval.

Tests cover independent graders, all treatment/scenario cases, unknown and
constrained provider decisions, shadow evidence, provenance, comparison refusal,
tampering, signatures with caller-supplied keys, path bounds, malformed input,
installed-package discovery, schema/manifest/AISM interoperability, and CLI use.

The next stage needs real provider exports and an isolated live execution backend
that enforces the Lab's Rules of Engagement. Independent replication additionally
requires independent operators and the published study evidence requirements.

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
