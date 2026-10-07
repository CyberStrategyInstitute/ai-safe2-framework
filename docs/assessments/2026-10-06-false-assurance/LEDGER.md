# Ledger: False-Assurance Hardening

Append-only. Newest entry at the bottom. Each entry: what happened, evidence, next step.

---

## 2026-10-06 E1: Initial findings (pre-battery)

Installed safe2 1.0.0 and nexus-a2a-sdk 0.5.0 from `main` (`83de4a8`). Probed the MCP
scorer with a hostile local server whose tool description instructs credential theft.
It scored 87/100 "Acceptable", earned the badge, and passed `safe2 gate mcp --ci-fail-below 70`.
It did this with a self-published attestation file, an empty OAuth metadata document,
and a 429 response after 3 requests. An honest server scored 63.

**Evidence:** reproduced by battery cases `MCP score:*` and `gate mcp URL:*`.
**Next:** full four-area battery.

## 2026-10-06 E2: First fix pass (session context later lost)

An earlier pass at the request built a battery and pushed three commits to this branch:
- `47c2dc8` fixed the MCP knowledge server (M1-M7).
- `06e523a` fixed the MCP toolkit score, scan, and wrap (T1-T7).
- `8f3d038` fixed the skill trust gate and the project gate (S1, C1, C2).

It also left an uncommitted Rego v1 rewrite. The chat context for that pass was lost.
Its commit messages are the record.

**Lesson:** this is why the ledger, state file, and snapshots now live in the repo.

## 2026-10-06 E3: Battery rebuilt and re-run independently

The earlier pass was not trusted. The battery was rebuilt (126 cases) and run against
untouched `main` and the branch.

| Area | main `83de4a8` | branch `8f3d038` + WIP |
|---|---|---|
| SKILL | 9 / 18 | 19 / 8 |
| MCP | 2 / 14 | 20 / 0 |
| CLI | 24 / 1 | 25 / 0 |
| NEXUS | 24 / 30 | 30 / 24 |

Four harness defects were corrected, each because the product was right:
- `feedback record --outcome verified_done` without evidence correctly exits 1.
- `--strict` correctly REJECTs a document that quotes an attack phrase.
- An HTTP probe path was wrong.
- `skills/` root rejection is a packaging boundary issue, not a gate defect.

**New findings on main:**
- The OPA policies do not compile on OPA 1.x.
- `authorize_tool_call` is undefined for 9 of 13 inputs.
- A memory scope downgrade bypasses the mandate.
- Explicit deny rules never gate `allow`.
- `deny_reason` is always empty.
- The compose OPA mount points at a non-existent directory.
- Guardian allows 15 of 26 evasions.
- AgBOM tamper and rug-pull go undetected.

**Next:** NEXUS fixes.

## 2026-10-06 E4: NEXUS OPA fixed, checkpoint pushed

Commit `f3ecea0`, pushed:
- Rego v1 on all three policies.
- Authz is always defined, and the most restrictive scope wins.
- Explicit deny now gates `allow`.
- Deny reasons are populated.
- AISM loads.
- CI covers `NEXUS/opa` on OPA 0.65 and 1.4.2.

**Evidence:**
- `opa test`: 16/16 on both OPA versions. Against main's authz policy, 8 of 11 authz tests fail.
- APay rewrite differential: 873/873 identical decisions, zero looser.

**Next:** modular battery in the repo, ledger, and snapshots (owner request), then Guardian and AgBOM.

## 2026-10-06 E5: Battery moved into repo, durability files added

- Battery moved into `tests/battery/` (core plus one module per area). It writes
  per-area result files and supports `--resume` and `--areas`.
- Hostile code is stored inert (`.fixture` suffix), with credentials synthesized at run
  time. The TLS cert is generated per run.
- Pytest collects 0 files from it.
- Added `RUNBOOK.md`, `STATE.json`, and this ledger.

**Next:** freeze before and after snapshots, push, then Guardian (N-G) and AgBOM (N-A).

## 2026-10-06 E6 - Snapshots frozen

| Snapshot | Revision | PASS | FAIL | NOT_RUN | INFO |
|---|---|---|---|---|---|
| `before-83de4a8` | main | 61 | 63 | 1 | 1 |
| `after-225f45b` | branch | 101 | 27 | 0 | 1 |

Remaining 27: SKILL docs drift (6), NEXUS Guardian (15), AgBOM (5), compose OPA mount (1).
Repo semgrep rules clean on full tree. Pytest collects 0 battery files.
**Next:** nexus-compose, nexus-guardian, nexus-agbom; snapshot after each.

## 2026-10-06 E7: Compose and Guardian fixed

- `5af8409` compose: mounts now resolve to `NEXUS/opa` and `NEXUS/schemas`
  (`docker compose config`). The OPA healthcheck uses `/opa eval --fail`: exit 0
  with policies, 1 with an empty mount, 2 with a broken policy. **Limit:** no Docker
  daemon here, so there was no live `compose up`.
