# AI SAFE² CLI Roadmap to 1.0

This roadmap organizes development by complete user capability rather than by
date. Engineering pull requests may merge frequently. A public CLI release is
created only when its capability gate is satisfied and the combined workflow
has passed acceptance testing.

The objective for CLI 1.0 is a stable, provider-neutral evidence and decision
layer for assessing agent systems. After 1.0, ordinary growth should primarily
come from adapters, integrations, new assessment content, and compatible schema
extensions rather than unfinished core workflows.

This is a planning document. Items below a released version are not delivered
capabilities until their implementation, validation, and release evidence exist.

## Release policy

- Separate code review from product release. One capability may require several
  small pull requests, but those pull requests do not each require a version.
- Do not version by calendar cadence. Version when a defined user outcome is
  usable from installation through evidence export and human review.
- Keep the default branch releasable. Incomplete work remains behind an
  experimental command, explicit capability flag, or unmerged branch.
- Patch releases fix defects or documentation without adding a major workflow.
- Minor releases add one coherent, documented, acceptance-tested capability.
- Every release records exact revision, scope, exclusions, compatibility,
  security boundaries, validation evidence, residual risks, and rollback path.
- A passing automated score is evidence, not release authority. Required checks
  and named human acceptance remain distinct.

## Current foundation

The released CLI foundation through 0.5.0 includes project and MCP assessment,
skill gating, AISM decision support, local environment discovery, NEXUS and
NVIDIA SkillSpector evidence adapters, provider-neutral harness intake, task
receipts, usage evidence, unified manifests, Challenge Lab fixture workflows,
complete agent-system identity, and evidence-bounded failure localization.

These capabilities retain their documented limits. They do not by themselves
prove execution, root cause, billing, control effectiveness, organizational
maturity, or framework conformance.

## CLI 0.6: assess the correct change and deployment boundary

**User outcome:** Determine what system is being assessed, what a change
affected, and which findings are inherited, introduced, resolved, excluded, or
unknown.

Planned engineering sequence:

1. **Assessment scope contract**
   - Define deployable subjects and component boundaries.
   - Classify product code, tests, adversarial fixtures, examples, research,
     generated artifacts, dependencies, and third-party components.
   - Record included, excluded, partial, missing, and not-applicable coverage.
2. **Change attribution**
   - Compare a trusted baseline with the proposed revision.
   - Separate inherited findings from introduced, changed, and resolved
     findings.
   - Bind affected controls and components to the system identity manifest.
3. **Release-readiness card**
   - Combine scoped findings, before/after evidence, failure localization,
     hosted checks, residual risks, ownership, and next actions.
   - Produce canonical agent JSON and a readable human card.

Release gate:

- Mixed repositories no longer receive a deployment verdict based on fixtures
  or unrelated examples without explicit scope disclosure.
- Baseline and change findings are reproducible and deterministic.
- Negative, path-confusion, symlink, generated-content, and incomplete-coverage
  cases pass.
- At least one real repository and the AI SAFE² repository complete stranger-run
  acceptance from documented commands.

## CLI 0.7: continuous task evidence and operational truth

**User outcome:** Understand what agent work consumed, what it produced, what
was verified, and where evidence disappeared across harness boundaries.

Planned capabilities:

- Normalize task identity and lifecycle events across supported harness exports.
- Correlate receipts, artifacts, tests, tool calls, usage declarations, failures,
  retries, overrides, and completion claims without treating estimates as bills.
- Detect unsupported completion claims, missing verification, duplicate usage
  ownership, evidence gaps, and repeated operational friction.
- Provide opt-in local or CI automation for evaluating newly added or changed
  skills and agent configuration. No undisclosed telemetry or ambient content
  capture.
- Preserve provider attribution and native records through a stable adapter
  boundary.

Release gate:

- Users can trace one task from declaration through artifacts, verification,
  resource evidence, and final claim.
- Continuous modes are explicit, bounded, observable, stoppable, and documented.
- Secret, prompt, and personal-data handling passes adversarial review.
- Degraded providers and unavailable evidence fail honestly without erasing the
  partial record.

## CLI 0.8: AISM implementation decisions and remediation

**User outcome:** Translate system and operational evidence into an actionable,
human-owned improvement decision.

Planned capabilities:

- Bind AISM assessment scope to system identity and deployment boundaries.
- Score only supported implementation evidence while keeping normative maturity,
  supplemental evidence confidence, and scanner findings separate.
- Show control gaps, impacts, conflicts, dependencies, alternatives, why and
  why-not reasoning, recommended sequence, owners, exit criteria, and history.
