# Guided Start

`safe2 start` turns the first local AI SAFE² assessment into one previewable,
consent-bound workflow. It is designed for a person delegating to an agent and
for an agent that needs a clear stopping point before it changes anything.

## Quick start

Preview the plan. This reads only enough filesystem metadata to validate the
target and existing AI SAFE² configuration; it writes no files:

```console
safe2 start .
```

Execute after reviewing the target, inspection consent, output, and boundaries:

```console
safe2 start . --execute
```

The command asks for confirmation. An authorized non-interactive caller can use:

```console
safe2 start . --execute --yes
```

`--yes` means only that the displayed local plan was authorized. It does not
authorize remediation, network access, deployment, publication, or acceptance
of risk.

## Choose inspection scope

| Option | Local behavior | Default |
|---|---|---|
| no inspection flags | Inventory recognized local metadata and security assets | enabled |
| `--scan-content` | Read bounded project content for static analysis | disabled |
| `--inspect-config` | Emit allowlisted, redacted configuration structure | disabled; requires `--scan-content` |
| `--wsl` | Inventory WSL distribution names when available | disabled |

No option in this command enables remote or cloud access.
If an existing validated project configuration already enables content
collection, the preview shows the effective read as enabled and identifies its
source as `configuration`. Execution is bound to that configuration digest and
refuses to proceed if it changes after preview.

## Outputs

The default destination is `.safe2/onboarding`. Select another new directory
with `--output-dir`. Existing destinations are rejected.

| Artifact | Audience | Meaning |
|---|---|---|
| `onboarding-plan.json` | agent/reviewer | Exact approved scope, consent, steps, and stops |
| `onboarding-result.json` | agent/reviewer | Run outcome, assessment summary, authorization boundary, and integrity digest |
| `next-step-card.md` | human | Short action path and explicit boundary |
| `configuration-snapshot.toml` | reviewer | Exact bounded configuration approved for this run |
| `assessment/assessment.json` | agent/reviewer | Canonical assessment, coverage, limitations, and next actions |
| `assessment/decision-card.md` | human | Detailed readable assessment |
| `assessment/environment.json` | agent/reviewer | Local discovery and posture evidence |
| `assessment/project-scan.json` | agent/reviewer | Consented scan or explicit `not_requested` state |
| `assessment/manifest.json` | verifier | Hash-bound assessment artifact inventory |

`completed` means the approved workflow finished and wrote valid artifacts. It
does not mean the project is safe, compliant, conformant, or ready to deploy.

## Recovery and repeat runs

The project configuration is created first because the assessment consumes it.
If later assessment work fails, the secure configuration may remain and will be
reused on the next run. Partial evidence is staged and removed rather than
published. A successful bundle is never overwritten; choose a new output path
for another run.

## Agent handoff

```text
Run `safe2 start .` and show me the plan. Distinguish facts, requested reads,
missing coverage, and actions the command will not take. Do not add `--execute`,
`--yes`, `--scan-content`, `--inspect-config`, or `--wsl` without my explicit
approval. After execution, show me both Decision Cards and the canonical JSON
paths. Stop before remediation, remote access, deployment, publication, policy
change, exception, or risk acceptance.
```