- `904e289` Guardian:
  - Arguments are normalized before matching, and five built-in detectors were added.
  - HEAR reasoning has a quality floor.
  - An undeclared tier is treated as ACT-4. This breaks callers that omit
    `act_tier`; the opt-out is documented in the CHANGELOG.
  - Red/green: 24/33 new tests fail on main, 33/33 pass on the branch. SDK suite
    590/590. Example decisions are unchanged.

**Next:** AgBOM.

## 2026-10-06 E8: NEXUS complete

- `04f6192` AgBOM: chain verification recomputes content, snapshots are isolated, and a
  rug pull is quarantined with release only by explicit approval. Red/green: 7/9 → 9/9.
  Hashes are byte-identical to v0.3 for components never quarantined.
- `4f2cff2` Memory Vaccine: stub mode now labels drift as unmeasured (`drift_method`)
  and warns. Red/green: 4/4.
- `7b85788` nexus-score: checks are now behavioral, with a NOT ASSESSED state and
  meaningful exit codes.
  - **Headline:** main's own checker printed "10/10 verified, all v0.3 controls
    satisfied". Run against main, the behavioral checker gives 7 verified, 3 failed.
  - New battery case: the scorer's claims must agree with battery evidence.
- Harness: Guardian benign cases now declare `act_tier=1`, because an omitted tier
  is fail-closed by design and has its own case. Guardian battery: 27/27 on the
  branch, 11/27 on main.

**Next:** docs drift, then full gates, after snapshot, and draft PR.

## 2026-10-06 E9: Docs, CI, secrets, gates. Ready for PR.

- `2dac2ff` **New bug found by the behavioral scorer:** with `guardian_url` set and no
  `httpx`, the remote Guardian silently evaluated the default inline policy, so
  FAIL_CLOSED never engaged. It now fails per its configured mode. 2 red tests fixed.
- `3353be4` docs: retired a stale `skills/` redirect copy with broken links, and
  documented Guardian behavior and OPA tests in the NEXUS README. The six v3.0 skill
  surfaces were deliberately not relabeled: their content is v3.0 (decision D3).
- `517357f` harness: the skills checker now reads negation and historical context.
  Three false structural fails are gone; main still shows its one real defect.
- `5b38495` CI:
  - The compliance job installs a pinned, sha256-verified OPA.
  - A new `mcp-server` job runs `skills/mcp` tests via the documented install.
  - `opa.yml` verifies checksums.
  - Both jobs were simulated from clean venvs.
- `b24d040` gitleaks (full history): three fixture literals from this branch were fixed
  at source and baselined for their historical commits. Result: no leaks.
- `bfe324b` `gates.sh`, the local CI mirror: **30/30 PASS**.

**Final battery, identical harness (`bfe324b`):**

| | PASS | FAIL | NOT_RUN | INFO |
|---|---|---|---|---|
| main `83de4a8` | 61 | 60 | 1 | 1 |
| branch `bfe324b` | 124 | 0 | 0 | 1 |

**Limits:**
- There was no live `docker compose up`, because no daemon was available.
- Hosted CI results are pending until the PR runs.
- All results are self-assessment; none has been independently reviewed.

**Next:** draft PR, then owner decisions D1-D4.

## 2026-10-07 E10: Draft PR #393 open, hosted CI green

- **PR #393 opened via the GitHub REST API.** The session's GitHub access had worked all
  along, which an earlier ledger entry and the PR notes wrongly said it did not.
  `gh auth status` reports the proxied token as invalid, and `gh pr create` uses
  GraphQL, which Claude Code sessions block. `gh api -X POST repos/{o}/{r}/pulls` works.
- **First hosted run:** CodeQL raised 2 high alerts in the battery harness. Both were
  fixed in `e91ee9a`:
  - The TLS test server lacked a TLS 1.2 minimum.
  - The placeholder-fill variable name tripped the sensitive-data heuristic.
- **Head `0368490`:** 36 checks pass. 4 were skipped: Greptile and PR-Agent are advisory
  and skip on drafts, and the trust-gate scan skips because no `SKILL.md` changed.
  CodeQL reports no new alerts.

**Next:** owner decisions D1, D3, D4. Greptile review once the PR is ready-for-review.

## 2026-10-07 E11: Owner decisions implemented; PR #393 ready for owner

- `c59cc40` **D1:** the canonical skill moved to `skills/ai-safe2-secure-build-copilot/`
  and gates APPROVE under `--strict`. No `SKILL.md` redirect was left at `skills/`,
  because CI gates the directory of any changed `SKILL.md`.
- `8c71410` **D3:** six surfaces retagged to v3.1, with a v3.1 delta and Eval 11.
  - `21a8333`: the hosted trust gate blocked the Codex package because it had no
    `SKILL-CARD.md`, a gap that predates this PR. The card was added and validates at 100%.
