# Game Developer Quickstart

## What the developer receives

The starter adds policy and evidence files. It does not replace the engine,
build system, Claude configuration, Codex configuration, or repository tests.

## Installation

1. Copy `repository-template/` to the game repository.
2. Copy `profiles/game.json` to `.ai-safe2/profiles/game.json`.
3. Replace the owner placeholders in `.ai-safe2/workflow.json`.
4. Enter the actual build, test, lint, and packaging commands.
5. Validate the package and generate the repository-specific explanation:

   ```bash
   python scripts/validate_workflow.py --root .
   python scripts/explain_workflow.py \
     --workflow .ai-safe2/workflow.json \
     --profile .ai-safe2/profiles/game.json \
     --output AI-SAFE2-DEVELOPER-WORKFLOW.md
   ```

6. Read `AI-SAFE2-DEVELOPER-WORKFLOW.md` and confirm the routes, trust
   boundaries, owner, review options, and limitations match the game.
7. Commit the setup through a normal pull request.

The starter GitHub workflow verifies the pinned CLI, creates the deterministic
route, runs CLI decision routing, initializes the revision-bound human decision
record to `hold`, repeats the repository explanation, and uploads those
artifacts. A green validation proves that these required records were produced
and that the configuration is internally consistent. It does not prove that an
optional AI reviewer ran or that the game is secure or ready to release.

## What changes after installation

| Before | After |
|---|---|
| The same review habit may be used for every change | Documentation, gameplay code, and critical trust-boundary changes can take different routes |
| Claude, Codex, and scanners can produce disconnected comments | Results can be retained as attributed, revision-bound evidence |
| A missing reviewer may be easy to overlook | Failed, unavailable, and stale evidence do not satisfy a required capability |
| “Checks passed” can sound like release approval | The workflow stops at `ready_for_human_decision`; a named human decides |

Start with the route and deterministic checks. Add planning, semantic review,
security review, or runtime governance only where the repository's risks and
goals justify them. See the [Adoption Guide](ADOPTION-GUIDE.md) for the module
menu and tradeoffs.

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