- Generate machine-readable remediation plans and human decision cards.
- Reassess completed actions without silently converting implementation evidence
  into certification or organizational conformance.

Release gate:

- Every recommendation traces to evidence, an applicable control or AISM cell,
  a stated assumption, and an accountable decision owner.
- Missing evidence cannot improve a score or disappear from the denominator.
- Competing alternatives and accepted residual risk remain visible.
- CISO, engineer, governance, and agent acceptance passes produce consistent
  interpretations of the same canonical artifact.

## CLI 0.9: Challenge Lab execution and independent evidence exchange

**User outcome:** Run reproducible agent-governance experiments and compare
independent implementations without forcing them into identical internal
semantics.

Planned capabilities:

- Advance from fixture-only workflows to an explicitly bounded live execution
  harness for the applicable Challenge Lab treatments.
- Preserve pre-registration, scenario identity, treatment identity, system
  fingerprint, source artifacts, evaluator independence, and replay evidence.
- Stabilize third-party translation and proof-sidecar contracts, with TENIR as a
  documented interoperability example rather than a required implementation.
- Make Challenge 001 easy to install, run, verify, compare, and report while
  preserving divergence and incompatible conditions.
- Bind Challenge evidence into system identity, task evidence, failure
  localization, manifests, and AISM review without claiming independent
  replication when the evidence does not establish it.

Release gate:

- A stranger can reproduce the documented Challenge 001 workflow from a clean
  environment and distinguish fixtures, controlled live runs, translations,
  and independent evidence.
- Unsafe action, false block, enforcement outage, replay, incomplete evidence,
  and provider divergence cases remain visible.
- Evaluator, adapter, source, and policy versions are bound to every result.

## CLI 1.0: stable core and integration platform

**User outcome:** Install one supported CLI and obtain a complete, reviewable
picture of an agent system's safety, security, governance, compliance evidence,
operational performance, and unresolved decisions.

Core completion requirements:

- One documented workflow connects discovery, system identity, assessment
  scope, scanning, harness evidence, task receipts, usage, failure localization,
  AISM decisions, remediation, Challenge Lab evidence, and manifests.
- Stable public command names, exit-code meanings, schema identifiers, decision
  boundaries, configuration precedence, and machine-readable errors.
- A documented compatibility and deprecation policy with migration fixtures for
  every supported pre-1.0 artifact retained at 1.0.
- A provider-neutral adapter contract and conformance test kit for external
  harness, scanner, evaluator, ledger, usage, and cloud evidence providers.
- Secure defaults, bounded I/O, no-overwrite behavior, symlink and path defenses,
  subprocess limits, redaction guidance, dependency review, build provenance,
  and signed release artifacts where the release process supports them.
- Clean installation, offline-capable examples, Windows, Linux, WSL, and Python
  compatibility documented and validated to the declared matrix.
- Human-readable cards remain projections of canonical JSON, not separate
  decision sources.
- Complete quick start, command reference, architecture, threat model, evidence
  boundaries, troubleshooting, recovery, integration guide, and stranger-ready
  deployment checklist.

The 1.0 release gate requires:

1. All required hosted checks pass on the exact release revision.
2. Clean-package and documented-workflow acceptance passes across the supported
   runtime matrix.
3. Security, usability, adaptability, modularity, compatibility, and evidence
   honesty reviews have no unresolved release-blocking findings.
4. Agent acceptance covers multiple harness perspectives; human acceptance
   covers accountable security, engineering, governance, and first-time users.
5. The AI SAFE² self-assessment and at least one attributed independent review
   are recorded with their scope and limitations.
6. Every planned core capability is delivered, explicitly deferred as
   non-core, or removed from the 1.0 claim by the release owner.
7. Release notes provide a verified before/after view, quick start, limitations,
   rollback path, and next integration priorities.

## After 1.0

Post-1.0 work should normally extend the stable core through:

- native Codex, Claude Code, Hermes, OpenClaw, and other harness adapters;
- cloud, network, ledger, scanner, policy-engine, and usage-provider adapters;
- refreshed sovereign-runtime examples;
- additional Challenge Lab protocols and independently supplied evidence;
- compatible schemas, control content, reporting views, and performance work.

An integration that exposes a missing core abstraction may justify a 1.x core
change. It should not silently break the 1.0 contracts or redefine prior
evidence.

## Decision discipline

The roadmap is complete only when the user outcome is complete. A merged pull
request, passing test count, generated card, third-party score, or published
announcement is evidence of one step. None substitutes for the capability gate
of the target release.
