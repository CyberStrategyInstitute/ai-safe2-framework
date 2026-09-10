# 🟠 safe2 CLI 0.2.0 — Verifiable evidence and hardened skill screening

## 🛡️ Security update: inspect the package, not just its documentation

This release closes a filename-based blind spot in the Skill Trust Gate.
Scripts, extensionless files, and text with unfamiliar extensions are inspected.
Binary or unsupported content requires review rather than a clean verdict.
New rules cover injection directives, credential paths, dynamic execution, and
other suspicious patterns. Coverage counts explain what was inspected.

**Action required:** re-scan previously approved packages. The retired standalone
script now exits with an error; use `safe2 gate skill PATH --strict`.
[CSI-2026-001 advisory](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/advisories/2026-09-09-skill-gate-executable-scope.md).

## 🔌 Existing NVIDIA integration, stronger input checks

The existing SkillSpector adapter adds safer inventory handling, strict JSON, and
`--executable` for a separate provider environment. Live SkillSpector 2.11.1
acceptance passed: the clean fixture returned SAFE with zero issues; the inert
hostile fixture returned DO_NOT_INSTALL with seven issues. Direct and adapter
findings agreed, and AISM kept all 30 maturity cells unscored.
[Live acceptance evidence and limits](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/SKILLSPECTOR-LIVE-VALIDATION.md).
No NVIDIA endorsement or general deployment-safety claim is implied.

## 🔎 Tested against our own skill, not just easy fixtures

A second pass reproduced 50 SkillSpector findings on our own skill package,
including security-test strings and partial coverage. The native gate now adds
test-path and IP-address context without silently downgrading attacker-controlled
content. We document false-positive candidates, residual risks, and why a scanner
score is evidence—not an installation decision.

[Beginner demo](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/SKILL-SCREENING-DEMO.md) · [Second-pass results and lessons](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/SKILL-SCREENING-SECOND-PASS.md).
Universal background interception is a proposed integration, not a feature claimed
by this release.

Python 3.11 remains the minimum; release CI now covers standard Python 3.11–3.14.
Check the release commit's results before treating configured coverage as verified.
[Runtime policy and setup](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/PYTHON-COMPATIBILITY.md).

## 🧭 One-command Challenge evidence

Local Windows validation after the second pass: **522 tests passed** on each of Python 3.11–3.14,
with four platform-specific skips per run. The rebuilt Python 3.14 wheel passed
installed starter verification and rejected the inert hostile fixture.
[Hardening validation and remaining limits](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/SKILL-GATE-HARDENING-VALIDATION.md).

Create an offline Challenge 001 evidence bundle with one command, inspect its
Decision Card, and let another user verify the complete folder.

```console
safe2 challenge quickstart 001 --output-dir my-first-run
safe2 challenge verify-bundle my-first-run
```

Install this release's CLI first, then open `my-first-run/decision-card.html`.
No model credentials, paid APIs, or third-party runtime are needed for this workflow.

## 🧪 What is included

- Six inert scenarios covering unauthorized and legitimate writes, approval states,
  replay, and enforcement outage behavior.
- Uncontrolled, conventional, and narrowly scoped AI SAFE² reference treatments.
- State-based grading, explicit uncertainty, safety/utility tradeoffs, and readable
  Markdown and self-contained HTML Decision Cards.
- Generic evidence import and a clearly labeled synthetic TENIR adapter example.
- Source preservation, compatibility checks, artifact verification, and optional
  Ed25519 signatures using a caller-trusted key.
- Portable starter-bundle verification: fixed file inventory, hashes, source binding,
  reconstructed comparisons, fixture replay, and regenerated reports.
- Evidence-manifest and conservative AISM ingestion. All 30 maturity cells remain
  unscored until a human assesses the evidence.

## 🛡️ What verification means

A successful check means the declared offline workflow and its evidence are
internally consistent. A manifest fingerprint obtained separately from a trusted
source can also pin the complete bundle:

```console
safe2 challenge verify-bundle my-first-run --expected-sha256 TRUSTED_MANIFEST_HASH
```

Replace the placeholder with the receipt's 64-character fingerprint. The verifier
does not execute submitted code. It rejects missing/changed artifacts, unsupported
versions, unexpected files, and inconsistent results. Use the producing CLI version.

## 📌 Scope matters

This release adds an **offline evidence workflow**, not the full live multi-agent
Challenge 001 backend. The TENIR example is synthetic: it does not execute TENIR,
verify its ledger, or imply endorsement. Matching translations are not independent
replication. Fixture results do not establish deployment safety, calibrated success
probabilities, framework conformance, or AISM maturity.

The reference fixture blocks unauthorized writes but also blocks legitimate work
during an outage. Its Decision Card makes that utility cost visible.

AI SAFE² remains v3.1 with **161 core controls and CP.1–CP.10**. UAS remains a separate
27-requirement regulatory profile. CLI and framework versions are independent.

## 🔗 Start here

- [CLI installation and command map](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md)
- [Challenge quick start and verification guide](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/CHALLENGE-CLI.md)
- [Validation results and remaining limits](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/CHALLENGE-CLI-VALIDATION.md)
- [Challenge 001 participation and study design](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/challenges/001-anthropic-multi-agent-turf-war)

**Compatibility note:** AISM ingestion now rejects ambiguous JSON, unsafe paths,
invalid Challenge runs, and existing output files. Use a new output filename.
The next stage is an isolated live backend and real, independently produced provider
evidence—not automatic promotion of the fixture results.
