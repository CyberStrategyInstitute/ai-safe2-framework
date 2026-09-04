# safe2 CLI consolidation

PART 3 diagnosis: *"Two failed release rounds. Parallel half-builds compete
with each other."* This is that consolidation. Before this change, four
CLI-shaped security tools existed in this repo, none installable from the
repo root, none aware of each other:

| Old location | What it did | New home |
|---|---|---|
| `scanner/` (no console entry point at all) | 161-control static project audit | `safe2 scan project` / `safe2 gate project` / `safe2 score project` |
| `scripts/skill_trust_gate.py` (loose script, no package) | Skill package trust gate | `safe2 scan skill` / `safe2 gate skill` |
| `examples/mcp-security-toolkit/` (filed as an *example*; `mcp-score`, `mcp-scan`, `mcp-safe-wrap`, 134 tests) | MCP server static/remote scanning + runtime wrapping | `safe2 scan mcp` / `safe2 score mcp` / `safe2 gate mcp` / `safe2 mcp wrap-stdio` / `safe2 mcp wrap-proxy` |
| `gateway/` (separate `ai-safe2-gateway` package) | Runtime enforcement proxy | `safe2 serve` (thin launcher; still its own package, now reachable through one entry point) |

One package now, `ai-safe2`, one console script, `safe2`, with operational
groups for scanning, gating, scoring, reporting, MCP protection, attributed
evidence collection, AISM decision support, and executable examples.

## Agent-facing AISM and evidence additions

- `safe2 aism init|ingest|score|compare` implements the documented 5-pillar by
  6-dimension AISM calculation and preserves the Low/Medium/High cell rubric.
- JSON is the canonical agent contract. Markdown and self-contained HTML
  Decision Cards are human views generated from the same result.
- Facts, assumptions, conflicts, unknowns, impacts, alternatives, history, and
  recommendations remain separate fields.
- Probability inputs require an outcome, time horizon, method, confidence, and
  range. The engine emits `NOT ESTIMABLE` rather than inventing a probability.
- `safe2 evidence nexus` collects attributed static or read-only runtime NEXUS
  evidence without claiming conformance.
- `safe2 evidence skillspector` consumes NVIDIA SkillSpector's JSON contract as
  an optional independent provider without implying NVIDIA endorsement.
- `safe2 example list|verify` inventories the repository's executable example
  surfaces and validates versioned example manifests.

AI SAFE² remains 161 controls and CP.1 through CP.10. UAS is identified as the
`UAS-1.0` regulatory profile extension with 27 profile requirements; it does not
increase the core control count or create CP.11 as a core Cross-Pillar control.

## Ship criterion (met)

```
git clone <repo>
cd ai-safe2-framework
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
pytest tests/ scanner/tests/
```

The consolidated suite includes the original 214 tests plus AISM, UAS profile,
NEXUS evidence, SkillSpector adapter, and executable-example tests. Run it rather
than relying on a fixed historical count:

```
pytest tests/ scanner/tests/
```

The suite includes `tests/test_cli_smoke.py` and
`tests/test_skill_gate_engine.py`, the original `scanner/tests/`, and the
original MCP toolkit suite (`tests/mcp_toolkit/`, moved unchanged from
`examples/mcp-security-toolkit/tests/` except for five path-resolution
fixes — see below).

## What actually changed in the code, vs. what's just new glue

- `scanner/` and `aisafe2_mcp_tools/` (moved from `examples/mcp-security-toolkit/src/`)
  are **unmodified business logic**, imported as-is. `safe2` does not
  reimplement any detection rule, scoring check, or injection pattern —
  it only adds CLI wiring, a shared exit-code contract, and a markdown
  renderer (the one format none of the four originals produced).
- `scripts/skill_trust_gate.py`'s two functions (`scan`, `decision_for`)
  were copied into `safe2/engines/skill_gate.py` unchanged, so `safe2 scan
  skill` / `safe2 gate skill` and the original script share the same rules
  by construction, not by two copies staying in sync by hand. The original
  script still works (kept for anyone with existing automation against it)
  and now prints a deprecation notice.
- Five tests in the migrated `tests/mcp_toolkit/` suite hardcoded a path
  relative to the old `examples/mcp-security-toolkit/tests/` location to
  find the `scan/fixes/*.template` directory. Fixed to resolve the fixes
  directory from the installed `aisafe2_mcp_tools.scan` package location
  instead of a relative-to-test-file guess — this is a real fix, not a
  skip; all five now pass in the new layout.

## Exit-code contract (new — see `safe2/commands/gate.py`)

The three old tools each had their own gate semantics: `skill_trust_gate.py`
returned bare 0/2, `mcp-scan --ci` and `mcp-score --ci-fail-below` both used
bare 0/1, and `scanner/cli.py`'s tier logic was a fourth variant. `safe2
gate *` now uses one contract everywhere: 0 pass, 1 fail/reject, 2 hold for
review (skill gate only), 3 input error. Update any CI pipeline that was
shell-scripted against the old bare 0/1 assumptions.

## Backward compatibility

`pip install ai-safe2` still installs `mcp-score`, `mcp-scan`, and
`mcp-safe-wrap` as console scripts (pointed at the same underlying code),
so the old README's `pip install aisafe2-mcp-tools` instructions don't
break anyone already using them. They're marked deprecated in favor of
`safe2 scan mcp` / `safe2 score mcp` / `safe2 mcp wrap-*`.

## Deliberately out of scope this pass

- **`skills/mcp/` (the AI SAFE2 MCP *knowledge* server — `ai-safe2-mcp`,
  exposing the 161 controls as MCP resources/tools).** This is a different
  product from the MCP *Security Toolkit* absorbed above, despite the
  similar name, and folding it into `safe2 mcp serve` without a full
  read-through of its 388-line `app.py` would mean claiming an integration
  that wasn't actually verified. `safe2 mcp serve` is a stub that says so
  and points at the existing `ai-safe2-mcp` console script. Natural next PR.
- **`gateway/`'s internals.** `safe2 serve` launches it via `uvicorn
  gateway.main:app` (real, not faked) behind the optional `gateway` extra,
  but its 1288-line `main.py` and `provider_adapters.py` were not
  refactored into the safe2 package — it stays a separate, larger service
  reached through one entry point rather than merged code.

## To finish the migration in the real repo

This was built and tested in a local clone; nothing has been pushed. Once
reviewed:

```
git add safe2/ aisafe2_mcp_tools/ pyproject.toml MIGRATION.md \
        scripts/skill_trust_gate.py examples/mcp-security-toolkit/README.md \
        tests/
git commit -m "Consolidate scanner, skill trust gate, and MCP toolkit into one safe2 CLI"
```

Leave `examples/mcp-security-toolkit/src` and `scripts/skill_trust_gate.py`
in place until you're satisfied the new paths are solid in production, then
`git rm -r examples/mcp-security-toolkit/src` (keep its README's redirect
notice, or remove the whole directory) and the deprecated script.

## Known pre-existing scanner limitation (not introduced by this change)

Running `safe2 scan project` against `safe2/` itself surfaces false
positives from the 161-control heuristics — e.g. it flags
`subprocess.call(["uvicorn", ...])` in `safe2/cli.py` as "LLM API call
without logging context." The pattern-matching is keying on generic
subprocess/call shapes, not actual LLM API usage. This is an existing
characteristic of `scanner/rules/`'s heuristics, unchanged by this
consolidation — worth a follow-up pass on the P4/P5 rule precision, flagged
here rather than silently left for someone to rediscover.
