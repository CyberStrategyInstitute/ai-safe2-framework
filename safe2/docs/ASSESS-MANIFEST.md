# Project manifest for hosted assessment (`safe2 assess --manifest`)

`safe2 assess --manifest` runs the normal [unified assessment](UNIFIED-ASSESSMENT.md)
and then writes one extra artifact, `aisafe2-project-manifest-1.json`
(`aisafe2-project-manifest/1`): the facts about your agents, MCP servers, hooks,
permissions, and config files that the hosted Tarvin assessment turns into a
governance record.

The manifest holds **names, boolean flags, counts, and digests only**. It never
holds file contents, prompts, secret values, command lines, environment values, or
tool arguments. Nothing is sent anywhere unless you add `--post`.

## Quick start

```bash
safe2 init .
safe2 assess . --manifest --scan-content --inspect-config
```

That writes the usual evidence bundle plus, inside it:

| File | Purpose |
|---|---|
| `aisafe2-project-manifest-1.json` | The manifest. Validated against the schema before it is written. |
| `manifest-collection-notes.json` | Local only. Why each unfavourable default or omitted key was used, and which files were read or skipped. Never sent. |

To send it, set the key in your environment and add `--post`:

```bash
export SAFE2_MCP_PRO_KEY=as2k_...   # a Tarvin key
safe2 assess . --manifest --scan-content --inspect-config --post
```

Use `--manifest-out PATH` to write the manifest somewhere other than the bundle
(a relative path resolves from your current directory; an existing file is never
overwritten).

## Consent

`--manifest` requires **both** `--scan-content` and `--inspect-config` on the command
line. Without them the command stops before it reads, writes, or sends anything:

```text
Error: --manifest requires explicit --scan-content and --inspect-config consent
```

A `collect_content = true` setting in `.safe2/config.toml` does not stand in for
these flags for `--manifest`. `--manifest-out` and `--post` are rejected without `--manifest`.

## What is read

Only the target project and the user-level agent locations that `safe2 doctor`
already knows. Every read is bounded by `limits.max_file_bytes`, rejects symbolic
links, and goes through the shared `safe2.secure_io` reader.

| Location | Files |
|---|---|
| Project | Agent definitions (`.claude/agents/*.md`, `.github/agents/*.md`), MCP configs (`.mcp.json` and any `mcp.json`, including under `.cursor/` and `.vscode/`), harness settings (`.claude/settings.json`, `.claude/settings.local.json`, `.codex/config.toml`), `.env` and `.env.*`, and CI workflows (searched for a headless-agent marker only) |
| User (`~`) | `~/.claude/settings.json`, `~/.claude/agents/*.md`, `~/.codex/config.toml` |

`~/.claude.json` is **not** read: it is not a location `doctor` knows. A file in these
locations that exists but cannot be read or parsed stops the run (see below), because
skipping it could hide a permissive setting. In particular a symlinked `~/.claude`
(common with dotfile managers) blocks `--manifest` until the symlink is not in the path.

## What the manifest contains

| Field | Source |
|---|---|
| `generator` | Always `{"name": "safe2 assess --manifest", "version": <safe2 version>}`. The hosted service labels a manifest `cli` only for a `generator.name` it recognizes; any other name is `model_supplied` and is never applied over an existing CLI record. Read-only check of the Tarvin repository (not the deployed service): commit `b80cc52` of PR #11 recognizes both `safe2 assess --manifest` and the legacy `safe2 assess --pro`, but the PR's current head `ffd88bf` lists only `safe2 assess --pro`. **Confirm the deployed service accepts `safe2 assess --manifest` before the first real `--post`.** |
| `project.name` | `project.name` from `.safe2/config.toml`, else the directory name. `project_id` is omitted (see open decisions). |
| `agents[]` | Name, harness, `definition_digest` (SHA-256 of the definition file), tool **names**, the flags below, and `approval_points`. |
| `mcp_servers[]` | Name, transport, `auth_type`, `pinned_digest` (a SHA-256 found in the arguments, such as `image@sha256:<hex>`; a version number is not a digest), and `config_digest`. |
| `hooks[]` | Event name and the SHA-256 of the command. The command itself is never kept. |
| `permissions` | Most permissive mode found, rule counts, and a digest of the rules. |
| `config_files[]` | Relative path (`~/...` for user-level files), SHA-256, and `secret_findings`, a count of lines that match a secret pattern. The matched text is never kept. |
| `ci_gate` | Omitted. CI is not inspected, because collection opens no network connection. The server treats an omitted key as unknown. |

