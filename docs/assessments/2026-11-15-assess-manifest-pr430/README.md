# PR #430 `safe2 assess --manifest`: security review, rollback runbook, test evidence

> **BOT-DRAFTED, pending human confirmation.**
> Self-assessed by the authoring agent (Claude). Not independent validation, not a design
> approval, not a conformance claim, and not a `safe2 dev receipt`. Nothing here approves a
> merge, release, deployment, or risk acceptance.

## Decision record

| Item | State |
|---|---|
| Subject | PR #430, branch `csi/safe2-assess-pro`, 26 files changed against `main` (CLI `safe2 assess --manifest`, collector, post client, schema, docs, tests) |
| Delivery shape / risk | Delivery shape: not determined here (no shape is declared in the PR body; `safe2 dev plan` was not run). Risk: treated as **critical** because the Codex I1 finding used that route; it can send project facts to a hosted service |
| Human design approval | **Not recorded.** Pending. |
| Final revision-bound `safe2 dev receipt` | **Not produced.** See [Receipt status](#receipt-status). |
| Owner of Record decision | _(blank: for Vincent to fill in)_ |
| Decision date | _(blank)_ |

## 1. Security review of the PR diff (self-assessment)

Scope: `git diff origin/main..<assessed revision>`. Method, stated exactly: I read
`safe2/manifest/collect.py` (frontmatter and tool-list parsing, in full detail), `safe2/manifest/post.py`
(signatures, endpoint, redirect, timeout, redaction and retry code), the `safe2/secure_io.py` diff, the
top-level `safe2/docs/ASSESS-MANIFEST.md`, and the tests touched by this update. I did **not** review line
by line: `safe2/commands/assess.py` (167 lines added, 11 removed), `safe2/contracts.py`,
`safe2/manifest/heuristics.py`, `safe2/manifest/workflow.py`, the vendored schema, the heuristics data
file, or most of the other tests. The table below therefore repeats the PR's own documented claims and
the test names that exercise them, except where it says otherwise. No dynamic or adversarial testing
beyond the repository's own test suite. Plane:
`agent-to-tool` / local file collection, plus one outbound `--post` request to a hosted
endpoint. Evidence from one plane does not validate another.

| Area | Observation | Evidence | Residual risk |
|---|---|---|---|
| Consent | `--manifest` stops before any read, write, or send unless `--scan-content` and `--inspect-config` are on the command line; `--post` is a separate opt-in | `tests/test_assess_manifest_cli.py` | `--post` is per-run consent; `privacy.network_export` is not consulted (open decision 4 in `ASSESS-MANIFEST.md`) |
| Data minimisation | Manifest carries names, flags, counts, and digests; schema rejects unknown keys | schema + sentinel tests in `test_assess_manifest_collect.py`, `_cli.py`, `_schema.py` | A tool/agent name or a short `.env` digest can still expose low-entropy secrets |
| Reads | Bounded reader, symlinks rejected, `doctor` locations only; unreadable or unparseable config fails the run | `safe2/secure_io.py`, collector tests | Existing assessment steps keep their own reads |
| Fail-closed collection | Unreadable/ambiguous agent frontmatter fails collection instead of yielding a favourable flag (this update closes two gaps, see §4) | `tests/test_assess_manifest_frontmatter.py`, `_collect.py` | Hand-written frontmatter reader (no YAML dependency): it rejects rather than guesses, so valid-but-unusual YAML stops `--manifest` |
| Credential handling | `SAFE2_MCP_PRO_KEY` from environment only; never an option, file, log, or output; server echoes redacted | `safe2/manifest/post.py`, `tests/test_assess_manifest_post.py` | Same-host process-environment reader; a server that re-encodes the key before echoing it is not detected |
| Network | One POST to a fixed `https` endpoint, no redirects, size limits (1 MiB), one retry on connect failure only; collection opens no connection (tests patch `socket`) | `post.py`, post tests | A user-set `HTTPS_PROXY` routes the request. The deployed service's acceptance of the `safe2 assess --manifest` generator name is **unconfirmed** |
| Output safety | Server text stripped of control characters and truncated | post tests | None known |
| Authenticity | Manifest is **unsigned**; the server trusts `generator.name` | documented | Any client can claim to be the CLI. Signing is an open decision; no key was created |
| Flag heuristics | `manifest-heuristics-v1.json` is `draft-unreviewed` | heuristics tests | **Needs a named human reviewer** before hosted rules rely on the flags |
| Atomic write | Notes first, manifest last; failure leaves no manifest; published-but-unlinked staging file reported distinctly | `tests/test_secure_io_publish.py`, CLI tests | Leftover `.tmp` needs manual removal in the one reported case |
| Dependencies | No new third-party dependency introduced by this update; `httpx` is used by `post.py` | `pyproject.toml` unchanged by this update | Supply-chain review of the PR-wide diff not performed here |

Not covered: independent review, dynamic testing against the hosted service, fuzzing of the
frontmatter reader, a signed manifest, and any claim about hosted-service behaviour.

## 2. Rollback / recovery runbook

The feature is additive and opt-in. Nothing runs unless a user passes `--manifest`.

**Before merge (PR still draft).** Do nothing to `main`. Stop by leaving the PR draft or closing it.
Reverting is deleting the branch; no deployed artifact exists.

**After merge, before a release.** Revert the merge (or squash) commit through a new PR
(`git revert -m 1 <sha>` for a merge commit, plain `git revert <sha>` for a squash commit). The change touches `safe2/commands/assess.py`, `safe2/cli.py`,
`safe2/contracts.py`, `safe2/discovery/assets.py`, `safe2/secure_io.py`, and adds
`safe2/manifest/`, one schema, one heuristics file, docs, and tests. Edits to existing modules, checked
against `git diff origin/main`: the `assess` command (registration renamed from `assess_project` to
`assess_command`, plus the new options; its body diff was not reviewed line by line), an optional
`extra_classifier` parameter in `safe2/discovery/assets.py` (default off, so existing inventories are unchanged),
one schema-registry entry in `safe2/contracts.py`, a `PublishedCleanupError` subclass of `OSError` in
`safe2/secure_io.py`, and doc paragraphs. Anything else changed in `assess.py` is not confirmed here.

**After a CLI release.** Publish a fixed or reverted version through the normal release owner; do
not delete or overwrite a published package version. Users can stop using the feature without a
release: omit `--manifest` and `--post`, or unset `SAFE2_MCP_PRO_KEY`.

**After a `--post` reached the hosted service.** The hosted record is owned by the service
operator. Ask the operator to delete the snapshot; this repository cannot recall a posted
manifest. Rotate the Tarvin key if it may have been exposed (`as2k_...`), through the key owner.

**Local clean-up.** Evidence bundles are written under the chosen `--output-dir`; delete the
bundle, and any leftover `.aisafe2-project-manifest-1.json.*.tmp`, by hand.

**Verification after any rollback.** `safe2 assess .` still runs without `--manifest`;
`python -m pytest tests/ scanner/tests/`; `python scripts/check_agent_manifest.py`.

Decision owner for rollback: _(blank: Owner of Record)_.

## 3. Test evidence

Bound to the code revision below. Later commits that only add this evidence file do not change
code; verify with `git diff <code revision>..HEAD --name-only`.

Code revision assessed: `341cc45` (a docs commit on top of code commit `43963bb`). Environment: local
Linux, Python 3.13 venv; hosted CI results are separate and recorded in the PR body, not here.

| Check | Command | Outcome |
|---|---|---|
| Full suite | `python -m pytest tests/ scanner/tests/ -q` | 1626 passed, 8 skipped, exit 0 (the skips are outside the manifest tests, not investigated individually) |
| Manifest tests | `python -m pytest tests/test_assess_manifest_*.py -q -rs` | 480 passed, 0 skipped |
| Frontmatter tests | `python -m pytest tests/test_assess_manifest_frontmatter.py -q` | 203 passed (174 at `6aa07ef` + 29 new parametrized cases) |
| Red at `6aa07ef` | same file with the new tests | 22 of the 29 new cases failed before the fix (unmatched `)` accepted in 20 cases; unclosed `(` in a block-list item accepted in 2). One further failure was my own mistaken positive case, removed before the fix. The other 7 passed before the fix: 5 are must-accept guards, and 2 are flow-list `[Bash(echo, Task]` negatives that already failed closed |
| Finding 1 mutation | neutralise `if not closed:`, run 3 closing-delimiter tests, restore | 3 failed, then 3 passed after `git checkout` |
| CI lint mirror | `ruff check --select E9,F63,F7,F82 safe2/ tests/ scripts/` | passed |
| Manifest checks | `scripts/check_agent_manifest.py`, `check_component_versions.py`, `check_repo_ux.py` | passed |
| mypy | `mypy safe2/manifest` | no issues. `mypy safe2` reports 10 errors in 7 files, none in files this PR changes (not a CI gate) |

What these prove: the listed behaviours were observed under these inputs. They do not prove
the hosted service accepts the manifest, nor that the heuristics are correct.


## 4. This update (review findings against 6aa07ef)

| Finding | Source | Result |
|---|---|---|
| `_parse_frontmatter` returns partial results when the closing `---` is past the 200-line limit | Greptile P1, `collect.py:330` | **Already fixed before this update**, in `672d4c9` (comment was raised on `31680d2`). Verified at `6aa07ef` by neutralising the `if not closed:` raise: three tests fail (`test_frontmatter_past_the_line_limit_fails_closed_instead_of_dropping_fields`, `test_frontmatter_that_never_closes_fails_closed`, `test_the_closing_delimiter_on_line_200_is_accepted_and_on_line_201_is_rejected`); restored, all pass. No code change and no new test needed; the existing tests cover a long `description` pushing `tools:`/`permissionMode:` past the limit and a missing delimiter. |
| `_scan_flow` ignores an unmatched `)` | Codex L1, `collect.py:182-188` | **Fixed** in `43963bb`, docs in `341cc45`. 29 new tests, written red first (22 failed at `6aa07ef`; of the other 7, 5 are must-accept guards and 2 were already rejected), green after. |
| Missing human design-approval record and revision-bound receipt | Codex I1 | **Drafted here**, labelled BOT-DRAFTED. Owner decision left blank. Receipt pending. |

Design calls for finding 2:

- Depth never goes below zero (a negative depth would stop commas splitting and change both quote
  readings); an unmatched `)` is reported as depth `-1` and rejected where an unclosed `(` already was.
- Block-list items are never split, so the only check they get is the balance check in
  `_strip_comment`. This also newly rejects an unclosed `(` in a block-list item
  (`- Bash(echo`), which was previously read as `Bash`.
- A stray `)` counts only when both quote readings see it. `Bash(echo ")")` is read the same way
  under both readings and stays accepted (an existing positive test); loosening that would have
  meant editing a test, tightening past it would have rejected unambiguous input.
- A quoted entry may hold an unmatched parenthesis (`["Bash(echo))", Task]`): quoting the whole
  entry is the documented escape hatch.

## Receipt status

`safe2 dev receipt PLAN SOURCE` requires a plan and a receipt source that record the final
revision, reviews, and the decision owner's inputs. No human decision or review source exists
yet, and a receipt generated now would manufacture one. **Pending**; produce it against the final
head after the Owner of Record decides. A receipt is decision evidence, never merge authority.
