# AI SAFE² Skill Screening Demo

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Evidence](https://img.shields.io/badge/Evidence-Skill_Screening-820F1A?style=flat-square)](./SKILL-SCREENING-DEMO.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Before starting

Install safe2 and the separately pinned provider using the
[runtime setup guide](./PYTHON-COMPATIBILITY.md). Use a trusted scanner executable
outside the candidate directory. Do not install candidate dependencies or execute
candidate scripts to scan them. Prefer a disposable, credential-free environment;
enforce network restrictions separately if required. `--no-llm` is not a firewall.

The following PowerShell walkthrough runs from a clone. On Linux/macOS use your
shell's variable syntax and replace `Scripts/skillspector.exe` with `bin/skillspector`.

## 1. Learn what good and bad controls look like

```powershell
$provider = (Resolve-Path .venv-skillspector/Scripts/skillspector.exe).Path
safe2 gate skill tests/fixtures/skillspector-live/clean --strict
safe2 gate skill tests/fixtures/skillspector-live/hostile --strict
safe2 evidence skillspector tests/fixtures/skillspector-live/clean --no-llm --executable $provider --output clean-evidence.json
safe2 evidence skillspector tests/fixtures/skillspector-live/hostile --no-llm --executable $provider --output hostile-evidence.json
```

Expected native decisions: APPROVE/exit 0 and REJECT/exit 1. The pinned live provider
returned zero versus seven issues. Provider results may change with dependencies;
record rather than assume exact scores. The evidence command returns 0 when
collection succeeds even when the provider says DO_NOT_INSTALL. Inspect the JSON.

## 2. Use our repository as the difficult example

```powershell
safe2 scan skill ./skills
safe2 evidence skillspector ./skills --no-llm --executable $provider --output own-skill-evidence.json
```

This is intentionally not a promised green demo. It includes an MCP implementation,
documentation, and adversarial test strings. Our second pass returned 50 provider
issues, many context-dependent matches, plus partial coverage. Review the
[findings and lessons](./SKILL-SCREENING-SECOND-PASS.md), not just the headline score.
Scan the exact package you intend to distribute; development caches and missing
external references can change coverage. Do not remove security tests to improve a score.

## 3. Point it at a candidate

```powershell
$candidate = 'C:/quarantine/candidate-skill'
safe2 gate skill $candidate --strict
$gateExit = $LASTEXITCODE
safe2 evidence skillspector $candidate --no-llm --executable $provider --output candidate-evidence.json
$collectionExit = $LASTEXITCODE
```

Keep candidate bytes quarantined until review. A nonzero native gate exit blocks
unattended use; a zero evidence-collection exit only means evidence was collected.
Missing provider, partial coverage, changed bytes, timeout, or unknown findings
require review, not automatic approval. Save outputs outside the candidate.

## 4. Preserve evidence and record a decision

```powershell
safe2 evidence manifest candidate-evidence.json --subject-id candidate-review --output candidate-manifest.json --strict
safe2 aism ingest candidate-evidence.json --subject-id candidate-review --subject-name "Candidate skill review" --output candidate-assessment.json
```

Use new filenames for each review. AISM starts with unscored maturity cells.
For each material finding, record source location, exact package hash, observed
behavior, intended use, reviewer, rationale, expiry, and residual risk. Separate
false detection, intentional authorized behavior, accepted risk, and incomplete
coverage. Do not edit the provider's original result to make a decision look clean.

## Continuous use: integration design, not an installed background service

The CLI does not intercept every harness, download, clipboard, or context message.
No watcher or global interception was installed by this work. Choose explicit,
consented locations and enforcement points:

| Event | Enforcement point | Important limitation |
|---|---|---|
| Skill created or edited | CI and pre-activation gate | A filesystem watcher alone runs after the write |
| Download or installation | Package-manager/harness pre-install hook; quarantine first | Download completion is not authorization to activate |
| Existing skill changed | Hash change invalidates approval; re-scan before next load | Debouncing must not leave a stale approval usable |
| Skill loaded by an agent | Mandatory pre-load check on exact bytes | A prompt asking the agent to scan is advisory, not enforcement |
| Text pasted into context | Harness pre-context hook, before model delivery | Filesystem watchers cannot see clipboard/context-only input |

Do not globally collect clipboard contents. A pasted-text check must be user/harness
initiated and run before admission, with data minimization and retention controls.
For today's manual workflow, save only the candidate text into a dedicated review
file and scan its containing directory; this does not validate referenced code or
retroactively protect context already delivered to a model.

Recommended next build: a small admission service with per-harness adapters. Its
receipt binds the package digest, scanner and policy versions, completeness,
reviewer decisions, expiry, and permitted use. Store receipts outside candidate
control. Cache only exact matches; changed bytes or rules invalidate the receipt.
Run the native gate quickly and the provider asynchronously while the candidate
stays quarantined. Missing/stale receipts deny unattended activation. Watchers
notify; pre-load hooks enforce. Notify humans on actionable changes, not every
unchanged scan. This service and trusted disposition processing are proposed,
not implemented by the current CLI.

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