`config_digest` hashes a redacted structure (name, transport, command basename,
argument count, pinned digest, environment and header **names**, auth type, URL
host). Environment values, header values, and arguments are not part of it.

### Flags are heuristics

The rules that turn tool names and settings into flags live in
[`safe2/data/manifest-heuristics-v1.json`](../data/manifest-heuristics-v1.json),
marked `draft-unreviewed`, with a test table in `tests/test_assess_manifest_heuristics.py`.
The hosted rules trust these flags, so a named reviewer should sign that file before
the flags are relied on.

- A tool is categorized only by its **name**. Tool arguments are never read into a decision.
- A `tools:` list is used as written. An agent with no `tools:` line inherits the
  names in the settings `allow` list plus `mcp__<server>` for every configured MCP
  server, so a mail or payment server counts even though its tools are not listed.
  The local notes record that the tools were inherited.
- Only a bare tool name in the `ask` list counts as an approval point. `Bash(git push:*)`
  covers a subset of uses and is not counted.
- `deny` and `ask` rules reach an agent only from `~/.claude/settings.json` and from the
  project directory that holds that agent's `.claude/agents` folder, so a nested project's
  restrictions never lower another project's agent. A project directory is the parent of a
  `.claude` folder, matched on whole path parts and ignoring case; a settings file that does not
  sit directly in a `.claude` folder is applied to no agent. `allow` rules, permission mode, hooks,
  and MCP servers are collected project-wide, which can only over-report capability. The
  manifest's rule counts and digest still cover every settings file read.
- `runs_unattended` is true for `permissionMode: bypassPermissions` on the agent, a
  settings-level bypass mode (Claude Code agents only), a scheduled-operation file such
  as `HEARTBEAT.md`, or a headless-agent marker in a CI workflow.
- `persistent_memory` is true for a memory tool, a `memory:` setting on the agent, or a
  persistent-state file such as `MEMORY.md`.

**When the CLI cannot tell, it writes the unfavourable value.** `mandate_configured`,
`memory_provenance`, and `budget_ceiling_configured` have no reliable configuration
signal today, so they are written `false` wherever the schema requires them. That
means a spawning agent always reads as lacking a mandate until a signal is defined.
The reasons are recorded in `manifest-collection-notes.json`, never in the manifest.

## Posting

`--post` makes one MCP `tools/call` of the hosted Tarvin assessment tool with
`{ "manifest": <manifest> }`
to `https://mcp.agency-check.app/pro/mcp` over Streamable HTTP: one POST, no
`initialize`, no session.

- **Tarvin key.** `SAFE2_MCP_PRO_KEY` (`as2k_...`) from the environment only. It is never
  accepted as an option, never written to config, the bundle, notes, logs, or the
  manifest, and never printed. If the server echoes it back, the key and any other
  `as2k_...` token are replaced with `[redacted]` in every string of the reply (values,
  field names, and list items) before it is shortened, shown, or returned in `--format json`.
  A reply nested too deeply to check is reported as `bad_response` and not shown.
- **No key.** The manifest path and the exact one-line call are printed and the command
  exits 0. It does not prompt.
- **Retries.** One retry, only on a connect error or a connect timeout, both of which fail before any
  request byte is sent. Never on a 4xx, 5xx, or a read or write timeout.
  Redirects are not followed, so the key never travels to another URL.
- **Limits.** Requests over 1 MiB are refused locally. Responses over 1 MiB are rejected.
- **Output.** Tier, missing controls, snapshot id, and whether the record was applied.
  The output always states that the manifest is **unsigned**.
