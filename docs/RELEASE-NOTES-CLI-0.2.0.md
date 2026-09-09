# 🟠 safe2 CLI 0.2.0 — Challenge evidence you can verify

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
