# 🟠 SAFE2 CLI 0.3.0 — Task receipts, test evidence, and usage visibility

AI SAFE² Framework remains v3.1. This release updates the CLI, not the framework's 161-control core.

[CLI guide](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md) · [Task-receipt walkthrough](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/TASK-RECEIPTS.md) · [Framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)

## 🟢 What changes

“Done” is a claim. This update helps humans and agents inspect the evidence behind it—and see the resource use attributed to individual tasks.

| Before this update | With CLI 0.3.0 |
|---|---|
| Workflow friction records describe reported outcomes | Task receipts evaluate explicit artifact and test/tool criteria |
| Process success and test success need separate interpretation | Fresh pytest capture associates observed process exit with a new JUnit report |
| A saved verdict must be manually checked | Standalone verification recomputes hashes, bindings, and the narrow test assessment |
| Report authorship is not authenticated by a hash | Optional expiring Ed25519 signatures authenticate report bytes against an operator-trusted key |
| Per-task usage declarations are difficult to compare | Usage correlation preserves parent/child relationships, rejects duplicate event ownership, and separates reported, estimated, and unknown values |

## 🧰 New commands

| Command | Purpose |
|---|---|
| `safe2 feedback receipt` | JSON or Markdown evidence receipt |
| `safe2 feedback usage` | Correlate declared per-task resource use |
| `safe2 feedback import-junit` | Normalize bounded, supported JUnit XML |
| `safe2 feedback capture-process` | Explicitly run and observe a local command |
| `safe2 feedback capture-pytest` | Run selected tests and capture fresh test evidence |
| `safe2 feedback verify-pytest` | Recheck a capture without executing code |
| `safe2 feedback sign-report` | Create a detached test/tool report signature |
| `safe2 feedback verify-report` | Check a signature against a supplied trusted key |

Seven versioned JSON contracts and packaged examples support automation. Existing friction commands remain available.

Challenge documentation and regression tests now make the outage fixture's scope
explicit: valid translation and legitimate shared-write completion do not certify
protected-action fail-closed behavior. Provider disagreement is preserved. No
challenge protocol, grader, or reference outcome was changed for a provider.

## 🔎 Read the result correctly

- **Supported:** the narrow criterion matches the available evidence.
- **Contradicted:** applicable evidence conflicts with that criterion.
- **Unverifiable:** evidence is missing, incomplete, unsafe, or inapplicable.

Missing evidence is not proof of deception. A successful process is not proof tests passed. Passing tests are not proof the entire task is complete.

`verify-pytest` exit 0 means internal consistency, including a consistent record of failure. Check the returned test assessment separately. Signatures authenticate bytes, not truthful execution; capture bundles are not yet accepted by `sign-report`.

## 🛡️ Security and scope

Explicit process execution requires `--execute`, an absolute executable path, and a new output file. Captures use bounded output and minimal inherited environment variables, and do not retain raw process output. Imported reports use strict JSON/XML validation and bounded reads.

Local execution still runs with the user's permissions. It is **not a sandbox**, does not isolate descendants or network access, and does not prevent a malicious same-user process from fabricating evidence. Hashes are not signatures.

Usage remains source-declared—not verified billing, subscription-quota allocation, or a dollar-cost guarantee. No new universal Codex/Claude/Hermes hooks or Headroom adapter are included. No new SkillSpector fix or NVIDIA endorsement is claimed.

## ➡️ Start here

Install from the merged repository using its [installation guide](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md), then follow the [copyable receipt and capture examples](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/TASK-RECEIPTS.md). Python 3.11–3.14 are supported; the separately installed SkillSpector provider requires its own compatible runtime.

Next priorities: externally isolated execution, source/environment snapshots, provider usage reconciliation, and opt-in harness adapters. These are roadmap items, not capabilities delivered in 0.3.0.