- **Exit codes.** `0` only when the server recorded the manifest (`applied` is true); `1` on
  "not applied" (the server answered but recorded nothing, for example because it treated the
  manifest as model-supplied), a reply whose `applied` is missing or is anything other than a
  boolean (reported as `bad_response`), `pro_required` (prints the upgrade URL), `invalid_manifest`
  (prints the schema paths), a rejected key, an HTTP error, or a network failure. The local
  manifest is kept in every case. With no key, `--post` sends nothing and exits `0`.

## Fails closed

No manifest is written, and the bundle is kept, when:

- the asset inventory reached `limits.max_files` (the manifest would silently omit agents);
- a project or user-level config file is unparseable, unreadable, or larger than `limits.max_file_bytes`;
- there are more than 200 agents, MCP servers, or distinct hooks, more than 500 config
  files, or an agent has more than 500 tools;
- an agent definition's frontmatter does not close with `---` within its first 200 lines
  (a `tools:` or `permissionMode:` line after the cut-off would be silently lost);
- `--manifest-out` is the bundle's `manifest-collection-notes.json`; or
- the manifest does not match the vendored schema.

The error names the file and reason, never a value. Rerun with a new `--output-dir`.

The collection notes are written first and the manifest last, so a failure leaves no
manifest behind. If the manifest cannot be written after the notes were, the notes written
by that run are removed again; files from an earlier run are never removed.

## Determinism

The manifest is serialized with sorted keys and stable list ordering. The same tree
produces the same bytes except `generated_at`.

## Schema

The manifest schema is vendored at
[`safe2/data/aisafe2-project-manifest-1.schema.json`](../data/aisafe2-project-manifest-1.schema.json)
and listed as `aisafe2-project-manifest-1` in `safe2 schema list`. A test pins its digest
and checks that it equals the server's `schemas/aisafe2-project-manifest-1.json`
(set `SAFE2_SERVER_SCHEMA` to a checkout's file; the test is skipped if none is available).

## Threat model

| Threat | Control | Remaining limitation |
|---|---|---|
| Customer data leaves the machine without consent | Both consent flags; nothing is sent without `--post`; tests patch `socket` and assert no connection is opened | `--post` is per-run consent. `privacy.network_export` in the config is not consulted |
| The API key leaks | Environment only; never in an option, file, log, or output; a server echo is redacted; sentinel-key tests cover success, 401/403, other HTTP errors, JSON-RPC and tool errors, event-stream replies, and a JSON-escaped echo, in human and JSON output | A process-environment reader on the same host can see it. Only the exact key and `as2k_...`-shaped tokens are redacted; a server that re-encodes or splits the key before echoing it is not detected |
| The key is sent to the wrong place | Fixed `https` endpoint; no redirects; plain `http` only for loopback in tests | A user who changes `HTTPS_PROXY` routes the request through that proxy |
| File contents, prompts, secrets, arguments, or commands reach the manifest | Only names, flags, counts, digests; the schema rejects unknown keys; sentinel tests grep the manifest, bundle, notes, and output | A tool or agent **name** is sent as written, and a secret placed in a name would be sent |
| A digest reveals a secret | The matched text is never kept | `config_files[].sha256` of a short `.env` is a SHA-256 of the whole file, so a low-entropy secret could be guessed offline |
| A hostile server writes to the terminal | Server text is stripped of control characters and truncated | None known |
| The manifest is forged | None | The manifest is **unsigned**. The server trusts `generator.name`, so any client can claim to be the CLI |
| A heuristic hides a gap | Unknown values are written unfavourably; incomplete collection fails closed | Heuristics can be wrong in either direction; they have not been reviewed |
| Reading outside the project | Reads limited to the project and `doctor`'s user locations through the bounded reader; a test spies on every collector read | The existing assessment steps keep their own reads |

## Open decisions

1. **Manifest signing.** Needs a key-management decision. No key is generated or stored here.
2. **Stable `project_id`.** Where it lives (config or a dotfile) and what a cloned
   repository does. Until decided it is omitted and the server falls back to
   `project.name`, so two projects with the same name on one account share a record.
3. **Which harness definitions count** as spawning, unattended, or sending. The rules are in
   the data file above and need a named reviewer.
4. **Whether `--post` should also require `privacy.network_export = true`.**
