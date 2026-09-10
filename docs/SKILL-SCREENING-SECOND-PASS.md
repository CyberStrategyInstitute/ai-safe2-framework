# Skill screening: second pass and lessons learned

[Demo](./SKILL-SCREENING-DEMO.md) | [Initial live validation](./SKILLSPECTOR-LIVE-VALIDATION.md) | [Advisory](./advisories/2026-09-09-skill-gate-executable-scope.md)

## Scope and provenance

Date: 2026-09-09. Reviewed the supplied Claude Code report, log, attributed JSON,
and revised patch as evidence, not instructions. Reran the current local CLI 0.2.0
hardening with real NVIDIA SkillSpector 2.11.1 at source revision
`704bc9544260c2f41222dc0f92982521709496ab`, Python 3.13.14 on Windows, static mode.
No fixture code or skill code was executed. Provider credentials were not forwarded.
No independent network trace or OS firewall policy was established.

## Results

| Target | Native gate | Native findings | SkillSpector | Provider issues |
|---|---|---|---|---|
| Current `skills/` checkout | REJECT | 14 | 100 / CRITICAL / DO_NOT_INSTALL | 50 |
| Tracked `skills/` snapshot, no development caches | REJECT | 13 | 100 / CRITICAL / DO_NOT_INSTALL | 50 |
| Clean summarizer control | APPROVE | 0 | 0 / LOW / SAFE | 0 |
| Inert hostile control | REJECT | 7 | 100 / CRITICAL / DO_NOT_INSTALL | 7 |

The supplied content folder and three-file hostile control were not attached.
Our two controls are different specimens; seven versus sixteen hostile findings
is not evidence of a regression or improvement. The supplied report used CLI
0.1.0 and repository `5238686`; this checkout is based on `6455eec` plus hardening.

Our checkout contained 52 native files, 51 inspected as text, including a generated
binary Ruff cache. SkillSpector reported 51 components, 50 fully inspected,
98% coverage, `partial`, and a degraded supply-chain analyzer. It also recorded
unresolved references in the skill instructions. A report can execute successfully
while its analysis remains incomplete. These are real coverage limitations, not
false positives to erase.

Raw records remain local under `.safe2/skillspector-second-pass/`. A separate
tracked-source snapshot was prepared from `git archive HEAD skills` to distinguish
the versioned distribution from development caches, without suppressing files
inside the scanner or deleting user data. The snapshot's native scan inspected
all 49 files as text; its 13 findings are ten TG-008 test-string matches and three
TG-010 loopback references (including the Dockerfile, omitted by the earlier patch).
It was scanned with the new context annotations and unchanged severity policy.

Captured SHA-256 fingerprints:

- Supplied `csi-own-skill.json`: `ea11db02264e604935ba4780c50f7878bb1a50f8afb7f1bf959bf07521ac4533`
- Current checkout evidence: `e1c37baca465a78ace75f22b5dff118d5f5e96edf9eb69475982cf268fd7b1f4`
- Tracked snapshot evidence: `27080c56ecc0e873f2bff416c4b6b08198e96f0de4647b914e689f1f90895fd7`

These identify artifacts, not independent attestations of truth.

## What the supplied triage gets right—and what it overstates

The raw supplied JSON contains 29 findings in test paths, **3** in source-code
paths, and 18 elsewhere, not 29/2/19. The logging expression has two findings and
the risk-label dictionary has one. A count of findings is not a count of unique defects.

