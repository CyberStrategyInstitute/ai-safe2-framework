# PR #430 complete security-diff review (`safe2/**`)

> **BOT-DRAFTED - requires Owner of Record confirmation.**
> Self-assessment by the authoring agent (Claude Sonnet 5.5). It is not independent
> validation, not a design approval, not a conformance claim, and not a `safe2 dev receipt`.
> Nothing here approves a merge, release, deployment, or risk acceptance. It replaces the
> partial review in [README.md](README.md) section 1 of the earlier revision.

## Subject and method

| Item | Value |
|---|---|
| Subject | PR #430, branch `csi/safe2-assess-pro` |
| Base | `origin/main` = `3dd7ecc8bc0f19a0c737f01a91b9bde68d0a20d3` (fetched 2026-11-15; the branch is linear on it, so it is also the merge base) |
| Diff reviewed | `git diff origin/main...5ee98fe` (27 files; 16 under `safe2/**`, 10 tests, 1 evidence note), plus the three fixes made in this review (`1812025`, `879b022`, `0d87a0d`) |
| Plane | `agent-to-tool` (local file collection) plus one opt-in outbound request to a hosted endpoint. Evidence from one plane does not validate another. |

How each file was reviewed. "Read" means read in full or, for existing files, every changed hunk
(`git diff`), in this session:

- Read in full: `manifest/collect.py` (913 lines), `manifest/post.py`, `manifest/workflow.py`,
  `manifest/heuristics.py`, the `assess.py`, `cli.py`, `contracts.py`, `discovery/assets.py` and
  `secure_io.py` diffs, `docs/ASSESS-MANIFEST.md`, and the three smaller doc diffs.
- Walked by script, not by eye: the vendored schema (closed objects, external `$ref`, length and
  count bounds, patterns). The heuristics data file was read for its secret patterns, unattended,
  memory, mode-order, `cannot_detect` and tool-category sections.
- Dynamic probes run here (scratch directories outside the repo): the frontmatter `KeyError`
  (before and after), the mode-masking case (before and after), an inheriting agent with no
  settings, and secret-pattern timing on 2 MB single lines (worst case about 1 s, linear).
- Not done: line-by-line reading of the 10 test files (only those touched here), fuzzing of the
  frontmatter reader, dynamic testing against the hosted service, a dependency audit, an
  installed-wheel run, independent review.

Dimensions: **IV** input validation, **PH** path handling, **NT** network/TLS, **DS**
deserialization, **SP** subprocess/exec, **SC** secret handling, **FM** failure modes.
"N/A" = the dimension does not occur in that file.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Low | `_parse_frontmatter` raised an uncaught `KeyError` (traceback, exit 1) for an agent file with a bare `tools` / `disallowedTools` line before a list item. No manifest was written (fail closed by accident), but the failure was not reported or handled. | **Fixed** `1812025`. Red first: 5 of 7 new unit cases and the 1 CLI case failed at `5ee98fe` (3 `KeyError`, 2 no failure); 2 must-accept guards passed. Now a named collection failure. |
| F2 | Medium | An unrecognized `permissions.defaultMode` (for example `dontAsk`) ties with `bypassPermissions` in the mode ranking, and `max()` kept the first of the tie. With `settings.json` = `dontAsk` and `settings.local.json` = `bypassPermissions` the manifest reported mode `other` and `runs_unattended: false`: a favourable under-report that depended on file-name order. | **Fixed** `879b022`: a known mode wins the tie. Red first: 1 of 2 orderings failed at `5ee98fe` (the other is a guard). |
| F3 | Medium | An agent with no `tools:` line reports `tools: []` and every capability flag false when no settings `allow` rules or MCP servers exist (reproduced). In Claude Code an omitted `tools:` inherits the main thread's tools, so such an agent can include `Task`, `Bash`, `Write`, or web tools. This conflicts with "when the CLI cannot tell, it writes the unfavourable value". Only the local notes record `tools_inherited: true`. | **Not changed. Owner decision.** Fixing it changes flag semantics, the heuristics file (`draft-unreviewed`) and the golden outputs, which is beyond a minimal review fix, and the correct inherited set should be confirmed against Claude Code. Needs the named heuristics reviewer (open decision 3). |
| F4 | Low | `clean_text` strips only C0/C1 control characters. Bidirectional-override and zero-width characters in server text pass through to the terminal. The earlier note and `ASSESS-MANIFEST.md` said "None known". | **Not changed.** The server is the one the user authenticated to; residual only. The claim is corrected in `ASSESS-MANIFEST.md`. |
| F5 | Low | `parse_heuristics` validates `tool_categories`, `approval_point_categories` and the two secret patterns but not `unattended`, `memory`, `permission_mode_order`, `cannot_detect` or the `placeholder_*` keys. A damaged packaged file surfaces as a `KeyError` at collection. | **Not changed.** Packaged, reviewed data; not user-reachable. |
| F6 | Low | `post_manifest` has per-read timeouts (connect 10 s, others 30 s) but no overall deadline; a server that sends one byte per 29 s can hold the command open until the 1 MiB cap. | **Not changed.** Opt-in, user-authenticated endpoint; bounded by size. |
| F7 | Low | The agent name falls back to the file stem unfiltered. A stem over 200 characters or a path over 512 fails schema validation (closed, with a message); control characters in a file name are JSON-escaped and sent as a name. | **Not changed.** Fails closed or sends only a name. |
| F8 | Info | `collect.py` imports the private `scanner.scanner._KNOWN_SECRET`. `scanner` is packaged in the wheel (`pyproject.toml` `packages`), so it resolves, but a rename in `scanner` would break `assess` at import time. | Not changed. |
| F9 | Info | `--post` with no key exits 0 and prints the manual call. Documented in `ASSESS-MANIFEST.md`. | Not changed; recorded so a reader does not assume `--post` implies sent. |
| F10 | Info | A symlinked `~/.claude` (dotfile managers) fails `--manifest` closed every time. Documented. | Usability limit. |
| F11 | Info | `httpx` honours `HTTPS_PROXY` and `SSL_CERT_FILE`. Same-host user control; documented for the proxy. | Residual. |
| F12 | Info | `write_new_atomic`: if the staging unlink fails with an `OSError` while another exception is in flight and nothing was published, the unlink error replaces it. The behaviour predates this PR (only the published case is new). | Not changed. |

