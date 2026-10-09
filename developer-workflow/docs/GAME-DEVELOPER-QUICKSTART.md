# Game Developer Quickstart

## What the developer receives

The starter adds policy and evidence files. It does not replace the engine,
build system, Claude configuration, Codex configuration, or repository tests.

## Installation

1. Copy `repository-template/` to the game repository.
2. Copy `profiles/game.json` to `.ai-safe2/profiles/game.json`.
3. Replace the owner placeholders in `.ai-safe2/workflow.json`.
4. Enter the actual build, test, lint, and packaging commands.
5. Commit the setup through a normal pull request.

## Game-specific review lenses

- deterministic simulation and replay;
- save-file integrity and migration;
- client/server trust and authoritative state;
- multiplayer abuse and anti-cheat boundaries;
- economy, inventory, purchase, and entitlement correctness;
- user-generated content and moderation boundaries;
- asset and dependency provenance;
- frame-time, memory, loading, and device constraints;
- platform permissions, privacy, and telemetry;
- build signing, store packaging, and rollback.

## Claude and Codex together

- Claude may plan or implement one task while Codex reviews another.
- Do not allow one provider's success to satisfy another required capability.
- Record the provider, model when known, reviewed commit, scope, and result.
- If both review the same change, retain both results and reconcile conflicts.
- A provider failure is disclosed as unavailable or failed. It is not a clean
  review.

## Suggested first pull request

Use a small, reversible change with tests. The pull request should demonstrate:

1. classification;
2. deterministic evidence;
3. one optional semantic review;
4. a completion receipt;
5. a named human decision.

Do not start with payment, authentication, multiplayer authority, build
signing, or destructive save migration.

