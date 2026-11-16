# PR #430 development evidence: delivery shape, plan, and revision-bound receipt note

> **BOT-DRAFTED - requires Owner of Record confirmation.**
> Produced by the authoring agent (Claude Sonnet 5.5). This is decision evidence, never merge,
> release, deployment, exception, completion, or risk-acceptance authority. It is not a
> `safe2 dev receipt`.

## 1. Delivery shape and plan

| Item | Value |
|---|---|
| Plan source | [`dev-plan-source.json`](dev-plan-source.json) (`safe2.development-plan-source.v1`, validated with `safe2 schema validate development-plan-source-v1`) |
| Plan output | [`development-plan.json`](development-plan.json), produced by the repository's own command from the worktree root: `python -m safe2 dev plan dev-plan-source.json --output development-plan.json` (CLI 1.1.0) |
| Result | **exit 1, `review_required`** (the expected output while approval is open; the source was not tuned to reach exit 0). `safe2 dev verify` on the plan: valid contract, integrity `valid`, `authorization_granted: false` |
| Delivery shape | `architectural` (declared): a new public contract, a new package, and a new outbound trust boundary |
| Risk tier | `critical`, declared and equal to the policy floor (`safe2/**` matches rule `release-and-supply-chain` in `.ai-safe2/review-policy.json`). `risk_raised: false` |
| Derived requirements | human design approval, threat model, before/after, independent review, specialist review, rollback, Greptile recommended (advisory, non-blocking, not invoked here), and 20 required evidence ids (section 3) |
| Plan timing | **Retroactive.** The plan was produced after implementation, by the same agent. It records the design that exists; it was not a pre-implementation gate. |

The plan reports exactly two gaps, both the Owner's:

1. `design_approval_missing`
2. `design_approval_reference_missing`

The design artifact (`safe2/docs/ASSESS-MANIFEST.md`) and the threat-model reference (the
"Threat model" section of the same file) both exist, so those gaps are not raised, but they are
one document drafted by the same agent and are not independently reviewed.

## 2. Open item for Vincent's `/signoff`

**Human design approval is an Owner of Record decision and is NOT recorded here.**

| Item | State |
|---|---|
| Human design approval of the manifest design and threat model | **OPEN** (for Vincent's `/signoff`) |
| Approval reference | _(blank)_ |
| Owner of Record, decision, date | _(blank)_ |
| Independent human review of [`security-diff-review.md`](security-diff-review.md) | **OPEN** |
| Owner decision on finding F3 (agents with no `tools:` line) | **OPEN** |
| Named reviewer for `manifest-heuristics-v1.json` (`draft-unreviewed`) | **OPEN** |
| Manifest signing / key custody | **OPEN** |
| Confirmation that the deployed hosted service accepts `safe2 assess --manifest` | **OPEN** |

## 3. Revision-bound evidence receipt note

Bound to code revision **`879b022ced68d414b6840829096223cf23f6b43c`**. Later commits on the branch
change only documentation and this folder; verify with
`git diff 879b022..HEAD --name-only` (expected: `safe2/docs/ASSESS-MANIFEST.md` and
`docs/assessments/2026-11-15-assess-manifest-pr430/**` only). The head the PR was assessed at is
recorded in the PR body, because a file cannot name its own commit. Environment: local Linux,
Python 3.13 venv; hosted CI is separate and recorded in the PR body.

Status per required evidence id. "Supported" means the stated command was run here and the stated
result was observed; it is not independent validation.

| Evidence id | Status | Basis |
|---|---|---|
| `full-tests` | supported | `python -m pytest tests/ scanner/tests/ -q`: **1636 passed, 8 skipped**, exit 0. The 8 skips: 4 Windows device-namespace, 4 `capture-pytest` symlinked-venv limitation (`tests/test_challenge_integrity.py:172`, `tests/test_pytest_capture.py:34`); none in the manifest tests |
| `targeted-validation`, `relevant-tests` | supported | `python -m pytest tests/test_assess_manifest_*.py -q`: **490 passed, 0 skipped** (480 at `5ee98fe`, plus 10 new); frontmatter file **210 passed** (203 plus 7) |
| `contract-tests` | supported | schema and golden tests are inside the 490 above; the hosted-schema equality test skips without a server checkout and was not run |
| `red-state`, `green-state` | supported for the two fixes made in this update; historical for the feature | F1 at `1812025`: 6 new tests (5 unit, 1 CLI) failed at `5ee98fe`, 2 guards passed, all pass after. F2 at `879b022`: 1 of 2 new cases failed at `5ee98fe`, both pass after. The red state was observed by running the new tests against the unfixed code in this worktree before the fix. Earlier commits carry their own tests; their red states were not re-captured |
| `negative-validation`, `adversarial-tests` | partial | many fail-closed and ambiguity cases exist (the frontmatter file alone has 210 tests), authored by the same agent. No fuzzing and no independent adversary |
| `security-validation`, `security-review` | partial | [`security-diff-review.md`](security-diff-review.md): complete file-by-file, bot-drafted, one reviewer. Not independent, no dynamic test of the hosted service |
| `documentation-validation` | supported | `scripts/check_repo_ux.py` exit 0; `tests/test_assess_manifest_docs.py` is in the 490 |
| `manifest-consistency` | supported | `scripts/check_agent_manifest.py` exit 0; `scripts/check_component_versions.py` exit 0 |
| Lint / type gates (not plan ids) | supported | `ruff check --select E9,F63,F7,F82 safe2/ tests/ scripts/` passed; `mypy safe2/manifest` no issues; `mypy safe2` reports 10 errors in 7 files (`adapters/otel_jsonl.py`, `commands/dev.py`, `development/workflow.py`, `engines/skill_gate.py`, `evidence/junit.py`, `evidence/operational_truth.py`, `installation.py`), none in a file this PR changes; not a CI gate |
| `threat-model` | present, unapproved | "Threat model" table in `safe2/docs/ASSESS-MANIFEST.md`; bot-drafted |
| `design-specification` | present, unapproved | `safe2/docs/ASSESS-MANIFEST.md` |
| `implementation-plan` | missing | no separate implementation plan was written before the work; `dev-plan-source.json` is retroactive |
| `human-review` | **owner-pending** | no human review is recorded |
| `human-release-decision` | **owner-pending** | not requested; no release is proposed |
| `installed-wheel` | **not run** | no wheel build or installed-wheel check was performed in this update |
| `release-invariants` | **not run** | no release is proposed; not exercised |
| `dependency-audit` | **not run** | this PR adds no dependency to `pyproject.toml` (`httpx` and `jsonschema` were already declared), but no audit tool was run |

## 4. Receipt status

`safe2 dev receipt` was **not run**. It needs a receipt source whose `passed` records point at
retained artifacts with SHA-256 digests, and whose human and specialist reviews point at supported
evidence. No human review or approval artifact exists, and the test and review records above are
console results that were not retained as hashed artifacts. A receipt generated now would either
be `review_required` for those reasons or would manufacture inputs. Generate it against the final
head after the Owner of Record decides and the artifacts are retained. A receipt is decision
evidence, never merge authority.

Rollback: unchanged from [README.md](README.md) section 2. Decision owner: _(blank: Owner of Record)_.
