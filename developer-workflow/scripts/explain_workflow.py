#!/usr/bin/env python3
"""Generate a repository-specific explanation of the installed workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render(workflow: dict, profile: dict) -> str:
    route_rows = []
    for name in ("standard", "enhanced", "critical"):
        route = workflow["routes"][name]
        required = ", ".join(f"`{item}`" for item in route["required_capabilities"])
        route_rows.append(
            f"| {name.title()} | {required} | "
            f"{route.get('semantic_review', 'not specified')} | "
            f"{route.get('security_review', 'not specified')} |"
        )
    route_table = "\n".join(route_rows)

    critical = "\n".join(f"- `{item}`" for item in profile["critical_patterns"])
    enhanced = "\n".join(f"- `{item}`" for item in profile["enhanced_patterns"])
    lenses = "\n".join(f"- {item}" for item in profile["lenses"])
    providers = workflow.get("providers", {})
    provider_lines = "\n".join(
        f"- **{capability.replace('_', ' ').title()}:** "
        + ", ".join(values)
        for capability, values in providers.items()
    ) or "- No optional providers are configured."

    return f"""# AI SAFE2 Developer Workflow in this repository

Generated from the repository's current workflow and profile configuration.
Regenerate this file after either configuration changes.

## What changed

This repository now has a deterministic pull-request route, revision-bound
evidence contracts, and a human decision boundary. The workflow may report
`hold` or `ready_for_human_decision`. It cannot merge, release, deploy, or
accept risk.

| Before | Now |
|---|---|
| Review depth could depend on habit or provider availability | Changed paths select a configured route |
| Results could be scattered across CI and review comments | Evidence has a producer, capability, status, and subject revision |
| A missing reviewer could be mistaken for success | Failed, unavailable, and stale evidence do not satisfy requirements |
| AI output could appear authoritative | A named human retains the final decision |

## Active configuration

- **Workflow:** `{workflow["workflow_id"]}`
- **Profile:** `{profile["profile_id"]}` ({profile["name"]})
- **Decision owner:** `{workflow["decision_owner"]}`
- **Minimum AI SAFE2 CLI:** `{workflow["minimum_cli_version"]}`

| Route | Required evidence capabilities | Semantic review | Security review |
|---|---|---|---|
{route_table}

## What is treated as critical

{critical}

## What receives enhanced review

{enhanced}

## Review lenses

{lenses}

## Optional providers named by this configuration

{provider_lines}

A provider listed here is configured as an option. This report does not prove
that credentials exist, that the provider ran, or that an adapter produced
valid evidence.

## What happens on a pull request

```mermaid
flowchart LR
    PR[Pull request] --> R[Classify changed paths]
    R --> E[Determine required evidence]
    E --> C[Collect configured evidence]
    C --> D{{Complete for this revision?}}
    D -->|No| H[Hold and disclose gaps]
    D -->|Yes| HD[Ready for human decision]
    HD --> O[Named human decides]
```

## Current preview boundary

The installed contract preview classifies changes and creates a replayable
route artifact, a CLI decision-routing result, a human decision record, and
this explanation. The human record starts at `hold`. The preview does not
automatically convert every repository CI result into evidence unless this
repository adds an evidence bridge. Without complete evidence, `hold` is the
correct result.

## Ways to extend this repository

- Add deterministic test, build, scanner, and smoke-test evidence first.
- Add Superpowers or another method module for stronger planning, debugging,
  test-first work, and completion verification.
- Add Codex or Claude semantic review for non-trivial engineering changes.
- Add Codex Security, Claude security review, CodeQL, Semgrep, or Gitleaks for
  security-sensitive boundaries.
- Use a strategic reviewer selectively for major integrations or releases.
- Add runtime evidence when agents, tools, delegated authority, or production
  actions are in scope.

Each addition should declare its permissions, data boundary, version, failure
behavior, output contract, and whether it observes, recommends, enforces
existing policy, or authorizes. Bundled adapters must not authorize.

## Verify the installation

1. Confirm the critical and enhanced paths match this repository.
2. Replace any placeholder owner or command.
3. Run the package validator and self-tests.
4. Open representative documentation, code, and critical-path pull requests.
5. Verify each route and inspect the uploaded route artifact.
6. Confirm missing or failed evidence leaves the decision at `hold`.
7. Record the final human decision separately.

## Tradeoffs

The workflow improves consistency, evidence quality, and provider independence.
It also requires policy maintenance, pinned upgrades, capability mapping, and a
human owner. More rigorous routes can add time and cost. Installation alone is
not evidence that the repository is secure, compliant, or ready to release.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    content = render(load(args.workflow), load(args.profile))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

