# AI SAFE² CLI 0.9.9 Release-Candidate Record

## Outcome

CLI 0.9.9 consolidates the pre-1.0 core into one installable, provider-neutral
evidence layer for projects, harnesses, agents, and accountable human reviewers.
It is a release candidate for final validation, not the 1.0 stability promise.

## Capability sequence

| Slice | User outcome | Evidence boundary |
|---|---|---|
| Project initialization | Create secure defaults and see configuration precedence | Does not authorize assessment scope |
| Unified assessment | Produce one bounded project bundle and human card | Unrequested content remains incomplete, never clean |
| Adapter SDK | Validate external descriptors and attributed specimens | Conformance checks contracts, not provider truth |
| Codex JSONL | Convert explicit Codex traces without retaining prompts or output | Offline aggregate evidence; no session access |
| OpenTelemetry | Import OTLP traces and export privacy-reduced SAFE² metadata | Selected categorical values are hashed; telemetry remains producer-controlled and is not proof of execution or billing |
| Continuous evidence | Preserve repeated skill/configuration change reports | Polling detection, not interception or prevention |
| Claim audit | Identify evidence consistency, contradictions, gaps, and disclosures | No honesty score, deception inference, or completion certification |
| Installation self-check | Verify Python, package metadata, dependencies, entry point, and contracts | No signature, vulnerability, or project assurance claim |
| Stranger acceptance | Replay fixed benign/hostile controls from an installed release | Self-produced reproducibility, explicitly not independent validation |

## Compatibility

- Python support target remains CPython 3.11–3.14.
- Existing command names and the legacy `mcp-score`, `mcp-scan`, and
  `mcp-safe-wrap` aliases remain available.
- New schemas and commands are additive. Existing evidence artifacts are not
  rewritten automatically; replay them with the producing CLI version.
- AI SAFE² remains framework v3.1 with 161 controls and CP.1 through CP.10. The
  UAS profile remains a 27-requirement regulatory extension.

## Security and privacy defaults

- bounded regular-file inputs, duplicate-key and non-finite JSON rejection;
- symlink/reparse defenses and no-overwrite output behavior at new boundaries;
- no prompts, command strings, command output, or arbitrary span bodies in
  adapter output; selected OpenTelemetry categorical values are represented by
  truncated SHA-256 labels rather than copied text;
- no ambient credential, session-store, or network access by the new adapters;
- explicit partial, unavailable, contradicted, and held states;
- provider output remains attributed evidence and cannot claim AI SAFE²
  conformance.

## Validation gate

The candidate is ready to release only after the exact combined revision passes:

1. focused negative and contract tests for every new capability;
2. the complete repository suite;
3. Ruff and repository UX/Markdown checks;
4. source and wheel builds plus installed-wheel self-check and acceptance replay;
5. hosted Python 3.11–3.14, CodeQL, dependency, secret, schema, and consistency
   checks; and
6. attributed external review when available, recorded as unavailable rather
   than approval when no current result exists.

Final observed results belong in the pull request and release record after those
checks run. This document intentionally does not predeclare them green.

## Remaining path to 1.0

The 1.0 decision is a stability and acceptance gate: freeze public command/schema
contracts, document deprecation policy, complete multi-platform stranger and
persona acceptance, record AI SAFE² self-assessment plus attributed independent
review, close release-blocking findings, and sign/publish the exact validated
artifacts through the release owner.