- `e0637f7` CI: `ci.yml` had the repository default token scope and is now
  `contents: read`. `opa.yml`'s checkout is SHA-pinned.
- `98598ed` **Harness defect (mine):** fixed ports let a stale branch knowledge server answer
  for main. The `before-83de4a8-harness-bfe324b` snapshot recorded a false PASS for
  main's HTTP case. Ports are now kernel-assigned and checked, and an occupied port
  makes the case NOT_RUN. That snapshot is marked invalid in STATE.
- **Final, same harness:**

  | | PASS | FAIL | NOT_RUN |
  |---|---|---|---|
  | main | 60 | 65 | 1 |
  | branch `21a8333` | 126 | 0 | 0 |

  62 cases red→green; 0 regressions.
- **Red/green:** all 13 new test files fail on main and pass here (`receipt/evidence/red-green.md`).
- **Gates:** 30/30. Hosted CI: 39 success, 2 advisory skips, CodeQL no new alerts.
- **Receipt** (`safe2 dev`): integrity valid, `review_required`. 23 of 27 evidence items
  are supported; human, codeowner and security review and the release decision belong to the owner.
- **D4:** the interim floor is in #393. Registry-bound tiers come as a follow-up PR.

**Next:** the owner merges #393. Then the D4 follow-up PR.

## 2026-10-07 E12: PR #393 ready for review

- Marked ready via the CCR route; the PR body was replaced with `PR_DESCRIPTION.md`.
- Hosted CI on head: every deterministic check passed. The "Decision evidence" run cancelled
  by the ready_for_review event was superseded by a successful run.
- **AI reviewers, recorded rather than assumed:**
  - Greptile posted no review; its advisory status check passes by design.
  - PR-Agent's advisory check failed: no substantive review was published by its model
    provider.
  - Neither counts as approval or as a finding. The receipt already lists both as unavailable.
- Both CodeQL review threads from the first run are resolved (fixed in `e91ee9a`).
- GitHub reports the PR `mergeable`, state `unstable` because the advisory check is red.

**Next:** the owner reviews and merges. Then the D4 follow-up PR.

## 2026-10-07 E13: Correction to E12

On `82ed851` PR-Agent published a bounded review: one hunk, `ci.yml` permissions, with
"no actionable issue". Its first run had published nothing. Greptile still posted no
review. At `82ed851` all 41 checks pass and the PR is `mergeable: clean`.

## 2026-10-07 E14: D4 follow-up, PR #394 (stacked on #393)

- `5bc3c03` on `feat/aim-bound-act-tier` adds registry-bound ACT tiers (AIM v0.3). The IETF
  draft section 3.1.1 already specified them, and the schema file the draft cites did not exist.
- Also closes the same bug class in OPA:
  - A `config_change` that omitted `act_tier` skipped the approval; on #393's head it returned
    `allow=true`.
  - An agent with no tier passed I-4 with no kill path.
- **Red on #393's head:** the Python test file fails at collection and the Rego tests fail to
  type-check. **Green here:** 18/18, `opa test` 25/25 on 0.65 and 1.4.2, SDK 626/626,
  gates 30/30, battery 126/126.
- PR #394 targets the #393 branch, so only 7 hosted checks ran (most workflows filter PRs to
  `main`). Retarget #394 to `main` after #393 merges to run full CI.

**Next:** the owner merges #393 (merge commit or rebase); #394 is retargeted and reviewed.

## 2026-10-07 E15: Repository-wide consistency sweep (stacked on #393)

The owner asked whether the skills update fixed v3.0/v3.1 mismatches repo-wide. It had
not: the sweep in #393 covered `skills/` only. Branch `fix/v31-consistency-sweep`,
based on `7286925`; owner chose a separate PR, a redirect for the stale toolkit, and
a retag of the example packages.

- `0be3c6f` MCP toolkit: printed control equals emitted control; v3.1 names. New
  `test_control_citations.py` (9 red, then green) and repo-wide guard.
- `bb22cce` Release truth: SECURITY.md (CLI was `0.1.x`), manifest (`0.9.9`), AGENTS.md,
  README install fallback; `publish.yml` fails loudly on non-`v` CLI tags. Root cause
  of 1.0.0 missing from PyPI recorded. Raised by the owner's daily run.
- `4dc446b` Core retag; NEXUS current version 0.5 (was shown as v0.3 in 9 places).
- `061e64b` `examples/mcp-security-toolkit/` replaced by a redirect.
- `891a8e4` Example packages retagged; lovable `policy.yaml` parse error fixed.
- #394 `2e37be6`: AIM v0.3 schema descriptions cite v3.1.

Verification: guard clean; local gates 31/31; battery 126/0/0; example smoke results
identical before/after. Evidence: `docs/assessments/2026-10-07-version-consistency/`.

**PR:** #395 (draft). **Next:** the owner merges #393; #395 and #394 retarget to `main`. Publishing 1.0.x
to PyPI is an owner release action (recommended: v1.0.1 after #393).
