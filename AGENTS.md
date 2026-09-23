# AI SAFE² v3.1 Agent Entry Point

This file is the deterministic starting point for software agents, coding assistants, retrieval systems, compliance bots, and other automated consumers of this repository.

It has two jobs: preserve correct framework interpretation and define the
minimum evidence-producing workflow for changes made in this repository or by
agents reusing these instructions elsewhere.

## Delivery workflow: isolate, build, prove, assess, ship

Use this workflow with any model, harness, or review provider. Repository facts
and executable evidence take priority over model confidence or reviewer scores.

### 1. Establish and isolate

1. Read the nearest applicable `AGENTS.md`, repository manifest, contributing
   guidance, security policy, and relevant tests before changing files.
2. Record the requested outcome, acceptance conditions, applicable controls,
   assumptions, exclusions, and evidence needed to call the work complete.
3. Inspect the working tree and preserve unrelated user changes. Never erase or
   rewrite work merely to obtain a clean checkout.
4. For a new feature, use a dedicated branch or worktree based on the current
   trusted default branch. Confirm the base revision; do not assume a branch
   named `main`, a remote named `origin`, or network access.
5. Parallel agents must use separate worktrees or non-overlapping task scopes.
   Shared-directory parallel editing is not isolation.

### 2. Build for the next maintainer

1. Follow the architecture already established in the target repository. Add a
   service layer only when the design calls for one; do not impose a generic
   structure that increases coupling or hides control flow.
2. Keep policy, evidence collection, decision logic, presentation, and external
   adapters separable where practical. Third-party outputs remain attributed
   evidence rather than native AI SAFE² decisions.
3. Prefer strict, versioned contracts; bounded inputs; explicit unknown,
   partial, and not-applicable states; deterministic output; and fail-closed
   behavior at security or authorization boundaries.
4. Preserve facts, declarations, assumptions, contradictions, and missing
   evidence as different states. Never manufacture a score, probability,
   successful execution, root cause, conformance claim, or human approval.
5. Add or update documentation, examples, package data, navigation, and version
   references in the same change when users or agents need them to succeed.

### 3. Prove the change

1. Capture the relevant before state before implementation when it can be
   reproduced safely. After implementation, capture the same measure or user
   journey under comparable conditions.
2. Use the evidence type appropriate to the claim:
   - UI or workflow: screenshots, video, or an accessibility/interaction trace.
   - Performance: repeatable measurements with environment and method.
   - CLI, API, contract, or security behavior: tests, exit codes, schemas,
     redacted output, hashes, and negative/adversarial cases.
   - Documentation: link, anchor, example-command, and rendering checks.
3. A passing test proves only the behavior that test observed. A screenshot
   does not prove backend enforcement. A hash proves byte equality, not truth.
4. Store only safe, minimal evidence. Redact credentials, personal data, private
   prompts, tokens, and unnecessary environment details.
5. If the before state cannot be captured, say why and use a regression test or
   historical artifact without presenting it as direct before/after proof.

### 4. Assess and independently review

1. Run the smallest relevant checks during development, then the repository's
   complete required quality, security, compatibility, packaging, and
   documentation gates before release.
2. Use AI SAFE² against the changed system where applicable: identify the full
   model-plus-harness system, applicable enforcement planes and controls,
   evidence coverage, limitations, residual risks, decision owner, and next
   action. Self-assessment must be labeled as such.
3. Inspect the final diff for unintended scope, unsafe defaults, secret or data
   exposure, dependency and supply-chain changes, compatibility breaks,
   misleading claims, and missing rollback or migration guidance.
4. Independent human or machine review is valuable corroboration. Greptile,
   CodeRabbit, Macroscope, SkillSpector, and similar providers are optional
   attributed reviewers, not authorities. Preserve provider/version, scope,
   result, unresolved findings, and coverage gaps.
5. Do not optimize for a vendor's numeric score or loop forever. Resolve valid
   findings, document accepted residual risk, and stop when defined acceptance
   gates pass or a decision owner must intervene.
6. For GitHub changes, complete local pre-push gates, then open a draft pull
   request. When Greptile is configured, run `check-pr`, address valid findings,
   rerun affected first-party checks, and use `greploop` for no more than five
   review cycles before marking the pull request ready. If Greptile is absent,
   unavailable, or degraded, record that state explicitly; never manufacture a
   confidence score or treat missing provider output as approval.

### 5. Ship with receipts

1. The pull request must explain the problem, user value, scope, exclusions,
   before/after result, security and evidence boundaries, tests performed,
   compatibility, residual risks, and rollback or recovery path when relevant.
2. Link durable evidence or provide reproducible commands. Distinguish local
   results from hosted CI and pending checks.
3. Re-run affected checks after every material review-driven change. Never cite
   an earlier green run as evidence for changed code.
4. Do not claim ready, complete, fixed, deployed, or released while required
   checks are failing, work remains uncommitted, the PR differs from the tested
   revision, or an external deployment has not been observed.
