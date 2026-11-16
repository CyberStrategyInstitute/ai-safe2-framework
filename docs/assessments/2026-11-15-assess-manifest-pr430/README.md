# PR #430 `safe2 assess --manifest`: security review, rollback runbook, test evidence

> **BOT-DRAFTED - requires Owner of Record confirmation.**
> Self-assessed by the authoring agent (Claude). Not independent validation, not a design
> approval, not a conformance claim, and not a `safe2 dev receipt`. Nothing here approves a
> merge, release, deployment, or risk acceptance.

## Decision record

| Item | State |
|---|---|
| Subject | PR #430, branch `csi/safe2-assess-pro` (CLI `safe2 assess --manifest`, collector, post client, schema, docs, tests) |
| Delivery shape / risk | `architectural` / `critical`, from `safe2 dev plan`: [development-evidence.md](development-evidence.md) section 1 ([plan source](dev-plan-source.json), [plan](development-plan.json), exit 1 `review_required`, retroactive). Risk equals the policy floor for `safe2/**` |
| Human design approval | **Not recorded. OPEN for Vincent's `/signoff`** ([development-evidence.md](development-evidence.md) section 2) |
| Revision-bound evidence note | [development-evidence.md](development-evidence.md) section 3. A `safe2 dev receipt` was **not produced**; see [Receipt status](#receipt-status) |
| Owner of Record decision | _(blank: for Vincent to fill in)_ |
| Decision date | _(blank)_ |

## 1. Security review of the PR diff (self-assessment)

The earlier partial review in this section was **replaced** by a complete file-by-file review:
[security-diff-review.md](security-diff-review.md) (BOT-DRAFTED - requires Owner of Record
confirmation). It covers every changed file under `safe2/**` (16 files), lists what was checked per
file, and records 12 findings. Two were real defects in `safe2/manifest/collect.py` and are fixed
with red-first tests (F1 frontmatter `KeyError`, `1812025`; F2 an unrecognized permission mode
hiding `bypassPermissions`, `879b022`). One Medium gap is left open for an owner decision (F3:
an agent with no `tools:` line reports all capability flags false). The condensed table below
remains as a summary of design-level controls and residual risks; where it differs from the new
review, the new review governs.

| Area | Observation | Evidence | Residual risk |
|---|---|---|---|
| Consent | `--manifest` stops before any read, write, or send unless `--scan-content` and `--inspect-config` are on the command line; `--post` is a separate opt-in | `tests/test_assess_manifest_cli.py` | `--post` is per-run consent; `privacy.network_export` is not consulted (open decision 4 in `ASSESS-MANIFEST.md`) |
| Data minimisation | Manifest carries names, flags, counts, and digests; schema rejects unknown keys | schema + sentinel tests in `test_assess_manifest_collect.py`, `_cli.py`, `_schema.py` | A tool/agent name or a short `.env` digest can still expose low-entropy secrets |
| Reads | Bounded reader, symlinks rejected, `doctor` locations only; unreadable or unparseable config fails the run | `safe2/secure_io.py`, collector tests | Existing assessment steps keep their own reads |
| Fail-closed collection | Unreadable/ambiguous agent frontmatter fails collection instead of yielding a favourable flag (this update closes two gaps, see §4) | `tests/test_assess_manifest_frontmatter.py`, `_collect.py` | Hand-written frontmatter reader (no YAML dependency): it rejects rather than guesses, so valid-but-unusual YAML stops `--manifest` |
| Credential handling | `SAFE2_MCP_PRO_KEY` from environment only; never an option, file, log, or output; server echoes redacted | `safe2/manifest/post.py`, `tests/test_assess_manifest_post.py` | Same-host process-environment reader; a server that re-encodes the key before echoing it is not detected |
| Network | One POST to a fixed `https` endpoint, no redirects, size limits (1 MiB), one retry on connect failure only; collection opens no connection (tests patch `socket`) | `post.py`, post tests | A user-set `HTTPS_PROXY` routes the request. The deployed service's acceptance of the `safe2 assess --manifest` generator name is **unconfirmed** |
| Output safety | Server text stripped of control characters and truncated | post tests | Bidirectional-override and zero-width characters are not stripped (F4) |
| Authenticity | Manifest is **unsigned**; the server trusts `generator.name` | documented | Any client can claim to be the CLI. Signing is an open decision; no key was created |
| Flag heuristics | `manifest-heuristics-v1.json` is `draft-unreviewed` | heuristics tests | **Needs a named human reviewer** before hosted rules rely on the flags |
| Atomic write | Notes first, manifest last; failure leaves no manifest; published-but-unlinked staging file reported distinctly | `tests/test_secure_io_publish.py`, CLI tests | Leftover `.tmp` needs manual removal in the one reported case |
| Dependencies | No new third-party dependency in the PR; `httpx` and `jsonschema` were already declared | `git diff origin/main...HEAD -- pyproject.toml` is empty | No dependency-audit tool was run |

Not covered: independent review, dynamic testing against the hosted service, fuzzing of the
frontmatter reader, a signed manifest, a dependency audit, an installed-wheel run, and any claim
about hosted-service behaviour.

## 2. Rollback / recovery runbook

The feature is additive and opt-in. Nothing runs unless a user passes `--manifest`.

**Before merge (PR still draft).** Do nothing to `main`. Stop by leaving the PR draft or closing it.
Reverting is deleting the branch; no deployed artifact exists.

**After merge, before a release.** Revert the merge (or squash) commit through a new PR
(`git revert -m 1 <sha>` for a merge commit, plain `git revert <sha>` for a squash commit). The change touches `safe2/commands/assess.py`, `safe2/cli.py`,
`safe2/contracts.py`, `safe2/discovery/assets.py`, `safe2/secure_io.py`, and adds
`safe2/manifest/`, one schema, one heuristics file, docs, and tests. Edits to existing modules, checked
against `git diff origin/main`: the `assess` command (registration renamed from `assess_project` to
`assess_command`, plus the new options; its diff is reviewed in full in [security-diff-review.md](security-diff-review.md)), an optional
`extra_classifier` parameter in `safe2/discovery/assets.py` (default off, so existing inventories are unchanged),
one schema-registry entry in `safe2/contracts.py`, a `PublishedCleanupError` subclass of `OSError` in
`safe2/secure_io.py`, and doc paragraphs.

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

The earlier test accounting (bound to `341cc45`) was superseded. Current, revision-bound results
(code revision `879b022`: 1636 passed and 8 skipped in the full suite; 490 passed in the manifest
tests; lint, type and manifest-check results) are in
[development-evidence.md](development-evidence.md) section 3, together with the per-evidence-id
status and the items that were **not run** (installed wheel, release invariants, dependency audit).
Hosted CI results are recorded in the PR body, not here.

What these prove: the listed behaviours were observed under these inputs. They do not prove
the hosted service accepts the manifest, nor that the heuristics are correct.

## 4. This update (review findings against 6aa07ef)

| Finding | Source | Result |
|---|---|---|
| `_parse_frontmatter` returns partial results when the closing `---` is past the 200-line limit | Greptile P1, `collect.py:330` | **Already fixed before this update**, in `672d4c9` (comment was raised on `31680d2`). Verified at `6aa07ef` by neutralising the `if not closed:` raise: three tests fail (`test_frontmatter_past_the_line_limit_fails_closed_instead_of_dropping_fields`, `test_frontmatter_that_never_closes_fails_closed`, `test_the_closing_delimiter_on_line_200_is_accepted_and_on_line_201_is_rejected`); restored, all pass. No code change and no new test needed; the existing tests cover a long `description` pushing `tools:`/`permissionMode:` past the limit and a missing delimiter. |
| `_scan_flow` ignores an unmatched `)` | Codex L1, `collect.py:182-188` | **Fixed** in `43963bb`, docs in `341cc45`. 29 new tests, written red first (22 failed at `6aa07ef`; of the other 7, 5 are must-accept guards and 2 were already rejected), green after. |
| Missing human design-approval record and revision-bound receipt | Codex I1 | **Drafted here**, labelled BOT-DRAFTED. Owner decision left blank. Receipt pending. |
| Security review partial (M2) | Codex cross-review at `5ee98fe` | **Replaced** by [security-diff-review.md](security-diff-review.md); two defects fixed (`1812025`, `879b022`). |
| Critical-route development evidence (M1) | Codex cross-review at `5ee98fe` | **Added**: [development-evidence.md](development-evidence.md) with `safe2 dev plan` output; human design approval left OPEN for the Owner of Record. |

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
revision, reviews, and the decision owner's inputs. The plan now exists
([development-plan.json](development-plan.json), `review_required`). No human decision or review
artifact exists yet, and a receipt generated now would manufacture one; see
[development-evidence.md](development-evidence.md) section 4. **Pending**; produce it against the
final head after the Owner of Record decides. A receipt is decision evidence, never merge authority.
