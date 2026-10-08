# AI SAFE2 Developer Workflow

Version: 0.1.0 preview  
Minimum AI SAFE2 CLI: 1.0.1

AI SAFE2 Developer Workflow is a provider-neutral decision-evidence layer for
human and AI-assisted software development. It determines what evidence a
change needs, records what was actually produced for the exact revision, and
preserves a replayable record for the human who decides whether to merge or
release.

It does not replace Claude, Codex, Superpowers, tests, scanners, or human
review. It connects their outputs without granting them merge, release,
deployment, policy-change, or risk-acceptance authority.

## First release scope

This preview provides:

- a stable core boundary and adapter protocol;
- normalized evidence and human decision-record schemas;
- standard, enhanced, and critical change routes;
- a ready-to-customize game-development profile;
- manifests for Codex, Claude, security, deterministic, runtime, MCP Pro,
  Agency Check, Sovereign Runtime, and Drift/Love Equation adapters;
- provider-independent repository instructions for teams using both Claude
  and Codex;
- an upstream dependency inventory that favors pinned, isolated upgrades;
- validation and example decision-record generation scripts.

Provider execution remains opt-in. Installing this pack does not call an
external model or change a developer's Claude or Codex configuration.

## Product boundary

```text
AI SAFE2 Core
  policy + evidence + decision state + provenance + replay contracts

Surfaces
  CLI | NEXUS | Skills | MCP | SDK/API

Product workflows
  Developer Workflow | MCP Pro | Agency Check | future domain workflows

Adapters
  Codex | Claude | scanners | Sovereign Runtime | Drift/Love Equation | others
```

The CLI is the supported operator and CI interface to AI SAFE2 Core. It is not
the core itself. See [Architecture](docs/ARCHITECTURE.md).

## Five-minute game-developer setup

1. Install and verify AI SAFE2 in an isolated environment:

   ```console
   python -m pip install "ai-safe2[all]==1.0.1"
   safe2 --version
   safe2 self-check --strict
   ```

2. Copy `repository-template/` into the game repository.
3. Copy `profiles/game.json` into `.ai-safe2/profiles/game.json`.
4. Update repository owners and the project's real build and test commands.
5. Run:

   ```console
   python scripts/validate_workflow.py --root .
   ```

6. Open a setup pull request. Claude and Codex remain usable as they are. The
   workflow records their results only after their corresponding adapters are
   explicitly enabled.

See [Game Developer Quickstart](docs/GAME-DEVELOPER-QUICKSTART.md).

## Decision states

The workflow never converts silence into success:

- `produced`: expected evidence exists for the exact subject revision;
- `unavailable`: the provider could not be reached or used;
- `failed`: the provider ran but did not complete correctly;
- `not_requested`: policy did not require the provider;
- `hold`: evidence or human judgment is still required;
- `ready_for_human_decision`: required evidence is present, but no merge or
  release has been authorized.

## Release status

Version 0.1.0 is a stable contract preview for early adopters. It intentionally
does not claim automatic provider execution, automatic certification, or
independent validation. See [Current State and Release Gap](docs/CURRENT-STATE-AND-GAPS.md).