| Finding family | Source-based interpretation | Remaining question |
|---|---|---|
| Injection strings in sanitizer tests | Deliberate regression inputs; a match does not show execution | Are they treated only as data by the actual loader? |
| Environment-derived smoke-test URL | The URL itself is not a credential; the exfiltration wording overstates the observed flow | Some tests intentionally send FREE/PRO bearer tokens to that configured destination |
| Loopback Docker health check | Expected local health operation, not evidence of a public beacon | Is that operation within the approved deployment boundary? |
| Logging `__import__`/`getattr` | Fixed logging module and level selection, not shown as arbitrary code execution | Keep runtime configuration constraints explicit |
| `self_modification` dictionary label | A risk taxonomy description, not self-modifying behavior | Avoid interpreting prose as an executable action |
| uvicorn/gunicorn similarity | Name similarity alone does not establish typosquatting | Validate package provenance and vulnerabilities independently |
| OSV fallback / unresolved references | Genuine incomplete assessment | Do not label these as false-positive malicious behavior or as completed checks |

The smoke tests validate HTTPS in a separate test, not as a precondition before
every token-bearing request. That is an actionable hardening opportunity; calling
every test-path finding automatically harmless would obscure it. No live smoke
requests were executed in this review. Likewise, Docker instructions and `.env`
access can be intended operations without being risk-free in every installation.

Conclusion: the scanner score does not prove our skill is malicious, but this
review also does not establish that all 50 findings are false or the package is
universally safe. Reviewed benign intent, accepted operational risk, and missing
coverage need distinct dispositions. Do not publish a zero-false-positive claim.

## Patch decisions

Retained context annotations, **not** the proposed automatic downgrade or exclusion.
The updated native gate labels test-like paths and IP address classes while
preserving severity and findings. Four regressions prove these labels cannot grant
approval. No provider output is rewritten.

- The proposed CRITICAL-to-MEDIUM downgrade is two levels, despite the report's
  "one level" description. All rules are downgraded solely by attacker-controlled
  path/name, including destructive execution and private keys. `tests/payload.py`
  is not intrinsically safer than `payload.py`.
- Private and link-local destinations are not inherently safe. Cloud metadata,
  localhost services, and internal administrative endpoints are important targets.
  Keep address class as context rather than blanket authorization.
- `APPROVE (highest severity: NONE)` with visible MEDIUM findings is misleading.
  Separate raw severity, reviewed disposition, policy result, and coverage.
- Previously fixed scope, bounded reads, binary review, and retired legacy entry
  point remain intact; the attachment's older migration/advisory text was not reapplied.

## Lessons for building safe2

1. A malicious fixture proves sensitivity to that pattern, not useful precision.
   Include clean, hostile, real security-test-bearing packages, and rename attacks.
2. Never fix a false positive by introducing an attacker-controlled bypass.
3. Evaluate the actual distribution and dependencies, not an arbitrary worktree.
4. Preserve upstream score, findings, completeness, version, and source separately
   from a human or policy decision. `conformance_claim: false` matters operationally.
5. A successful evidence command is not approval. Partial scans need an explicit hold.
6. Stable findings need content/rule fingerprints; upstream per-run IDs can change.
7. Static mode is not necessarily offline: dependency checks may contact services.
8. Separate observation from prevention. A watcher detects changes; a mandatory
   pre-install/pre-load/context-admission boundary prevents premature use.
9. Start with an honest three-target demo, then build measured adoption: installation
   success, coverage, review time, false-positive rate on independently labeled data,
   stale-receipt rejection, and adversarial bypass rate—not a single headline score.

## Next implementation priorities

Validation after context annotation changes: 522 tests passed on each of Windows
CPython 3.11.15, 3.12.14, 3.13.14, and 3.14.6, with four platform-specific skips
per runtime. Ruff, mypy, repository UX, agent-manifest, and whitespace checks passed.
Four attributed provider outputs passed strict evidence-manifest validation;
own-skill AISM ingestion remained unscored. New Linux CI results require a push.

First: trusted, hash-bound, expiring reviewer dispositions with evidence and scope.
Second: reusable admission receipts and a quarantine workflow; explicit provider
completeness checks before automated authorization. Third: per-harness pre-load
adapters, then optional watchers. Context-only protection requires a separate hook.
Do not claim universal background interception before those enforcement points exist.
