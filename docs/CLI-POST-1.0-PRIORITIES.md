# AI SAFE² CLI: Post-1.0 Capability Priorities
### What 1.0 includes, what it deliberately leaves out, and what should be built next

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![CLI](https://img.shields.io/badge/CLI-Post--1.0_Priorities-820F1A?style=flat-square)](../safe2/README.md)

[Framework Home](../README.md) | [CLI Guide](../safe2/README.md) | [Operator Workflow](./CLI-1.0-WORKFLOW.md) | [Stability Policy](./CLI-STABILITY.md) | [Examples](../examples/README.md)

---

## The 1.0 value proposition

CLI 1.0 is a local-first evidence and decision-support layer for agent systems.
It gives agents a stable machine interface and gives people readable evidence
without granting the CLI deployment, exception, or risk-acceptance authority.

### Included in 1.0

- bounded project initialization and assessment;
- multi-harness, shell, WSL, explicit SSH-target, and safety-relevant asset
  discovery with explicit coverage gaps;
- model-plus-harness system identity and assessment scope;
- native project, MCP, and skill scanning and gates;
- provider-neutral adapter and evidence contracts;
- Codex JSONL and OpenTelemetry reference translators;
- NVIDIA SkillSpector and NEXUS attributed evidence intake;
- task receipts, usage correlation, claim audit, operational truth, failure
  localization, change attribution, and release-readiness cards;
- AISM scoring, comparison, evidence ingestion, and bounded remediation planning;
- Challenge Lab execution, import, translation, comparison, reporting, and
  artifact verification;
- offline installation self-check and stranger acceptance;
- stable commands, schemas, exit behavior, compatibility policy, and
  cross-platform clean-wheel qualification.

### Deliberately not included

- automatic access to private agent accounts, prompts, sessions, or cloud
  control planes;
- ambient network discovery or credential collection;
- native pre-install, pre-tool, or pre-action hooks for every harness;
- universal background interception of downloads, clipboard content, or agent
  context;
- proof that a detected harness is active, current, or securely configured;
- automatic AI SAFE² conformance, organizational AISM maturity, verified
  billing, or task-completion certification;
- autonomous remediation, release, deployment, exception, or risk acceptance;
- a hosted control plane or mandatory daemon.

These exclusions are security and evidence boundaries, not missing marketing
claims. A post-1.0 feature should narrow a boundary only with explicit consent,
least privilege, negative tests, and truthful coverage reporting.

## Priority order

Each priority is a capability-sized pull request. Progression is based on user
value and prerequisite relationships, not a calendar.

### Priority 1 — Guided agent onboarding and orchestration

**Problem:** 1.0 has the necessary primitives, but a first-time user or agent
must still assemble several commands and source artifacts.

**Build:** Add a `safe2 start` or equivalent guided workflow that selects an
outcome, checks installation, initializes safely, discovers the environment,
runs the bounded assessment, and writes a next-step card. It must preview the
plan, require explicit consent for content/config inspection, refuse overwrite,
and stop before remote access or remediation.

**Done when:** A clean-install evaluator can move from “point my agent at this
repository” to a reviewable local assessment without reading the full command
reference, and every skipped or unauthorized evidence domain remains visible.

### Priority 2 — Harness admission-hook kit

**Problem:** Polling and manual skill gates detect change, but cannot reliably
block a skill, tool, or configuration before a harness activates it.

**Build:** A small, versioned hook protocol and reference admission service for
pre-install, pre-load, pre-tool, and post-task events. Keep the native gate
synchronous and bounded; allow attributed third-party scanners to add evidence
without becoming the decision authority.

**Done when:** At least two materially different harnesses can call the same
protocol, hostile controls are blocked before activation, unavailable optional
providers degrade honestly, and no hook gains broader authority than the host
harness already granted.

### Priority 3 — Maintained native adapter pack

**Problem:** Provider-neutral intake works, but users still write translation
glue and can misstate what a harness export proves.

**Build:** Supported exporters or translators for the highest-adoption harnesses,
starting with documented, stable export or hook surfaces. Candidate coverage
includes Codex, Claude Code, Hermes, OpenClaw, Antigravity, and common agent/CI
telemetry. MiroFish, TinyFish, bots, Muse/Dot-style systems, and other runtimes
enter through the same conformance kit when a stable authorized interface exists.

**Done when:** Each adapter records provider and version, native source type,
collection scope, missing domains, redaction behavior, and exact-source binding;
passes shared conformance fixtures; and never claims access it did not have.

### Priority 4 — Explicit remote and cloud inventory connectors

**Problem:** A workstation assessment does not provide a complete picture when
agents also run in containers, remote hosts, CI, or cloud services.

**Build:** Opt-in connectors for named targets and least-privilege control-plane
exports. Start with containers and CI artifacts, then cloud inventories. Never
scan a network or discover accounts ambiently.

**Done when:** Local, WSL, container, CI, remote-host, and cloud evidence can be
joined into one system identity while unreachable, unauthorized, stale, and
not-applicable coverage remain distinct.

### Priority 5 — Technology Contribution Profile automation

**Problem:** The repository has a strong human method for deciding what a tool
contributes, but no CLI schema or command yet produces the reusable Technology
Card.

**Build:** Versioned TCP source and result schemas, conservative evidence
mapping, card rendering, comparison, and manifest integration. Preserve native
scores and keep technology contribution separate from organizational AISM
maturity and Challenge Lab C0-C5.

**Done when:** A user can compare alternatives by control fit, enforcement
location, evidence strength, failure behavior, retained authority, integration
cost, and residual risk without converting a vendor claim into conformance.

### Priority 6 — Challenge Lab adoption and independent replication kits

**Problem:** Challenge 001 is executable, but independent participants still
need easier packaging, submission validation, and result comparison.

**Build:** One-command participant bundles, adapter templates, offline
verification, reproducible reports, and public result metadata that preserves
raw divergence. Add new challenges only after the participation workflow is
proven.

**Done when:** A third party can run or translate its own harness result,
publish a verifiable evidence bundle, and compare it without changing the
frozen challenge or claiming that translated agreement proves independence.

## What should not be the next build

- another top-level score that collapses unlike evidence domains;
- a mandatory hosted service before the local trust model is proven;
- broad credentialed discovery hidden behind a convenient default;
- a long list of nominal integrations without versioned conformance tests;
- autonomous remediation before decision ownership and rollback are explicit;
- new Challenge Lab scenarios before Challenge 001 is easy to reproduce and
  independently submit.

## Release sequencing rule

Ship a capability only when its user journey, contract, negative cases,
security boundary, recovery path, documentation, and clean-install acceptance
are complete. Integration breadth is valuable after the common evidence layer
is stable; the moat is comparable, reproducible evaluation across systems—not
the number of logos in a README.
