# Threat model: false-assurance hardening (PR #393)

Scope: places where an AI SAFE² component makes a safety, compliance or
enforcement claim. The threat is not only an attacker getting through. It is
the tool *telling a human or a CI gate* that they did not.

## Assets

- CI and release decisions that consume gate exit codes and scores (`safe2 gate`, `safe2 score mcp`, `nexus-score`)
- Model context, which receives skill packages and MCP tool descriptions and outputs
- NEXUS enforcement decisions: Guardian verdicts, OPA authz, AgBOM chain state, Memory Vaccine write decisions
- Published grades, badges and self-checks that third parties may rely on

## Attacker and failure sources

| Source | Capability assumed | Representative battery cases |
|---|---|---|
| Hostile MCP server | Controls its tool catalog, outputs, headers, `.well-known` files and rate-limit behaviour | grade gaming via self-attestation, empty OAuth metadata, 429; poisoned descriptions; rug-pull after first `tools/list` |
| Hostile skill author | Controls every file in a skill package | paraphrased overrides, Unicode tag smuggling, homoglyphs, env exfil, obfuscated imports, persistence, trigger hijack |
| Compromised or manipulated agent | Chooses tool arguments and declared metadata (tier, reasoning, persistence scope) | encoded traversal, IMDS in numeric spellings, key material in args, `curl \| sh`, `act_tier` omitted or trivially justified, `request` scope on a durable write |
| Insider or storage tamper | Can edit stored AgBOM versions or evidence files | edited historical component, edited latest component, live edit rewriting history |
| Environment drift | Optional dependency or binary missing, wrong mount path, wrong CI path filter | remote Guardian without `httpx`, OPA 1.x syntax break, compose mount to a non-existent dir, CI watching `opa/**` |
| Assessment tooling itself | Stale processes, fixed ports, harness heuristics | stale server answering for main (found and fixed 2026-10-07), checker misreading negated text |

## Trust boundaries

1. MCP client ↔ untrusted MCP server (remote score, `wrap-stdio`, `wrap-proxy`)
2. Skill package ↔ model context (skill trust gate)
3. Agent tool call ↔ Guardian / OPA decision point
4. Stored AgBOM / evidence ↔ verifier
5. CI runner ↔ downloaded binaries (OPA, gitleaks: sha256-verified)

## Design rules applied

- **Fail closed on missing evidence.** NOT_RUN and NOT ASSESSED are distinct states and are never counted as a pass (battery, `nexus-score`).
- **Server- or caller-supplied claims never raise a score or lower a requirement.** This covers self-attestation, declared persistence scope and declared ACT tier (the undeclared tier is interim; registry-bound tiers are a follow-up).
- **Detection that does not gate is not enforcement.** A detected injection caps the score and fails the gate. Block mode withholds poisoned content.
- **Verification recomputes and does not trust stored digests** (AgBOM).
- **Every defect gets a test that is red on `main` and green on the branch.**

## Out of scope / residual

- Paraphrased or novel injections beyond the pattern libraries. Detectors are a floor.
- AgBOM signatures are a stub. A full-history rewriter can recompute hashes until ML-DSA-65 signing ships.
- Caller-asserted ACT tier (follow-up PR: tier bound to the registered AIM).
- No live `docker compose up` was exercised.