5. Agents may prepare and update a PR when authorized. Human merge, release,
   production deployment, risk acceptance, and framework-conformance decisions
   remain with their named owners unless authority is explicitly delegated.

### Portable completion record

For each material change, leave a concise record containing:

- subject and exact revision assessed;
- change scope and exclusions;
- applicable system identity and trust boundaries;
- before and after evidence, or the stated reason direct comparison is absent;
- validation commands and outcomes by environment;
- facts, assumptions, unknowns, conflicts, and residual risks;
- independent-review attribution and unresolved findings;
- recommendation, decision owner, rollback path, and next action.

This record can live in the pull request when no separate evidence artifact is
required. It must remain understandable without access to an agent's chat log.

## Start here

1. Parse `ai-safe2.manifest.json` first.
2. Treat `README.md` and the framework control documents it links to as the human-readable framework entry point.
3. Treat `skills/mcp/data/ai-safe2-controls-v3.0.json` as the stable machine-readable dataset for the unchanged 161-control core taxonomy.
4. Treat `skills/mcp/data/mcp-profile-v3.1.json` as the machine-readable CP.5.MCP v3.1 overlay containing MCP-1 through MCP-19.
5. Do not add the 19 MCP profile controls to the 161-control framework total.
6. Treat `00-cross-pillar/unbiased-ai/uas-profile-v1.json` as the UAS regulatory profile extension. Its 27 profile requirements do not add to the 161-control framework total and do not create CP.11 as a core Cross-Pillar control.

## Version model

- AI SAFE² Framework: v3.1.0
- NEXUS: v0.4
- Gateway: v3.0
- MCP primary specification binding: 2026-07-28
- MCP legacy compatibility binding: 2025-11-25
- UAS regulatory profile extension: v1.0, 27 profile requirements

Component versions are independent. Do not rewrite NEXUS or Gateway evidence as framework v3.1 component evidence unless that component has separately changed version.

## Normative interpretation

AI SAFE² defines governance outcomes, controls, evidence expectations, and conformance requirements. NEXUS is Cyber Strategy Institute's first-party reference implementation. NEXUS is not required for framework conformance. An alternative implementation may conform if it demonstrably satisfies the applicable controls and evidence requirements.

For CP.5 profiles, apply this protocol-independence rule:

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.

Do not infer a governance boundary from protocol-owned correlation or session fields.

## Enforcement planes

Classify requirements and evidence by plane before making a coverage claim:

- `north-south`: agent to model provider
- `east-west`: agent to agent
- `agent-to-tool`: agent to MCP server or tool

Evidence from one plane does not automatically validate another plane.

## Persistence vocabulary

Use these canonical persistence scopes in new evidence and integrations:

- `request`
- `handle_scoped`
- `durable`
- `swarm_shared`

Compatibility aliases may be accepted from older NEXUS data:

- `SESSION` -> `request`
- `CROSS_SESSION` -> `handle_scoped`
- `PERMANENT` -> `durable`

A state handle or legacy `Mcp-Session-Id` is not identity and is not, by itself, an authorization boundary.

## MCP v3.1 rules that agents must not infer incorrectly

- `server/discover` is optional under the 2026-07-28 binding. Its absence is not a conformance failure.
- MCP-19 requires intended-resource, audience, or equivalent evidenced binding.
- Possession of an opaque bearer token does not by itself prove MCP-19 audience/resource validation.
- The NEXUS MCP adapter in `NEXUS/adapters/mcp/adapter.py` is fail-closed scaffolding. Status: not production-ready.

## Recommended machine workflow

For automated assessment or implementation guidance:

1. Load `ai-safe2.manifest.json`.
2. Load the 161-control core dataset.
3. Determine the applicable enforcement plane and ACT context.
4. If MCP applies, load the 19-control CP.5.MCP profile overlay.
5. Resolve human-readable control detail through the paths identified in the manifest.
6. Use `scanner/` for static evidence where applicable, but do not equate scanner coverage with full framework conformance.
7. Use `challenges/` for falsification evidence and keep challenge maturity separate from framework/profile conformance.
8. Preserve source version and implementation provenance in generated evidence.

## Useful entry points

- Framework: `README.md`
- Cross-Pillar Governance: `00-cross-pillar/README.md`
- MCP profile: `00-cross-pillar/cp5_mcp_server_security.md`
- AISM: `AISM/README.md`
- NEXUS: `NEXUS/README.md`
- Scanner: `scanner/README.md`
- Examples: `examples/README.md`
- Research: `research/README.md`
- Challenge Lab: `challenges/README.md`
- Repository UX contract: `docs/REPOSITORY-UX-STANDARD.md`
- Reusable GitHub release-note template: `.github/RELEASE_TEMPLATE.md`

When a machine-readable field and prose appear to conflict, do not silently guess. Preserve the conflict in the output and prefer the current v3.1 normative document identified by the manifest for interpretation.
