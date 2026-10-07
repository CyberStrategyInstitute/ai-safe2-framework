# fix: close false-assurance defects across skills gate, MCP toolkit, CLI, and NEXUS

Self-assessed by the authoring agent. Owner review and merge decision outstanding. Not a conformance claim.

## Problem

A four-area adversarial battery found AI SAFE² components telling users that things were
safe, compliant or blocked when they were not. These cases are from `main` at `83de4a8`.

- **MCP scorer:** a server whose tool description instructs credential theft scored **87/100 "Acceptable"**, earned the badge and passed `safe2 gate mcp --ci-fail-below 70`. It did that with a self-published attestation file, an empty `{}` OAuth metadata document and a 429.
- **Skill trust gate:** approved **9 of 16** hostile skills.
- **Project gate:** passed Tier2 at **90/100** on code that runs `shell=True` and `eval()` on LLM output.
- **MCP knowledge server:** did not start on its documented install, because `mcp` 2.x removed FastMCP.
- **NEXUS Guardian:** allowed **24** evasions. Examples: `id_ed25519`, Windows paths, `%2e%2e%2f`, IMDS as a decimal or hex IP, key bytes in arguments, `curl | sh`, and ACT-4 with reasoning `"x"`. A remote Guardian without `httpx` silently ran the local policy, so FAIL_CLOSED never engaged.
- **NEXUS AgBOM:** a component edited inside a stored version still verified as an intact chain. A rug-pulled manifest became a second trusted server.
- **NEXUS OPA:**
  - No policy compiled on OPA 1.x. The AISM policy failed on every version, and CI watched a non-existent `opa/` path.
  - `authorize_tool_call` was undefined for 9 of 13 inputs.
  - A `request` scope label downgraded a PERMANENT write.
  - Deny rules never gated `allow`.
- **`nexus-score --v03-checks`:** printed **"10/10 verified, all v0.3 controls satisfied"** while the controls above were broken.
- **`skills/`:** installed as a single skill package, which shipped the MCP server's prompt-injection test corpus. Six platform skill surfaces still taught v3.0.

## Result: same battery, same harness (`tests/battery/`)

| | PASS | FAIL | NOT_RUN |
|---|---|---|---|
| `main` `83de4a8` | 60 | 65 | 1 |
| this branch `21a8333` | **126** | **0** | **0** |

62 cases go from red on `main` to green here, with 0 regressions. Frozen snapshots are in
`docs/assessments/2026-10-06-false-assurance/snapshots/`. The case list is in
`receipt/evidence/battery-delta.md`.

## Red/green per regression test file

Each of the 13 new test files was run against `main`'s code and then against this branch's:

| Test file | `main` | branch |
|---|---|---|
| NEXUS `test_guardian_evasion.py` | 24 failed, 9 passed | 33 passed |
| NEXUS `test_agbom_integrity.py` | 7 failed, 2 passed | 9 passed |
| NEXUS `test_memory_vaccine_honesty.py` | 4 failed | 4 passed |
| NEXUS `test_guardian_remote_failover.py` | 2 failed, 1 passed | 3 passed |
| NEXUS `test_nexus_score_honesty.py` | 2 failed | 2 passed |
| `tests/test_gate_false_assurance.py` | 13 failed, 4 passed | 17 passed |
| `tests/mcp_toolkit/test_scan_coverage.py` | 7 failed | 7 passed |
| `tests/mcp_toolkit/test_score_gaming.py` | 6 failed, 1 passed | 7 passed |
| `tests/mcp_toolkit/test_wrap_enforcement.py` | collection error | 7 passed |
| `skills/mcp/tests/test_honest_outputs.py`, `test_transport_e2e.py` | server cannot import | 5 + 6 passed |
| `NEXUS/opa/*_test.rego` | policies fail to load | 16/16 on OPA 0.65 and 1.4.2 |

## Scope: one commit per module

