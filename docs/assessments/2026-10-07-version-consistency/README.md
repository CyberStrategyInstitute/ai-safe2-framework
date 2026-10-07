# Repository version-consistency sweep (2026-10-07)

Self-assessed by the authoring agent. Not independent validation and not a conformance claim.

## Why

After #393 retagged the skill surfaces to v3.1, the owner asked whether the whole
repository was consistent. It was not. The landing-page guard (`check_repo_ux.py`)
covers 17 pages and 4 phrasings, so drift elsewhere was invisible:

| Class | Before (base `7286925`) | After |
|---|---|---|
| Stale `v3.0` framework labels | 600+ lines across shipped tooling, the MCP knowledge server, scanner, NEXUS, dashboard, CI templates and 15 example packages | 0 outside the reasoned allowlist |
| MCP control printed is not the control emitted | 9 failing citation tests (7 finding classes, 2 fix templates, the dep checker emitter, 5 remote-check remediations) | 51/51 pass |
| Retired v3.0 MCP names (for example "MCP-12 Swarm C2 Detection") | 20 | 0 |
| NEXUS presented as v0.3 (current is 0.5.0) | 9 current-state claims | 0 |
| CLI version claims | SECURITY.md `0.1.x`, manifest `0.9.9`, AGENTS.md "release candidate", README install fails on PyPI | Truthful; enforced by `check_agent_manifest.py` |
| Duplicate stale toolkit under `examples/` | 34 files, linked from the root README | Redirect README only |

## Evidence

All files are in `evidence/`.

| File | What it shows |
|---|---|
| `guard-red-7286925.txt`, `guard-green.txt` | Repo-wide guard output before (624 findings) and after (clean) |
| `citations-red-7286925.txt`, `citations-green.txt` | `tests/mcp_toolkit/test_control_citations.py`: 9 failed, then 51 passed |
| `agent-manifest-red-7286925.txt`, `agent-manifest-green.txt` | Published-version checks: 2 findings, then pass |
| `examples-before.txt`, `examples-after.txt` | Smoke and `safe2 example verify` results for all 22 examples; identical |
| `gates-local.txt` | Local CI mirror: 31/31 PASS |
| `battery-summary.txt` | Four-area battery: 126 PASS, 0 FAIL, 0 NOT_RUN (no regression from #393) |
| `inventory.py` | The classification script used to scope the sweep |

## What was deliberately kept

Every exception is in `.ai-safe2/version-label-allowlist.json` with a reason. An
entry that stops matching a tracked file fails the guard.

- **Gateway v3.0 component code**: `gateway/main.py` and the OpenClaw and Hermes copies. Gateway evidence keeps its v3.0 identity until a separately tested gateway release (`gateway/README.md`, Version and Conformance Boundary).
- **GENESIS hash seeds.** Changing them breaks verification of existing chains.
- **Byte-stable core taxonomy datasets and their generator**, the frozen AIM v0.2 schema, and attestation-file key prefixes (`MCP-12_swarm_c2_controls`). The keys are now documented as retired numbering, not v3.1 IDs.
- **Dated records**: research, releases, assessments, changelogs and the v3.0/v3.1 release overviews.

## Owner action outside this PR

PyPI serves `ai-safe2` 0.9.0. The 1.0.0 GitHub release was tagged
`2026-10-5_CLI_1.0.0`, and `publish.yml` only runs for `v*` tags, so it never
published. This PR makes that failure visible on the next release. It does not
publish anything.

## Reproduce

```bash
python scripts/check_framework_version_labels.py
python scripts/check_agent_manifest.py
python -m pytest tests/mcp_toolkit/test_control_citations.py tests/test_framework_version_labels.py -q
```
