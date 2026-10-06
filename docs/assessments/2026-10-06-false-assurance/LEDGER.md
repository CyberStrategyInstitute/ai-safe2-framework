# Ledger: False-Assurance Hardening

Append-only. Newest entry at the bottom. Each entry: what happened, evidence, next step.

---

## 2026-10-06 E1: Initial findings (pre-battery)

Installed safe2 1.0.0 and nexus-a2a-sdk 0.5.0 from `main` (`83de4a8`). Probed the MCP
scorer with a hostile local server whose tool description instructs credential theft.
It scored 87/100 "Acceptable", earned the badge, and passed `safe2 gate mcp --ci-fail-below 70`.
It did this with a self-published attestation file, an empty OAuth metadata document,
and a 429 response after 3 requests. An honest server scored 63.

**Evidence:** reproduced by battery cases `MCP score:*` and `gate mcp URL:*`.
**Next:** full four-area battery.

## 2026-10-06 E2: First fix pass (session context later lost)

An earlier pass at the request built a battery and pushed three commits to this branch:
- `47c2dc8` fixed the MCP knowledge server (M1-M7).
- `06e523a` fixed the MCP toolkit score, scan, and wrap (T1-T7).
- `8f3d038` fixed the skill trust gate and the project gate (S1, C1, C2).

It also left an uncommitted Rego v1 rewrite. The chat context for that pass was lost.
Its commit messages are the record.

**Lesson:** this is why the ledger, state file, and snapshots now live in the repo.

## 2026-10-06 E3: Battery rebuilt and re-run independently

The earlier pass was not trusted. The battery was rebuilt (126 cases) and run against
untouched `main` and the branch.

| Area | main `83de4a8` | branch `8f3d038` + WIP |
|---|---|---|
| SKILL | 9 / 18 | 19 / 8 |
| MCP | 2 / 14 | 20 / 0 |
| CLI | 24 / 1 | 25 / 0 |
| NEXUS | 24 / 30 | 30 / 24 |

Four harness defects were corrected, each because the product was right:
- `feedback record --outcome verified_done` without evidence correctly exits 1.
- `--strict` correctly REJECTs a document that quotes an attack phrase.
- An HTTP probe path was wrong.
- `skills/` root rejection is a packaging boundary issue, not a gate defect.

**New findings on main:**
- The OPA policies do not compile on OPA 1.x.
- `authorize_tool_call` is undefined for 9 of 13 inputs.
- A memory scope downgrade bypasses the mandate.
- Explicit deny rules never gate `allow`.
- `deny_reason` is always empty.
- The compose OPA mount points at a non-existent directory.
- Guardian allows 15 of 26 evasions.
- AgBOM tamper and rug-pull go undetected.

**Next:** NEXUS fixes.

## 2026-10-06 E4: NEXUS OPA fixed, checkpoint pushed

Commit `f3ecea0`, pushed:
- Rego v1 on all three policies.
- Authz is always defined, and the most restrictive scope wins.
- Explicit deny now gates `allow`.
- Deny reasons are populated.
- AISM loads.
- CI covers `NEXUS/opa` on OPA 0.65 and 1.4.2.

**Evidence:**
- `opa test`: 16/16 on both OPA versions. Against main's authz policy, 8 of 11 authz tests fail.
- APay rewrite differential: 873/873 identical decisions, zero looser.

**Next:** modular battery in the repo, ledger, and snapshots (owner request), then Guardian and AgBOM.

## 2026-10-06 E5: Battery moved into repo, durability files added

- Battery moved into `tests/battery/` (core plus one module per area). It writes
  per-area result files and supports `--resume` and `--areas`.
- Hostile code is stored inert (`.fixture` suffix), with credentials synthesized at run
  time. The TLS cert is generated per run.
- Pytest collects 0 files from it.
- Added `RUNBOOK.md`, `STATE.json`, and this ledger.

**Next:** freeze before and after snapshots, push, then Guardian (N-G) and AgBOM (N-A).
