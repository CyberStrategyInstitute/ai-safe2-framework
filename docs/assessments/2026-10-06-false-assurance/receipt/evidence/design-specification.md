# fix: close false-assurance defects across skills gate, MCP toolkit, CLI, and NEXUS

**Draft.** Self-assessed. Requires owner review. Not a conformance claim.

## Problem

A four-area adversarial battery found that AI SAFE² components told users things were
safe, compliant, or blocked when they were not. Representative cases on `main`
(`83de4a8`):

- **MCP scorer:** a server whose tool description instructs credential theft scored
  **87/100 "Acceptable"**, earned the badge, and passed `safe2 gate mcp --ci-fail-below 70`.
  It did so with a self-published attestation file, an empty `{}` OAuth metadata
  document, and a 429 response. An honest server scored 63.
- **Skill trust gate:** approved **9 of 16** hostile skills.
- **Project gate:** passed Tier2 at **90/100** on code that runs `shell=True` and
  `eval()` on LLM output.
- **MCP knowledge server:** did not start on a documented install (`mcp` 2.x removed
  FastMCP).
- **NEXUS Guardian:** allowed **24** evasions. Examples: `id_ed25519`, Windows paths,
  `%2e%2e%2f`, IMDS as a decimal or hex IP, key bytes in arguments, `curl | sh`, and
  ACT-4 reasoning of `"x"`.
- **NEXUS AgBOM:** a component edited inside a stored version verified as an intact
  chain. A rug-pulled manifest was registered as a second trusted server.
- **NEXUS OPA:** no policy compiled on OPA 1.x. The AISM policy failed type-checking on
  every version, and CI watched a non-existent `opa/` path. `authorize_tool_call` was
  undefined for 9 of 13 inputs. A `request` scope label downgraded a PERMANENT write.
  Deny rules never gated `allow`.
- **`nexus-score --v03-checks`:** printed **"10/10 verified, all v0.3 controls
  satisfied"** while the controls above were broken.

## Result: same battery, same harness (`tests/battery/`)

| | PASS | FAIL | NOT_RUN | INFO |
|---|---|---|---|---|
| `main` `83de4a8` | 61 | 60 | 1 | 1 |
| this branch | 124 | 0 | 0 | 1 |

Snapshots: `docs/assessments/2026-10-06-false-assurance/snapshots/`.

## Scope: one commit per module, each red on `main` and green here

| Commit | Module | Red → green evidence |
|---|---|---|
| `47c2dc8` | MCP knowledge server: starts on stdio/HTTP, auth, honest risk and code-review outputs | 9 of 11 new tests fail on previous revision |
| `06e523a` | MCP toolkit: score cannot be bought, gate fails on detected poisoning, scan coverage, wrap enforces | 19 of 21 new tests fail before |
| `8f3d038` | Skill trust gate (TG-013..024) and project gate (CRITICAL caps score) | 0/16 hostile approved (was 9/16) |
| `f3ecea0` | NEXUS OPA: Rego v1, always-defined decisions, most-restrictive scope, deny gates allow, CI | 8 of 11 authz tests fail on main; APay rewrite identical on 873/873 differential inputs |
| `5af8409` | Compose: real policy mounts; OPA healthcheck without curl | `docker compose config` resolves mounts; healthcheck exit 0/1/2 verified |
| `904e289` | Guardian: normalized arguments, 5 detectors, HEAR floor, undeclared tier treated as ACT-4 | 24 of 33 fail on main |
| `04f6192` | AgBOM: recomputed verification, isolated snapshots, rug-pull quarantine | 7 of 9 fail on main; hashes byte-identical for unquarantined components |
| `4f2cff2` | Memory Vaccine: stub drift labeled unmeasured | 4 of 4 |
| `7b85788` | nexus-score: behavioral checks, NOT ASSESSED state, exit codes | 2 of 2; old checker gives 10/10 on main, behavioral gives 7/10 |
| `2dac2ff` | Remote Guardian with no `httpx` no longer silently runs inline policy | 2 of 3; found by the new scorer in a clean venv |
| `3353be4` | Docs: stale skills redirect; Guardian and OPA notes | Broken links fixed |
| `5b38495` | CI: pinned, verified OPA in the compliance job; new `mcp-server` job; checksums in `opa.yml` | Clean-venv simulation of both jobs |
| `b24d040` | No key-shaped test literals; 3 historical fixture findings baselined | gitleaks full history: no leaks |
| `225f45b` `517357f` | Battery harness, runbook, ledger, state | Pytest collects 0 battery files; semgrep clean |

**Exclusions:**
- `skills/` package boundary (D1).
- v3.0 skill surfaces content refresh (D3).
- The NEXUS MCP adapter remains fail-closed scaffolding.
- No live `docker compose up` (no daemon in the assessment environment).

## Compatibility and breaking changes

- **Guardian:** an omitted `act_tier` is now treated as ACT-4, so HEAR applies. Callers
  must declare a tier, or opt out with `GuardianPolicy(treat_undeclared_tier_as=None)`.
  Documented in `NEXUS/CHANGELOG.md`. All repo examples already declared a tier; their
  decisions are unchanged.
- **`nexus-score --v03-checks`** exits non-zero on failure (1) or missing evidence (2).
  CI now installs OPA, so evidence is present.
- **MCP scores:** servers that relied on self-attestation or unvalidated OAuth metadata
  score lower. Previously published grades should not be relied on.
- AgBOM, APay, and memory APIs are additive and hash-compatible.

## Tests performed (local; hosted CI pending)

`docs/assessments/2026-10-06-false-assurance/gates.sh` mirrors the CI workflows:
**30/30 PASS** at `bfe324b`. Coverage:
- root, scanner, NEXUS, and `skills/mcp` suites
- example verify and smoke runs
- build and clean-wheel release qualification
- OPA 0.65.0 and 1.4.2 `check --strict`, `test`, and `fmt`
- ruff, semgrep, and gitleaks across full history
- repo UX, examples table, and v3.1 consistency checks

The OPA binaries used match the official release sha256.

## Security and evidence boundaries

- All results are self-assessment by the authoring agent. They are not independent
  validation (AGENTS.md §4.2).
- Greptile has not been run. Record its state when CI runs.
- Battery fixtures are inert (`.fixture` suffix); credentials are synthesized at run time.

## Residual risk and open decisions (owner: Vincent Sullivan)

- **D1:** `skills/` installs as one skill package that includes `skills/mcp` and its
  injection test corpus. The gate correctly rejects it.
- **D2:** publication of results, after merge.
- **D3:** six skill surfaces teach v3.0 content.
- **D4:** accept the undeclared-tier default for the next NEXUS release.
- AgBOM signing is still a stub. An attacker able to rewrite the full history can
  recompute it; real ML-DSA-65 signing closes that.
- Pattern-based detectors are a floor. Paraphrased injections can pass.

## Rollback

Each module is an independent commit. Revert a module's commit to roll it back. The
battery identifies which cases regress.

## Reproduce

See `docs/assessments/2026-10-06-false-assurance/RUNBOOK.md`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_011296BYhzy5JjGSp7A6w17r
