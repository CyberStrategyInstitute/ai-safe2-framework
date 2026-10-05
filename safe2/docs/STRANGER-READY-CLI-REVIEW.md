# AI SAFE² CLI Stranger-Ready Review

Review date: 2026-09-05<br>
Scope: local `ai-safe2` CLI package and repository integration surfaces<br>
Source rubric: user-supplied Stranger-Ready Deployment Checklist

## Decision

**GO for public beta distribution of the local CLI and reference examples.**

This is not approval of a hosted service. The repository does not provide user
accounts, payments, webhooks, shared OAuth connections, or a multi-tenant data
store. Hosted-product checks are therefore `NOT APPLICABLE`, not silently
passed. Checks requiring a real stranger, external service, or production
release remain `CANNOT VERIFY` until that environment exists.

## Gate 1: Understand it

| Item | Result | Evidence or required follow-up |
|---|---|---|
| 1.1 | CANNOT VERIFY | Conduct a timed cold-read with at least five people who have not seen the repository. |
| 1.2 | PASS | `pyproject.toml` describes an agent-facing governance, evidence, and assessment CLI; `safe2/README.md` maps concrete commands to outputs. |
| 1.3 | CANNOT VERIFY | Requires the cold-read exercise with branding hidden. |
| 1.4 | NOT APPLICABLE | This release is a repository and CLI package, not a product landing-page launch. |
| 1.5 | PASS | Root onboarding directs users to one CLI entry point, `safe2`, with examples and machine workflow links. |
| 1.6 | NOT APPLICABLE | No hosted visual landing page is part of this release. |
| 1.7 | PASS | The documentation consistently takes an evidence-before-claims, human-authority-retained position. |
| 1.8 | NOT APPLICABLE | No generated marketing hero or application shell ships with the CLI. |

## Gate 2: Trust it

| Item | Result | Evidence or required follow-up |
|---|---|---|
| 2.1 | PASS | `examples/environment-decision-card/` generates real Markdown and HTML output from an executable scenario. |
| 2.2 | NOT APPLICABLE | Testimonials are not required to establish correctness of an open-source CLI. Do not invent one. |
| 2.3 | PASS | `SECURITY.md`, `SUPPORT.md`, and `LICENSE` are repository-root trust surfaces. |
| 2.4 | PASS | Package metadata names Cyber Strategy Institute as publisher and links its repository and homepage. |
| 2.5 | PASS | The environment example performs baseline, controlled drift, policy denial, Decision Cards, friction evidence, and manifest validation. |
| 2.6 | PASS / HUMAN PENDING | Public issues and the security address are documented; delivery and human response require an external test. |
| 2.7 | NOT APPLICABLE | The repository and CLI are open source; there is no self-service paid tier in scope. |
| 2.8–2.9 | NOT APPLICABLE | The local CLI does not broker user OAuth accounts. Remote tokens are caller-supplied and require HTTPS. |
| 2.10 | PASS | Repository test, lint, UX, manifest, project, MCP, and skill scans were executed. Scanner self-matches are retained as findings, not misreported as product vulnerabilities or suppressed. |
| 2.11 | PASS WITH BOUNDARY | Credential transport, untrusted output, traversal bounds, schema validation, symlinks, malformed provider data, and fail-closed policy behavior have regressions. Live external infrastructure remains separate. |
| 2.12–2.13 | NOT APPLICABLE | No account/session tenancy exists in the CLI package. These become blocking if a hosted control plane is introduced. |

## Gate 3: Break it

| Item | Result | Evidence or required follow-up |
|---|---|---|
| 3.1 | PASS | Provider failures and malformed NEXUS/SkillSpector evidence produce typed failures without fabricated success. |
| 3.2–3.4 | NOT APPLICABLE | The CLI has no browser transaction, webhook, or payment workflow. |
| 3.5 | PASS | Permission/read failures become explicit coverage gaps, `HOLD`, controlled CLI errors, or failed evidence. |
| 3.6 | PASS | Remote probes and provider processes have timeouts; bounded subprocess collection kills timed-out or output-flooding children. |
| 3.7–3.7a | PASS | Empty evidence surfaces are represented explicitly and documentation supplies the next commands and examples. |
| 3.8 | PASS WITH BOUNDARY | Evidence files are independently sealed and manifests bind immutable digests. Full hostile filesystem swap resistance remains future hardening. |
| 3.9 | PASS / EXTERNAL MATRIX PENDING | Clean-wheel execution outside the checkout has passed. Linux/macOS, real SSH/WSL, and live SkillSpector remain release-matrix work. |

## Gate 4: Observe it

