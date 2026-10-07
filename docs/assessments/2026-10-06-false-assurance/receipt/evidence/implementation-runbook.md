# False-Assurance Hardening: Runbook

Assessment and fix campaign opened 2026-10-06. Owner: Vincent Sullivan.
Branch: `fix/v31-false-assurance-hardening`. Base: `main` at `83de4a8`.

**Question under test:** do the four AI SAFE² components ever tell a user something is
safe, compliant, or blocked when it is not?

| Area | Components |
|---|---|
| SKILL | `skills/` content and the skill trust gate (`safe2 gate/scan skill`) |
| MCP | `aisafe2_mcp_tools` (score, scan, wrap) and the `skills/mcp` knowledge server |
| CLI | `safe2` commands end to end: gates, doctor, evidence, schema, feedback, challenge |
| NEXUS | Guardian, AgBOM, SDK tests, OPA policies, compose wiring, scoring utility |

## Files in this folder

| File | Purpose | Rule |
|---|---|---|
| `RUNBOOK.md` | How to run, resume, extend | Update when the process changes |
| `LEDGER.md` | What happened, in order | **Append only.** Never edit past entries |
| `STATE.json` | Machine-readable resume point | Rewrite at every checkpoint |
| `snapshots/<label>-<sha>/` | Frozen battery results | Never edit; add a new snapshot instead |

## Run the battery

Prerequisites: Python 3.11+, `openssl`, `curl`. OPA 1.x (`OPA_BIN`) and OPA 0.65
(`OPA_LEGACY_BIN`, the docker-compose pin) for the NEXUS policy cases. Without them those
cases are recorded `NOT_RUN`, never `PASS`.

```bash
python -m venv .venv && .venv/bin/pip install -e ".[all,dev]" -e ./NEXUS -e ./skills/mcp
SHA=$(git rev-parse --short HEAD)
OPA_BIN=$(which opa) OPA_LEGACY_BIN=/path/to/opa-0.65 \
  .venv/bin/python tests/battery/run.py --label after --venv .venv \
  --out-dir docs/assessments/2026-10-06-false-assurance/snapshots/after-$SHA
```

One area only: add `--areas nexus` (or `skill`, `mcp`, `cli`; comma-separated).

**Before state:** check out `main` in a separate worktree, install it into its own venv,
and point `--repo` and `--venv` at those. Run the battery from the branch, so that both
sides face the same cases. For the knowledge server, use the install path that `main`
documents (`pip install -e skills/mcp`) in its own venv, passed as `--mcp-venv`.

Outputs, one folder per run:

- `<area>.json`: written as soon as that area finishes
- `summary.json` and `MATRIX.md`: rebuilt from whichever area files exist
- `*_raw.txt`: tool output, with credentials synthesized and never real

## Resume after an interruption

1. `git fetch origin && git checkout fix/v31-false-assurance-hardening && git pull`
2. Read `STATE.json` (module status, last green commit, `next_step`), then the last `LEDGER.md` entry.
3. Re-run an interrupted battery with the same `--out-dir` plus `--resume`. Areas already
   recorded for the current revision are skipped.
4. Continue from `next_step`. Do not rebuild context from chat history.

## Verdicts

| Status | Meaning |
|---|---|
| PASS | Product behaved securely and correctly for this case |
| FAIL | Product gave false assurance, missed an attack, or broke |
| NOT_RUN | Case could not execute; the reason is recorded. Never counted as a pass |
| INFO | Recorded fact needing a human decision, e.g. a packaging boundary |

Fixing the product is the only way to turn a FAIL green. If a case expectation is
wrong, fix the harness in its own commit and say why in the ledger.

## Add a case

1. Add the fixture under `tests/battery/fixtures/`. Hostile code gets a `.fixture` suffix,
   so linters and semgrep never treat it as project code. Key-shaped strings use the
   `@@FAKE_*@@` placeholders defined in `core.py`.
2. Add the case to the matching `area_*.py`, stating the secure expectation in `want`.
3. Run it against `main` (expect red) and the branch (expect green). Record both in the ledger.

## Checkpoint protocol

After every completed module, and at least every ~30 minutes:

1. Run the affected areas.
2. Commit, with one commit per module.
3. Write the snapshot, update `STATE.json`, and append to `LEDGER.md`.
4. Push the branch.

Work that is not pushed does not exist.

## Differential tools (not part of the default run)

`fixtures/apay_diff.py OLD NEW TESTMOD OPA_BIN OPA_LEGACY_BIN` compares `main`'s APay
policy on OPA 0.65 with the branch policy on OPA 1.x. It runs 873 inputs derived from the
repo's own APay fixture and fails if any decision got looser.

## Boundaries

- Fixes only. Architectural moves need the owner's decision; they are listed under
  `open_decisions` in `STATE.json`.
- No merge, release, publish, or conformance claim. Those belong to the owner.
- Battery results are self-assessment evidence (AGENTS.md §4.2). They are not independent
  validation.
