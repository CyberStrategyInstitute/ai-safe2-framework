# Operational Truth and Agent-Input Monitoring

AI SAFE² CLI 0.7.0 connects provider-attributed harness exports and task
receipts into one canonical task record. It answers four practical questions:
what was observed, what was only declared, what evidence is missing or in
conflict, and whether the supplied record is ready for a human decision.

It does not certify completion, reconcile a provider bill, authenticate native
logs, or claim AI SAFE² conformance. Those boundaries remain `false` in the
machine-readable result even when all supplied evidence agrees.

## Quick start

First normalize one or more harness exports and create a task receipt:

```bash
safe2 evidence harness harness-source.json --output harness-evidence.json
safe2 feedback receipt task-receipt-input.json --artifact-root . --output task-receipt.json
```

Declare the task identity, revision, SHA-256 digests of receipts explicitly
bound to that revision, required evidence domains, decision owner, assumptions,
and exclusions. An unbound receipt remains visible but cannot support a
completion claim. A starting example ships as
`safe2/data/operational-truth-source-demo.json`.

```bash
safe2 evidence truth operational-truth-policy.json \
  harness-evidence.json task-receipt.json \
  --output operational-truth.json \
  --card operational-truth.md \
  --strict
```

The JSON is canonical. The Markdown card is a readable projection. `--strict`
writes both artifacts before returning a nonzero exit when the result is
`review` or `hold`.

## Decision meanings

| Gate | Meaning |
|---|---|
| `ready_for_human_decision` | Required coverage is complete and the supplied receipt supports the completion claim; this is not verified completion |
| `review` | Evidence is missing, partial, not claimed, or insufficient to support the claim |
| `hold` | Task/revision identity conflicts, contradictory receipt evidence, or conflicting usage records exist |

Coverage is conservative across harnesses: a missing domain in one supplied
harness is not hidden by complete coverage from another. Repeated usage event
identifiers are deduplicated only when their metric, value, basis, and source
reference agree. Conflicting duplicates cause a hold.

## Explicit local or CI monitoring

The change monitor is a bounded, one-shot command. It is never installed as a
background service, does not scan a network, exports no file content, and sends
no telemetry. It tracks complete packages rooted by `SKILL.md`; named agent
instructions including `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`; `.mcp.json`
and `openclaw.json`; and JSON, TOML, or YAML configuration inside explicit
`.codex`, `.claude`, `.hermes`, and `.openclaw` directories beneath the root.

```bash
# First run: inventory and evaluate present skills
safe2 evidence changes . --output agent-input-baseline.json --strict

# Later run or CI job: compare against the prior immutable artifact
safe2 evidence changes . \
  --baseline agent-input-baseline.json \
  --output agent-input-current.json \
  --strict
```

New or changed skills are evaluated by the first-party Skill Trust Gate.
Agent-configuration changes are held for human review because a byte change can
alter authority without being inherently malicious. Removed files remain
visible. The baseline binds a privacy-preserving digest of the resolved root so
unrelated directories with the same name cannot exchange baselines. Git,
virtual environments, dependencies, and caches are excluded.
Traversal is bounded to 10,000 entries and 1 MB per tracked file by default;
incomplete coverage fails closed.

For periodic use, call the one-shot command from an operator-controlled CI
schedule or local scheduler. That makes frequency, scope, logs, cancellation,
and artifact retention visible in the system already responsible for jobs.
AI SAFE² does not create a hidden daemon.

## Security and privacy boundaries

- Evidence files are parsed under strict versioned JSON contracts with bounded
  size and count limits.
- Input identity is checked before and after opening to reject file-replacement
  races rather than following a substituted link or special file.
- Duplicate artifact bytes, unsafe output paths, symbolic links in monitored
  scope, unknown contracts, and output overwrite attempts are rejected.
- Cards never become a second decision source; regenerate them from canonical
  JSON.
- Native records stay provider-attributed. Importing them does not authenticate
  their origin or prove that omitted events do not exist.
- Do not place raw prompts, secrets, credentials, or personal data in normalized
  source files. Store only the minimum identifiers, hashes, counts, status, and
  references necessary for review.

## Contracts

- `operational-truth-source-v1`
- `operational-truth-manifest-v1`
- `change-monitor-v1`

Discover, export, and validate them with `safe2 schema list`, `safe2 schema
export`, and `safe2 schema validate`.
