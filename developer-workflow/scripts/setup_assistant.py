#!/usr/bin/env python3
"""Generate a bounded, goal-based Developer Workflow setup plan."""

from __future__ import annotations

import argparse
from pathlib import Path


MODULES = {
    "planning": {
        "prompt": "Do you want stronger planning, debugging, and verification methods?",
        "tool": "Superpowers",
        "steps": [
            "Review the upstream project and its permissions before installation.",
            "Pin the reviewed commit in `upstreams.lock.json`; never run from a moving branch.",
            "Install only the methods needed by the repository or agent environment.",
            "Use the methods for planning, test-first work, debugging, and verification.",
            "Keep test and decision evidence separate; a method cannot approve a change.",
        ],
    },
    "deterministic-security": {
        "prompt": "Do you want repeatable security checks on pull requests?",
        "tool": "CodeQL, Semgrep CE, and Gitleaks",
        "steps": [
            "Enable CodeQL using default setup or a SHA-pinned advanced workflow.",
            "Add a pinned Semgrep CE scan with repository-owned rules and triage its baseline.",
            "Add a pinned Gitleaks binary or action and enable redaction.",
            "Run clean and deliberately failing fixtures for every scanner.",
            "Map results to revision-bound evidence; skipped or unavailable is not `produced`.",
        ],
    },
    "semantic-review": {
        "prompt": "Do you want routine AI-assisted pull-request review?",
        "tool": "PR-Agent with OpenRouter; Codex or Claude as alternatives",
        "steps": [
            "Create a bounded OpenRouter key with an expiry and spending limit.",
            "Add it under repository Actions secrets as `OPENROUTER_API_KEY`; never commit it.",
            "Adapt the SHA-pinned PR-Agent/OpenRouter reference workflow and preflight policy.",
            "Use live catalog and endpoint checks instead of hard-coded availability claims.",
            "Open a non-draft code PR and verify substantive review of the exact head commit.",
            "Inspect receipts and preserve `degraded`, `unavailable`, and `failed`.",
            "Add `OPENAI_KEY` only as an intentional metered fallback with confirmed capacity.",
        ],
    },
    "security-review": {
        "prompt": "Do you want specialized AI security review for sensitive changes?",
        "tool": "Codex Security or Claude security review",
        "steps": [
            "Review the provider's repository access, data boundary, retention, and permissions.",
            "Bind the reviewer to enhanced or critical routes, not documentation-only changes.",
            "Define the security policy and trust boundaries the reviewer must use.",
            "Test a representative sensitive diff and bind findings to the current revision.",
            "Validate findings before fixing them; retain limitations and unresolved risk.",
            "Keep merge, release, exception, and risk authority with the named human.",
        ],
    },
    "strategic-review": {
        "prompt": "Do you want independent review at major integration or release points?",
        "tool": "Greptile",
        "steps": [
            "Install the GitHub App only for approved repositories and inspect its permissions.",
            "Choose a bounded trigger: major integration/release, label, or explicit request.",
            "Disable draft reviews and avoid all-event reviews when credits are constrained.",
            "Freeze the candidate head, request one review, and verify the reviewed commit.",
            "Resolve valid findings, rerun first-party checks, and retain provider limitations.",
            "Skip routine text, image, link, and low-impact documentation changes by default.",
        ],
    },
    "runtime": {
        "prompt": "Does the repository operate agents, tools, delegated authority, or consequential actions?",
        "tool": "NEXUS, MCP controls, and a matching runtime adapter",
        "steps": [
            "Identify the full model-plus-harness system, enforcement plane, tools, and authority.",
            "Select only adapters that match those boundaries; a manifest is not execution.",
            "Keep policy, enforcement, evidence collection, and presentation separable.",
            "Test authorization, delegation, stale evidence, interruption, rollback, and outages.",
            "Bind receipts to the deployed version, configuration, environment, and owner.",
            "Treat runtime evidence as deployment-specific; source review cannot replace it.",
        ],
    },
}


def ask(prompt: str, *, default: bool = False) -> bool:
    answer = input(prompt + (" [Y/n] " if default else " [y/N] ")).strip().lower()
    return default if not answer else answer in {"y", "yes"}


def render_plan(selected: set[str]) -> str:
    unknown = selected - set(MODULES)
    if unknown:
        raise ValueError("unknown setup goals: " + ", ".join(sorted(unknown)))
    rows = []
    sections = []
    for goal, module in MODULES.items():
        rows.append(
            f"| {goal.replace('-', ' ').title()} | "
            f"{'Selected' if goal in selected else 'Not selected'} | {module['tool']} |"
        )
        if goal in selected:
            tasks = "\n".join(f"{index}. {step}" for index, step in enumerate(module["steps"], 1))
            sections.append(f"### {module['tool']}\n\n{tasks}")
    optional = "\n\n".join(sections) or (
        "No optional modules were selected. Add one later through an isolated setup pull request."
    )
    return f"""# AI SAFE2 Developer Workflow setup plan

This plan was generated from explicit repository goals. It does not install a
service, create an account, add a credential, change repository settings, or
authorize merge or release.

## Required core — always install

1. Install and verify the pinned AI SAFE2 CLI.
2. Copy the repository template and replace every `REPLACE-*` value.
3. Customize critical and enhanced paths for this repository.
4. Run `validate_workflow.py`, `safe2 self-check --strict`, and repository tests.
5. Open a setup PR and verify documentation, code, and critical-path routes.
6. Confirm CLI and human decision records bind to the exact revision.
7. Keep `hold` until every required capability has truthful evidence.

## Selected outcomes

| Outcome | Selection | Suggested module |
|---|---|---|
{chr(10).join(rows)}

## Optional module tasks

{optional}

## Supply-chain tasks — always apply

1. Record each external repository, action, package, and service in `upstreams.lock.json`.
2. Pin actions to SHAs and packages to reviewed versions or digests.
3. Use Dependabot or Renovate to propose isolated update PRs.
4. Never promote a moving upstream branch or let an adapter approve its own update.
5. Rerun compatibility, security, and adversarial fixtures before promotion.

## Acceptance check

- Core route and decision artifacts exist for the current revision.
- Each selected provider is `produced`, `failed`, `unavailable`, or `not_requested`.
- Required evidence names its producer, scope, and exact subject revision.
- Credentials exist only in the approved secret store.
- A named human remains the merge, release, deployment, policy, and risk owner.

See `developer-workflow/docs/TOOL-SETUP-GUIDE.md` for detailed setup and verification.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goals", help="Comma-separated goals: " + ",".join(MODULES))
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.interactive and args.goals:
        parser.error("choose either --interactive or --goals")
    if args.interactive:
        selected = {
            goal
            for goal, module in MODULES.items()
            if ask(module["prompt"], default=goal == "deterministic-security")
        }
    else:
        selected = {item.strip() for item in (args.goals or "").split(",") if item.strip()}
    try:
        content = render_plan(selected)
    except ValueError as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
