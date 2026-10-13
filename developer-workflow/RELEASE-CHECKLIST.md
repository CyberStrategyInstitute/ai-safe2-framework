# Release Checklist

## Completed for 0.1.0

- [x] Core, CLI, product-surface, and adapter boundaries documented
- [x] AI SAFE2 CLI pinned to 1.0.1
- [x] MIT license includes a standalone SPDX identifier
- [x] Claude and Codex use the same repository policy without configuration takeover
- [x] Game profile included
- [x] MCP Pro and Agency Check integration boundaries documented
- [x] NEXUS, Sovereign Runtime, and Drift/Love Equation registered
- [x] Adapter, evidence, and decision schemas added
- [x] Provider failure cannot satisfy a required review
- [x] Human authority remains explicit
- [x] Upstream dependency policy documented
- [x] Contract tests passed
- [x] JSON schemas validated against bundled examples
- [x] Terminal approvals require an attributable human decision record
- [x] Evidence completeness is capability- and revision-bound
- [x] Starter CI emits a replayable route artifact on every pull request
- [x] Canonical evidence digest semantics documented

## Adoption experience added after 0.1.0

- [x] Before/after value is visible before installation
- [x] Architecture and pull-request flow diagrams are included
- [x] Folder structure and delivered components are explained
- [x] Optional planning, code-review, security-review, and runtime modules are
  separated by capability and status
- [x] Repository-specific workflow explanation can be generated locally
- [x] Starter CI publishes that explanation in its summary and as an artifact
- [x] Starter CI verifies the pinned AI SAFE2 CLI and emits both CLI routing
  and human decision records for the exact revision
- [x] Explanation generation has a release/template parity contract test
- [x] New users can generate a goal-based setup plan without enabling external
  services or adding credentials
- [x] OpenRouter/PR-Agent, Greptile, planning, security, runtime, and upstream
  setup tasks have one linked owner/maintainer/acceptance guide
- [ ] Validate the onboarding flow in a clean external canary repository
- [ ] Add mobile, API/service, and AI-agent profiles only after each has a
  tested canary and documented trust boundaries

## Repository owner before publishing

- [ ] Choose the GitHub repository name and visibility
- [ ] Replace `REPLACE-*` placeholders in the repository template
- [ ] Confirm public terminology for Sovereign Runtime and Drift/Love Equation
- [ ] Confirm whether `agency-check.app` is ready to be named publicly
- [ ] Add repository description, topics, and support contact
- [ ] Enable branch protection and secret scanning
- [ ] Create a signed or annotated `v0.1.0` tag
- [ ] Attach the release archive and checksums
- [ ] State clearly that unimplemented adapters are manifests, not delivered execution