| Commit | Module |
|---|---|
| `47c2dc8` | MCP knowledge server starts on stdio and HTTP; auth hardening; risk and code-review outputs report honestly |
| `06e523a` | MCP toolkit: score cannot be bought, gate fails on detected poisoning, scan coverage, wrap enforces |
| `8f3d038` | Skill trust gate rules TG-013 to TG-024; project gate caps the score on CRITICAL findings |
| `f3ecea0` | NEXUS OPA: Rego v1, always-defined decisions, most-restrictive scope, deny gates allow. APay migration identical on 873/873 differential inputs |
| `5af8409` | Compose: real policy mounts; OPA healthcheck that needs no curl |
| `904e289` `2dac2ff` | Guardian: normalized arguments, 5 detectors, HEAR floor, undeclared tier treated as ACT-4; remote client fails per its fail mode |
| `04f6192` | AgBOM: recomputed verification, isolated snapshots, rug-pull quarantine (hash-compatible) |
| `4f2cff2` `7b85788` | Memory Vaccine labels unmeasured drift; nexus-score checks behavior and has a NOT ASSESSED state |
| `c59cc40` | **D1:** canonical skill moved to `skills/ai-safe2-secure-build-copilot/`; `skills/` is no longer a skill package |
| `8c71410` `21a8333` | **D3:** six skill surfaces retagged to v3.1 with a v3.1 delta and Eval 11; the Codex skill gets its trust card |
| `5b38495` `e0637f7` | CI: pinned, sha256-verified OPA; new `mcp-server` job; `ci.yml` token now read-only; actions SHA-pinned |
| `b24d040` | No key-shaped test literals; 3 historical fixture findings baselined |
| `225f45b` `98598ed` ... | Battery harness, runbook, ledger, state, fresh ports per run, receipt |

## Owner decisions (2026-10-07)

- **D1, option A:** done. No redirect file named `SKILL.md` was left at `skills/`, because CI gates the directory of any changed `SKILL.md`. The moved notice lives in `skills/README.md`.
- **D2:** publish only after merge.
- **D3:** done.
- **D4:** the undeclared-tier-as-ACT-4 interim floor is in this PR. Registry-bound tiers come in a separate follow-up PR.

## Compatibility and breaking changes

- **Guardian:** an omitted `act_tier` is treated as ACT-4, so HEAR applies. Declare a tier, or opt out with `GuardianPolicy(treat_undeclared_tier_as=None)` (see `NEXUS/CHANGELOG.md`). Repo examples are unchanged.
- **`nexus-score --v03-checks`:** exits 1 on a failed check and 2 on missing evidence. CI installs OPA, so evidence is present.
- **MCP scores:** servers that relied on self-attestation or unvalidated OAuth metadata will score lower. Do not rely on grades published before this change.
- **Skill path:** links to the old blob URL `skills/SKILL.md` now 404. The folder URL still resolves.

## Evidence

- **Local CI mirror (`gates.sh`):** 30/30 PASS. It covers:
  - all test suites
  - example verification
  - build and clean-wheel release qualification
  - OPA 0.65.0 and 1.4.2
  - ruff, semgrep, and gitleaks across full history
  - repo UX and v3.1 consistency checks
- **Hosted CI at `21a8333`:** 39 checks succeed. 2 advisory checks were skipped because the PR was a draft. CodeQL reports no new alerts.
- **Development receipt** (`receipt/development-receipt.json`): `safe2 dev verify` reports integrity valid. Status is **`review_required`**: 23 of 27 required evidence items are supported. The four open items are human review, codeowner review, specialist security review and the release decision. Those belong to the owner.
- **Self-assessment boundary (AGENTS.md §4.2):** none of this is independent validation.

## Residual risk

- Guardian's ACT tier is still asserted by the caller (follow-up PR).
- Pattern detectors are a floor; paraphrased or novel payloads can pass.
- AgBOM signatures are a stub until ML-DSA-65 signing ships.
- No live `docker compose up` was run.
- `capture-pytest` cannot launch a symlinked venv interpreter. Those tests skip in venvs and run in CI.

## Rollback

Each module is an independent commit. To roll one back, revert its commit, then run
`tests/battery/run.py --areas <area>` to see which cases regress.

## Reproduce

See `docs/assessments/2026-10-06-false-assurance/RUNBOOK.md`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_011296BYhzy5JjGSp7A6w17r
