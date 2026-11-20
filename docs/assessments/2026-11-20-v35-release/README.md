# AI SAFE2 v3.5 release qualification

[Framework home](../../../README.md) | [Release notes](../../../releases/AI-SAFE2-v3.5.0.md) | [Dedicated component updates](../../POST-V35-COMPONENT-UPDATES.md)

## Scope and method

Three loops used maintainer/agent-contract, adversarial/skeptical-evaluator, and operator/release-engineer perspectives. These were review lenses used by the same assistant, with deterministic tests and hosted tools. They do not establish independent expert approval.

## Loop 1: identity, contracts and issue acceptance

The framework is identified as v3.5 across Markdown, machine metadata, generated views, CLI output and support documentation. Component publication remains separately evidenced. Review found the stale 3.1 support row and missing source-rights detail from #390. Both are corrected. C53 adds three P2.T4.4 clauses and research note 077. Totals are 173 core controls, 157 child clauses, 53 research decisions/notes, 19 MCP controls and twelve MCP child requirements.

Canonical mirrors, generated documents, source maps, navigation, current README anchors, HTML routes and release identity checks pass. Frozen v3.0/v3.1 compatibility datasets are unchanged against the integrated main baseline.

## Loop 2: adversarial and assurance boundaries

Review considered exact-action binding, replay, current conditions, inherited authority, concurrent ancestor budgets, idempotency, postconditions and evidence independence in the bounded SQLite fixture. CLI readiness remains a declared-evidence check and cannot authorize deployment. Rosetta source review and applicability are not manufactured from tags. The review found a link bug for `_ADV` control IDs; the explorer now consumes canonical generated anchors, and a regression checks every control anchor.

Hosted CodeQL flagged dynamic DOM element construction in the explorer. The helper now creates only explicitly permitted literal element names, rejects unsupported names and keeps source text in textContent. The generated page and regression test are synchronized. Two issue-reference Markdown formatting errors were also corrected.

The formal Codex Security diff service could not attach to this Windows Git worktree and returned: `Review changes requires a non-bare Git worktree with a resolvable HEAD.` The local HEAD resolves. No completed formal diff scan is claimed. Hosted CodeQL, repository guardrails, secret and dependency checks are recorded separately in the PR for the final revision.

## Loop 3: package and operator qualification

- Full local suite: 1,170 passed, eight skipped.
- MCP suite: 150 passed, eleven skipped, two deprecation warnings.
- NEXUS SDK suite: 628 passed, 22 deprecation warnings.
- Follow-up framework/explorer regression: 30 passed after the advanced-ID anchor and DOM-construction corrections.
- CLI/MCP wheels build. Cold package-local imports resolve all 173 controls, 53 decisions, 157 child clauses, 19 MCP controls and current framework status.
- Live PyPI metadata validation confirms documented published component pins. No package publication was performed.
- Exact-head hosted matrix and container build/health results are recorded in PR #433. Passing evidence is bounded by the checks actually executed.

## Release and follow-up decisions

PR #433 supplies the v3.5 update. The owner retains merge, release and deployment decisions. Core Gateway remains component v3.0 with enforcement qualification in #434. Scanner's 64 implemented detections remain separate from its 173-control catalog (#435). NEXUS, MCP enforcement, individual sovereign runtimes, component packages, workflow, source mapping and human-oversight validation have dedicated follow-ups. Unfinished implementation requests remain open; declined mechanisms receive explicit dispositions.
