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
| `safe2 aism init FILE` | Create a 30-cell unscored assessment | Missing evidence remains unscored |
| `safe2 aism ingest BUNDLE...` | Import evidence conservatively | Suggests mappings; requires human confirmation |
| `safe2 aism score FILE` | Validate and score AISM assessment | Produces agent JSON or human Decision Card |
| `safe2 aism compare OLD NEW` | Compare score, decision, and coverage history | Rejects malformed inputs cleanly |
| `safe2 example list` | Discover executable examples | Works in a clone and installed wheel |
| `safe2 example verify NAME` | Verify declared example outcomes | Fails on expectation drift |
| `safe2 mcp wrap ...` | Consumer-side MCP inspection and policy proxy | Applies runtime policy and audit behavior |

Run `safe2 COMMAND --help` for complete options.

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
