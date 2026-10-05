# Unified Project Assessment

`safe2 assess` provides the shortest path from installation to a reviewable AI
SAFE² evidence bundle. It orchestrates existing environment discovery, asset
inventory, posture analysis, and optional static scanning. It does not replace
the deeper evidence commands or infer evidence that was not collected.

## Quick start

```bash
safe2 init . --profile local
safe2 assess . --scan-content --inspect-config
```

The command creates the configured output directory, `.safe2/evidence` by
default, only when that path does not already exist. A relative `--output-dir`
is resolved from the assessed project root, not from the caller's current
working directory. The published bundle contains:

| Artifact | Purpose |
|---|---|
| `assessment.json` | Canonical summary, coverage, disposition, and next actions |
| `environment.json` | Sealed local harness, environment, asset, and posture evidence |
| `project-scan.json` | Completed or explicitly unrequested static-analysis evidence |
| `manifest.json` | Byte hashes and structural validation for machine evidence |
| `decision-card.md` | Human-readable projection of the canonical assessment |

## Consent and privacy

The default run inventories recognized filenames and metadata. It does not read
project contents for static analysis and therefore returns `INCOMPLETE` rather
than a clean result.

`--scan-content` explicitly permits bounded local content reads by the static
scanner. `--inspect-config` requires the same consent and emits only allowlisted
structural facts; raw configuration values are not retained. The workflow does
not transmit telemetry or connect to cloud accounts, remote hosts, or active
harness sessions.

## Interpreting the disposition

| Disposition | Meaning |
|---|---|
| `BASELINE` | Requested local surfaces completed and produced no observed finding; this is not a universal safety verdict |
| `REVIEW` | Requested surfaces completed and one or more findings require human review |
| `INCOMPLETE` | Material evidence was unrequested, truncated, or unavailable |

Static analysis and metadata cannot establish runtime behavior, organizational
maturity, certification, framework conformance, or deployment authorization.
Add task receipts, harness exports, system identity, AISM implementation
evidence, and Challenge Lab evidence when those claims matter.

## Recovery

The bundle is assembled in a staging directory and published only after its
contracts validate. Existing output directories are never replaced. Move or
archive a prior bundle, select a new `--output-dir`, and rerun.
