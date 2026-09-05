# AI SAFE² CLI
### Agent-facing assessment, evidence, decision support, and enforcement for AI SAFE² v3.1

[Framework Home](../README.md) | [AISM](../AISM/README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [Examples](../examples/README.md) | [NEXUS](../NEXUS/)

The `safe2` package turns repository controls, assessment logic, and evidence
contracts into a single command surface for agents, engineers, governance
teams, and CI systems. JSON is the canonical agent exchange format. Human
decisions remain human-owned and can be rendered as Markdown or HTML Decision
Cards.

## Where This Capability Lives

| Location | Role |
|---|---|
| [`AISM/`](../AISM/README.md) | Normative maturity model, architecture, methodology, assessment, and crosswalk |
| [`safe2/aism/`](./aism/) | Executable AISM validation, scoring, ingestion, comparison, and Decision Card rendering |
| [`safe2/evidence/`](./evidence/) | NEXUS and NVIDIA SkillSpector evidence adapters |
| [`safe2/commands/`](./commands/) | Unified CLI command groups and stable error handling |
| [`examples/aism-decision-card/`](../examples/aism-decision-card/) | Runnable reference assessment and human acceptance example |

This is a repository and packaging boundary, not a new framework pillar. AI
SAFE² remains 161 core controls with CP.1 through CP.10. UAS is a separate
27-requirement regulatory profile extension.

## Install

From a repository clone:

```bash
pip install -e ".[all]"
safe2 --help
```

For contributor checks:

```bash
pip install -e ".[all,dev]"
pytest tests/ scanner/tests/
```

## Command Map

| Command | Purpose | Decision behavior |
|---|---|---|
| `safe2 scan project PATH` | Informational 161-control project scan | Reports findings; does not gate |
| `safe2 score project PATH` | Compact project score | Reports score only |
| `safe2 gate project PATH` | CI/CD project decision | Enforces tier or `--fail-under` threshold |
| `safe2 gate skill PATH --strict` | Skill trust decision | Approve, reject, or hold for review |
| `safe2 scan mcp PATH` | Static MCP source analysis | Informational |
| `safe2 score mcp URL` | Remote MCP assessment | Reports evidence-backed score |
| `safe2 report ...` | JSON, SARIF, Markdown, or HTML artifacts | Preserves native engine semantics |
| `safe2 evidence nexus PATH` | Collect NEXUS implementation/runtime evidence | Does not infer maturity |
| `safe2 evidence skillspector PATH` | Run optional NVIDIA SkillSpector adapter | Preserves upstream output and attribution |
| `safe2 evidence manifest FILE...` | Bind heterogeneous evidence into one run record | Hashes and validates artifacts without claiming conformance |
| `safe2 aism init FILE` | Create a 30-cell unscored assessment | Missing evidence remains unscored |
| `safe2 aism ingest BUNDLE...` | Import evidence conservatively | Suggests mappings; requires human confirmation |
| `safe2 aism score FILE` | Validate and score AISM assessment | Produces agent JSON or human Decision Card |
| `safe2 aism compare OLD NEW` | Compare score, decision, and coverage history | Rejects malformed inputs cleanly |
| `safe2 example list` | Discover executable examples | Works in a clone and installed wheel |
| `safe2 example verify NAME` | Verify declared example outcomes | Fails on expectation drift |
| `safe2 mcp wrap ...` | Consumer-side MCP inspection and policy proxy | Applies runtime policy and audit behavior |
| `safe2 doctor PATH` | Metadata-only harness, shell, host, and WSL discovery | Inventory evidence only; does not claim assessment or conformance |
| `safe2 feedback record ...` | Capture sanitized operational friction | Records typed outcome and verification state in local JSONL |
| `safe2 feedback summary FILE` | Measure recurring friction and completion-verification gap | Aggregates local evidence without sending telemetry |
| `safe2 schema list` | Discover packaged machine-readable contracts | Returns stable schema identifiers as JSON |
| `safe2 schema export NAME` | Export one versioned JSON Schema | Writes to stdout or an integration-owned file |
| `safe2 schema validate NAME FILE` | Validate an evidence artifact | Exit 0 valid, 1 contract violation, 2 unreadable input |

## Multi-Harness Environment Discovery

`safe2 doctor` is the first local-first discovery surface for environments that
run more than one agent harness. It detects known command/configuration
indicators for Codex, Claude Code, Antigravity, Hermes, OpenClaw, and Grok,
along with available shells, the host operating system, CI markers, and WSL
availability.

```bash
safe2 doctor .
safe2 doctor . --format json --output environment-inventory.json
safe2 doctor . --assess
safe2 doctor . --no-wsl
safe2 doctor . --wsl-distro Ubuntu-24.04
safe2 doctor . --ssh-host audit@devbox.example --ssh-port 22
```

The v1 collector is deliberately metadata-only: it does not read configuration
contents, environment-variable values, prompts, tool output, or credentials.
It inventories WSL distribution names when the host exposes them. A named WSL
distribution can be inspected with `--wsl-distro`; an SSH-accessible Linux host
or cloud VM can be inspected with `--ssh-host`. Both execute a fixed,
metadata-only POSIX probe. SSH uses batch mode, requires an already trusted host
key, and will not prompt for passwords or accept a new host key. Targets must be
provided explicitly: `safe2 doctor` never scans a network. A discovery result
is not proof that a harness is active, current, or securely configured.

Cloud control-plane inventory, Windows remoting, containers, and deep
configuration assessment are not implemented in the v1 collector. Failed or
unreachable explicit targets are reported as incomplete rather than being
treated as clean.

Add `--assess` to derive a first metadata-bounded posture. It identifies
project-policy review needs, stale or non-PATH installation indicators,
unreachable target coverage gaps, and multi-harness consistency needs. It does
not convert metadata into a security score: missing policy indicators retain
explicit alternative explanations, mappings are labeled as candidate controls,
and runtime/configuration/cloud coverage remains false until directly tested.

By default, the doctor also performs a bounded, filename-and-metadata-only
inventory of security-relevant project assets:

- agent instruction and definition files;
- agent skills;
- MCP configuration candidates;
- persistent agent state and heartbeat indicators;
- CI/CD workflows;
- container definitions; and
- Terraform, Bicep, and Pulumi infrastructure definitions.

```bash
safe2 doctor . --assess --max-files 50000
safe2 doctor . --no-assets
safe2 doctor . --assess --hash-assets
safe2 doctor . --assess --inspect-config
```

Dependency, VCS, build, cache, and local evidence directories are excluded;
symbolic links are not followed. File contents and hashes are not collected by
default. `--hash-assets` opts into bounded local reads of recognized
security-relevant assets and emits only SHA-256 digests, enabling stronger
change detection for agent instructions, skills, CI, containers, persistent
state, and infrastructure definitions. Files above
`--max-asset-hash-bytes` remain explicit hash coverage gaps.
If the traversal limit is reached, the posture receives a high-severity
coverage-gap finding instead of treating the partial inventory as complete.

`--inspect-config` is a separate opt-in boundary. It reads only discovered JSON
or TOML harness/MCP configuration files and emits an allowlisted structural
summary: top-level key names, permission-rule counts, hook event names, MCP
server names and transport classes, selected sandbox/approval modes, file size,
and a content hash for later drift comparison. It does not emit URLs, commands,
arguments, header names or values, environment key names or values, prompts, or
raw configuration. Files that cannot be parsed or exceed the configured limit
remain explicit coverage gaps.

```bash
safe2 doctor . --inspect-config --max-config-bytes 1048576 --format json
safe2 doctor . --assess --inspect-config \
  --output environment-inventory.json \
  --card-format markdown --card-output environment-card.md
safe2 doctor . --assess --inspect-config \
  --card-format html --card-output environment-card.html
```

The posture flags fully permissive sandbox/approval combinations for human
review and reports only the count of secret-like key names. A matching key does
not prove that a plaintext secret is present; it may contain a placeholder or
environment reference.

The optional environment Decision Card is a concise human briefing derived
from the same sealed JSON inventory. Markdown is optimized for repositories and
review workflows; HTML is self-contained, responsive, and printable. Both show
the disposition, evidence confidence, scope, coverage, harness and asset counts,
drift history, integrity, deduplicated facts and assumptions, evidence
conflicts, persona impacts, prioritized actions, alternatives with pros and
cons, a recommended path, ownership gap, and exit criteria. Outcome probability
is explicitly `NOT ESTIMABLE` when only metadata evidence exists. Card creation
requires `--assess` and a separate `--card-output`, preserving the canonical JSON
artifact instead of replacing it.

### Agent and CI Policy Decisions

An environment policy turns the evidence-bounded posture into deterministic
agent and CI behavior. For example:

```json
{
  "schema_version": "safe2.environment-policy.v1",
  "id": "production-agent-default",
  "allowed_dispositions": ["BASELINE", "REVIEW"],
  "max_findings": {"critical": 0, "high": 0},
  "require_baseline": true,
  "require_baseline_integrity": true,
  "require_config_inspection": true,
  "require_all_targets_completed": true,
  "max_drift_changes": 0
}
```

```bash
safe2 doctor . --assess --inspect-config \
  --baseline trusted-inventory.json \
  --policy environment-policy.json --enforce-policy \
  --output environment-decision.json \
  --card-format markdown --card-output environment-card.md
```

Policy decisions are `ALLOW` (exit `0`), `DENY` (exit `1`), and `HOLD` (exit
`2`). `DENY` represents an observed threshold or allowed-disposition breach.
`HOLD` represents missing or incomplete evidence needed to decide safely. An
`INCOMPLETE` posture always holds even if a policy attempts to allow it.
Without `--enforce-policy`, evaluation is advisory and the command exits `0`;
with enforcement, all requested JSON and card artifacts are written before the
decision exit code is returned.

`ALLOW` means only that supplied evidence met the named local policy. It is not
a universal safety determination, authorization, certification, AISM maturity
rating, or AI SAFE² conformance claim.

### Trusted Baselines and Drift

Save a reviewed inventory, then compare later runs against it:

```bash
safe2 doctor . --no-wsl --assess --inspect-config \
  --output .safe2/evidence/environment-baseline.json
safe2 doctor . --no-wsl --assess --inspect-config \
  --baseline .safe2/evidence/environment-baseline.json \
  --output .safe2/evidence/environment-current.json
```

The comparison reports added, removed, or modified harness indicators and
security-relevant assets, changed hashes for configurations inspected in both runs, lost target
coverage, and comparison-scope changes. Configuration hashes are available only
when both inventories used `--inspect-config`. Asset content comparison uses
hashes when both runs use `--hash-assets`; otherwise size or modification-time
changes are reported as weaker metadata drift. A change is a review signal, not
proof of unauthorized activity or elevated risk. The baseline should be retained
as trusted evidence only after an authorized human or policy workflow reviews
its scope, coverage, and known exceptions.

Use the same explicit `--wsl-distro` and `--ssh-host` targets in both runs. If a
baseline target is omitted or can no longer be inspected, the result carries a
high-severity coverage finding rather than treating missing evidence as no
change. Comparing a different root or target scope is also a high-severity
coverage finding.

Every newly written discovery inventory includes a deterministic SHA-256
integrity block covering the complete JSON result except the integrity block
itself. A modified sealed baseline is rejected before comparison. Older
`safe2.discovery.v1` inventories remain usable but are labeled
`baseline_integrity: not_present`. Integrity proves that bytes represented by
the canonical JSON have not changed since sealing; because the v1 seal is
unsigned, it does not prove who created or approved the baseline. Store and
approve baselines through the repository's trusted evidence workflow.

## Operational Friction Evidence

User and agent frustrations can be recorded as evaluation evidence instead of
being lost in chat history. The initial taxonomy covers false completion,
missing evidence, silent tool failure, wrong conclusions from missing data,
stuck loops, sycophancy, context loss, permission friction, and integration
failure.

```bash
safe2 feedback record \
  --category false_completion \
  --outcome unverified_done \
  --severity high \
  --harness codex \
  --summary "Agent claimed completion without a resulting diff."

safe2 feedback summary .safe2/evidence/friction.jsonl \
  --output .safe2/evidence/friction-summary.json
```

Outcome states are `verified_done`, `unverified_done`, `failed`, `blocked`, and
`stuck`. An evidence reference changes the verification label from
`self_reported` to `external_reference_supplied`; it does not independently
prove that the referenced evidence is valid. The summary exposes the gap
between claimed completion and verified completion so future evaluations can
optimize for truth rather than confident status language.

Each newly recorded event has a deterministic SHA-256 integrity seal. Summary
generation verifies every available seal and fails closed on a modified event,
preventing corrupted evidence from silently changing completion or frustration
metrics. Legacy unsigned events remain readable, contribute to the metrics, and
are counted explicitly through `sealed_events`, `unsigned_events`, and
`integrity.coverage`. These unsigned digests detect modification only; they do
not authenticate the person or agent that created or approved an event.

Run `safe2 COMMAND --help` for complete options.

## Machine-Readable Contracts

Agent harnesses and CI integrations can discover and export the exact JSON
contracts shipped with their installed CLI version:

```bash
safe2 schema list
safe2 schema export discovery-v1 --output discovery-v1.schema.json
safe2 schema export environment-posture-v1
safe2 schema validate discovery-v1 environment-inventory.json
```

The catalog includes AISM assessments, environment discovery, discovery drift,
environment posture, friction events, and friction summaries. Integrations
should select schemas by their versioned identifier and reject unknown major
contracts rather than guessing from fields. Exporting a schema does not perform
an assessment or validate an evidence artifact; it provides the contract for
the harness's native validator.

`schema validate` is suitable for agent and CI branching: exit `0` means the
artifact satisfies the selected structural contract, exit `1` means contract
violations were found, and exit `2` means the input could not be safely read or
parsed. Validation output never includes instance values or verbose validator
messages. Structural validation does not verify evidence integrity, factual
accuracy, authorization, control effectiveness, or conformance.

## Unified Evidence Run Manifest

After collectors produce their JSON artifacts, bind them into one portable run
record:

```bash
safe2 evidence manifest \
  environment-inventory.json \
  friction-summary.json \
  assessment.json \
  --subject-id governed-workstation-01 \
  --output run-manifest.json \
  --strict
```

Each artifact record preserves its path, byte size, SHA-256 digest, declared
schema version, selected packaged contract, structural-validation state, and
available integrity-verification state. Unsupported, malformed, oversized,
symlinked, structurally invalid, or integrity-invalid artifacts remain visible
as invalid evidence instead of disappearing. `--strict` exits `1` after writing
the complete manifest if any artifact is invalid, allowing agents and CI to
retain diagnostic evidence while stopping promotion.

The manifest receives its own deterministic SHA-256 seal and records the CLI
version, run ID, timestamp, subject, and coverage summary. It is an evidence
inventory—not a maturity score, authorization decision, control-effectiveness
test, or conformance claim. Its unsigned hashes establish change detection, not
author identity or approval.

## AISM Decision Workflow

```bash
safe2 evidence nexus ./NEXUS --output nexus-evidence.json
safe2 evidence skillspector ./candidate-skill --output skillspector-evidence.json
safe2 aism ingest nexus-evidence.json skillspector-evidence.json \
  --subject-id governed-agent --subject-name "Governed Agent" \
  --output assessment.json
safe2 aism score assessment.json --format json --output decision.json
safe2 aism score assessment.json --format markdown --output decision-card.md
```

The Decision Card exposes scores, maturity, evidence trust, facts,
assumptions, conflicts, impacts, history, alternatives, pros and cons,
why/why-not reasoning, outcome and complementary non-outcome estimates,
recommendation ownership, review timing, and exit criteria. The tool never
invents probability or treats scanner availability as proof of conformance.

## Evidence and Trust Rules

- Unverified evidence is capped in the supplemental evidence-adjusted score.
- Digest-verified and independently verified artifacts require provenance.
- The raw AISM Sovereignty Score remains the normative maturity score.
- NEXUS is a reference implementation, not a mandatory conformance dependency.
- SkillSpector is optional; its upstream identity, version, license, target
  digest, timestamp, limitations, and non-endorsement are retained.
- Critical evidence conflicts force `HOLD` for accountable human resolution.

## Output Contracts

- JSON is intended for agents and governance automation.
- Markdown and HTML provide human-readable Decision Cards.
- SARIF supports code-scanning and review systems.
- Exit codes distinguish successful execution, failed gates, human review, and
  invalid input where the command is decision-bearing.

## Limitations

Static scans identify evidence and risk signals; they do not certify an
organization or prove complete runtime behavior. AISM results depend on the
scope, freshness, provenance, and independence of supplied evidence.
Probability ranges are attributed assessment inputs, not predictions invented
by the CLI.

## Start Here

1. Read the [AISM model](../AISM/README.md).
2. Run the [Decision Card example](../examples/aism-decision-card/README.md).
3. Review the [five-minute quickstart](../QUICKSTART_5_MIN.md).
4. Use `safe2 example verify aism-decision-card` as the first installation check.

## Navigation

| Previous | Current | Next |
|---|---|---|
| [AISM](../AISM/README.md) | **AI SAFE² CLI** | [Examples](../examples/README.md) |

[Framework Home](../README.md) | [AISM](../AISM/README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

*AI SAFE² v3.1 · Cyber Strategy Institute*
