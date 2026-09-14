# Agent system identity manifests

[Framework Home](../README.md) | [CLI Guide](../safe2/README.md) | [Harness Evidence](./TASK-RECEIPTS.md#provider-neutral-harness-evidence-intake) | [Challenge Lab](./CHALLENGE-CLI.md)

## Purpose

An agent assessment is not reproducible when it names only the model. The tested
system also includes its harness, tools, skills, memory, execution environment,
policies, evaluator, authority, and the relationships among them.

`safe2 evidence system` converts an attributed identity declaration into a
strict, portable manifest. It answers **what system is this evidence about?** It
does not claim that the declaration is authentic or matches deployed state.

## Quick start

From a repository checkout:

```console
safe2 schema export system-identity-source-v1
safe2 evidence system safe2/data/system-identity-source-demo.json --output system-identity.json --strict
safe2 evidence manifest system-identity.json --subject-id demo-agent-system --output run-manifest.json --strict
```

The packaged example explicitly identifies one component in each category and
links every component to the harness. Replace example values and digests with
attributed facts from the system being assessed.

## Identity categories

| Category | Examples of identity that belongs here |
| --- | --- |
| Model | Provider, model identifier, version or dated alias, worker/evaluator role |
| Harness | Product, SDK or CLI version, instance and orchestration role |
| Tool | API, MCP server, CLI, browser, test runner and effective authority |
| Skill | Skill or workflow version and artifact digest when available |
| Memory | Session or persistent store, access authority and role |
| Environment | Local host, WSL, container, VM, CI runner or cloud execution boundary |
| Policy | Policy/version, enforcement role and content digest when available |
| Evaluator | Test oracle, grader, independent system or human review component |

At least one model, harness and environment component is required. IDs must be
globally unique inside the manifest. Bindings form an explicit system graph using
relationships such as `uses`, `runs_on`, `invokes`, `governed_by`,
`evaluated_by`, `reads_from`, `writes_to` and `delegates_to`.

## Coverage is not presence

Each category has one coverage state:

| Status | Meaning |
| --- | --- |
| `complete` | The source claims the applicable category inventory is complete. |
| `partial` | Some applicable identities are present but gaps remain. |
| `missing` | No identity was collected and the basis must remain unknown. |
| `not_applicable` | The source affirmatively declares that the category does not apply. |

`missing` and `not_applicable` are deliberately different. A category cannot be
marked missing or not applicable while components of that category are present.
A complete category cannot contain components whose evidence basis is unknown.

Every component, binding and coverage statement is `observed`, `declared` or
`unknown`. Observed and declared statements require a source reference. An
unknown statement cannot cite evidence it does not have. These are attribution
labels, not SAFE2 verification levels.

## Two hashes, two meanings

The output contains:

- `source.sha256`: a digest of the exact submitted bytes. Formatting changes
  produce a new source digest.
- `system_fingerprint_sha256`: a canonical identity fingerprint over the subject,
  component identities, authority and relationships. Object key order, list order
  and evidence-source labels do not change this fingerprint; composition does.

Neither hash authenticates the author, proves deployed configuration, or proves
that a component was active during a run. Bind supporting artifacts separately
through `evidence_refs` and the existing evidence manifest.

## Strict mode

`--strict` writes the manifest and exits 1 when any of these gaps remain:

- partial or missing category coverage;
- a component with an unknown evidence basis;
- a versionable model, harness, tool, skill, policy or evaluator without a version;
- a component that has no relationship to another component.

Exit 0 means identity intake met these completeness rules. It does not mean
identity, configuration, execution, safety, control effectiveness or AI SAFE2
conformance was verified.

## Privacy and security guidance

Use stable, non-secret identifiers. Do not place prompts, credentials, tokens,
tool arguments, raw outputs, personal data or filesystem contents in an identity
manifest. `authority` records capability classes, not secret-bearing permission
documents. Use hashes and bounded external evidence references for supporting
artifacts.

The intake rejects oversized input, duplicate JSON keys, duplicate identifiers,
dangling or self-referential bindings, inconsistent source references and
contradictory coverage. Output uses no-overwrite file creation.

## Challenge Lab use

Bind one system identity manifest to every Challenge Lab treatment. A model-only
change and a harness-only change must produce different component identity but
can retain the same scenario and acceptance criteria. This creates the basis for
later paired comparisons without changing frozen Challenge 001 outcomes.

This increment records identity; it does not yet change Challenge Lab schemas or
automatically collect native Codex, Claude Code, Hermes or OpenClaw state. Native
adapters remain a later capability and must map supported exports or hooks into
the provider-neutral contract.