| Item | Result | Evidence or required follow-up |
|---|---|---|
| 4.1 | PASS | JSON artifacts, friction JSONL, policy decisions, schema validation, and run manifests provide structured evidence. |
| 4.2 | PASS WITH RETENTION DEPENDENCY | Baselines, drift, sealed events, and manifests reconstruct recorded runs when operators retain them. The CLI does not silently upload telemetry. |
| 4.3 | PASS | Failures carry typed categories, validation state, artifact path, target status, or policy reason. |
| 4.4 | CANNOT VERIFY | Run a cold recovery exercise with a first-time user using only CLI errors, Quickstart, and Support documentation. |
| 4.5 | PASS | The repository contains versioned release/evolution records, executable examples, schemas, and a comprehensive automated suite. |

## Gate 5: Come back

| Item | Result | Evidence or required follow-up |
|---|---|---|
| 5.1–5.2 | CANNOT VERIFY | Product owner must retain anonymized evidence of user interviews and a recurring feedback cadence. Do not put private interview data in this repository. |
| 5.3 | PASS | The CLI is composable from shells, CI, agent harnesses, JSON consumers, SSH, WSL, and evidence-provider adapters. |
| 5.4 | PASS | The canonical baseline-to-policy-to-card-to-manifest workflow is executable in pytest, CI, pre-publish, and installed-wheel verification. |
| 5.5 | NOT APPLICABLE TO LOCAL CLI | There is no central usage telemetry by design. If hosted distribution is added, opt-in privacy-preserving health signals and accountable review become mandatory. |

## Remaining assurance plan

These items improve assurance without overstating what local tests prove:

1. **Cold-user validation:** five first-use sessions and one failure-recovery
   session, recording only task completion, time, confusing step, and recovery
   outcome.
2. **Platform matrix:** Python 3.11–3.13 on Windows, Ubuntu, and macOS; retain
   workflow artifacts for install, schema discovery, and executable example.
3. **Integration matrix:** live, authorized tests for WSL, SSH, NEXUS runtime,
   and NVIDIA SkillSpector with sanitized evidence fixtures.
4. **Release provenance:** verify PyPI trusted publishing during release and add
   signed artifact/SBOM provenance when the release process supports it.
5. **Filesystem hardening:** use atomic replace and no-follow/open-handle checks
   for evidence and baseline paths where platform support permits.
6. **Longitudinal value:** use the friction taxonomy to measure recurring user
   failure categories and prioritize improvements without collecting prompts,
   credentials, or customer content.

## Using AI SAFE² to evaluate AI SAFE²

Self-evaluation is useful only when scope and conflicts remain visible. It is
not self-certification. The repeatable loop is:

1. `safe2 doctor` inventories the actual execution environment and separates
   observed facts from assumptions and coverage gaps.
2. Project, MCP, and skill scans provide static candidate evidence. Findings
   require contextual triage; scanner output is not conformance evidence by
   itself.
3. NEXUS, SkillSpector, runtime probes, tests, and other providers retain their
   source contract and provenance as independent evidence.
4. `safe2 evidence manifest` binds the artifacts and exposes unsupported,
   invalid, or integrity-invalid inputs.
5. AISM and environment policy evaluate the supplied evidence without changing
   the 161-control framework or inventing missing evidence.
6. Decision Cards present facts, assumptions, conflicts, impacts, alternatives,
   recommendations, ownership gaps, and exit criteria to accountable humans.
7. Baselines, drift, and friction records make the next assessment comparable
   to the last one.

The final repository self-check observed four local harness indicators and
returned `REVIEW` for the workstation because persistent state, scheduled
operations, and three harness-specific project policies required confirmation.
Those are host-scope governance findings, not defects in the distributable
package. The strict skill gate returned `APPROVE` with no findings.

A static MCP scan of `safe2/` returned one high candidate because
`discovery/config.py` includes `token` in a list of secret-like key names. Code
review confirmed that the module redacts and counts matching configuration
names; it does not forward OAuth tokens. The candidate is retained as a
documented contextual false positive. This demonstrates why AI SAFE² preserves
scanner evidence and human adjudication separately.

| Quality objective | AI SAFE² evaluation surface | Release evidence |
|---|---|---|
| Security | P1, CP.5.MCP, gates, provider boundaries | Credential transport refusal, bounded readers/processes, schema and integrity tests |
| Usability | P2, P4, P5, Decision Cards, friction evidence | Executable examples, stable exit codes, facts/assumptions/actions, support paths |
| Adaptability | CP.5 profiles, enforcement planes, versioned contracts | Provider-neutral schemas, WSL/SSH/local targets, independent component versions |
| Modularity | CP.4/CP.9 governance and evidence provenance | Discovery, posture, policy, cards, manifests, AISM, NEXUS, and scanners remain separable |
| Accountability | CP.6, CP.8, CP.10 and AISM decision ownership | Conflicts force review; owners, limitations, exit criteria, and human authority remain explicit |

No checklist result establishes certification, organizational conformance, or
universal safety. It establishes a reproducible, evidence-bounded beta release
decision for the scoped CLI package.