## File-by-file

| File | What was checked | Verdict |
|---|---|---|
| `safe2/commands/assess.py` | **IV** consent (`--scan-content` and `--inspect-config`) checked before any read, write or send; `--manifest-out`/`--post` rejected without `--manifest`; malformed key rejected before the assessment runs and never echoed. **PH** target resolved; output paths pass through `write_new_atomic`. **NT** only calls `post_manifest` when `--post` and a key exist; no key means nothing sent. **DS** N/A. **SP** none added. **SC** key read from `os.environ` only, never an option; JSON output carries only redacted server fields. **FM** each failure class is named (cleanup, collection, validation, post); the bundle is kept and no manifest is left; exit 1 when the server did not record it. | Pass. F1 was reachable through this command as a traceback; fixed in `collect.py`. F9 observation. |
| `safe2/cli.py` | **IV/PH/NT/DS/SP/SC** N/A: registration rename (`assess_project` to `assess_command`) and one help line. A repository-wide search found no other importer of the old name. **FM** N/A. | Pass. |
| `safe2/contracts.py` | **DS** one schema-registry entry; validation builds a local-only `referencing` registry, so a `$ref` cannot be fetched remotely, and the vendored schema has no external `$ref`. Violations carry paths, not values. **IV/PH/NT/SP/SC** N/A. **FM** invalid manifest raises `ManifestValidationError`. | Pass. |
| `safe2/data/aisafe2-project-manifest-1.schema.json` | **IV** every object closed (`additionalProperties: false`, scripted check); bounds present: names 1-200, tools 500, agents/servers/hooks 200, config files 500, paths 512, mode 64; digests patterned. Enums for transport, auth and approval points. **DS** no external `$ref`. Other dimensions N/A. | Pass. Equality to the hosted schema is pinned by a test that skips when no server checkout is available (not run here). |
| `safe2/data/manifest-heuristics-v1.json` | **IV** secret regexes use bounded quantifiers except one linear tail; probed on 2 MB single lines, worst about 1 s. **SC** placeholder prefixes and words reduce false positives only. **FM** F5. Status `draft-unreviewed`. | Pass with caveat: needs a named human reviewer; F3 concerns its use. |
| `safe2/discovery/assets.py` | **IV/PH** `extra_classifier` runs only for files the built-in classes do not recognize; the walk is the existing one (no symlink following, `max_files` bound). Default `None` leaves existing inventories unchanged. **FM** truncated inventory is made fatal by the caller. Other dimensions N/A. | Pass. |
| `safe2/secure_io.py` | **PH** hard-link publish without overwrite, symlink ancestry rejected before and after `mkdir`, `O_EXCL` staging with random name, mode 0600. **FM** new `PublishedCleanupError` separates "published, cleanup failed" from "not written"; the caller keeps the output. F12. **DS/NT/SP/SC** N/A. | Pass. |
| `safe2/manifest/__init__.py` | Docstring only. | Pass. |
| `safe2/manifest/collect.py` | **IV** hand-written frontmatter reader rejects what it cannot read unambiguously (item-aware quote and parenthesis scans, line and tool caps); tool names constrained by regex; names printable-filtered and capped. F1 and F2 fixed here; F3, F7 open. **PH** reads go through `read_regular_bounded` (symlink leaf and ancestry rejected, size-bounded); discovery uses the bounded inventory; user-level files limited to three known locations; paths shown as `~/...` or project-relative. **NT** none. **DS** JSON/TOML parsed from bytes with `RecursionError` and decode errors mapped to "unparseable", which fails the run; no YAML, `pickle`, `eval` or `exec`. **SP** none. **SC** secret-pattern hits are counted per line and the match is never stored; `.env` content is hashed (a short file's digest is guessable offline, documented); command lines, args and env values never enter the manifest, only names and digests. **FM** incomplete collection raises `ManifestCollectionError`; truncation, over-limit counts and unreadable user files all fail closed. | **Pass after F1 and F2 fixes.** Open: F3 (Medium, owner decision), F7, F8. |
| `safe2/manifest/heuristics.py` | **IV** structural validation of categories, approval mapping and patterns; `re.compile` errors mapped to `HeuristicsError`. **DS** `json.loads` of packaged bytes. F5. **PH** `importlib.resources`. Others N/A. | Pass with F5. |
| `safe2/manifest/post.py` | **IV** key must start `as2k_` and hold no whitespace, rejected without echo; request over 1 MiB refused locally. **PH** N/A. **NT** fixed `https` endpoint (`http` only for loopback, hostname parsed with `urlsplit`), no redirects, TLS verification left at the `httpx` default, connect/read timeouts, one retry only on connect failure or connect timeout, response read as a stream and capped at 1 MiB after decoding (so a compressed bomb is counted). F6, F11. **DS** reply decoded as JSON or event-stream, depth overflow mapped to `bad_response`; `applied` must be a literal boolean. **SP** none. **SC** key is only in the `Authorization` header, never in an exception message (only the exception type name is kept); every reply string, key and list item is redacted before truncation. **FM** every outcome has a status; only `applied: true` exits 0. F4. | Pass. F4 and F6 low residuals. |
| `safe2/manifest/workflow.py` | **PH** `--manifest-out` made absolute, rejected if it equals the notes path; both writes use `write_new_atomic` (no overwrite, no symlink ancestry). **FM** notes first, manifest last; a failed manifest write removes only the notes this run created, never an earlier run's; published-but-unlinked is re-raised, not swallowed. **IV** validation before any manifest byte. **NT/DS/SP/SC** N/A. | Pass. |
| `safe2/README.md`, `safe2/docs/README.md`, `safe2/docs/UNIFIED-ASSESSMENT.md` | One-line link or sentence additions; the `UNIFIED-ASSESSMENT.md` wording states the one opt-in network exception. All dimensions N/A. | Pass. |
| `safe2/docs/ASSESS-MANIFEST.md` | Claims checked against code: consent order, exit codes (0 only when `applied` is true; no-key exit 0), redaction, retries, limits, fail-closed list, `tools:` inheritance, atomic-write behaviour. Mismatch found: the threat-model row "None known" for hostile server text (F4); corrected here. The list of constructs that stop collection gained the bare-key case. All code dimensions N/A. | Pass after the two edits. |

## Conclusion (self-assessment)

Two real defects in `collect.py` were found and fixed with tests written red first (F1, F2). One
Medium design gap remains open for an owner decision (F3). Nothing found in the network, key
handling, path handling or atomic-write code required a change. This is a bounded, single-reviewer
read of the diff; it does not replace an independent review, dynamic testing of the hosted
service, a dependency audit, or the Owner of Record's confirmation.

Owner of Record confirmation: _(blank: for Vincent)_
