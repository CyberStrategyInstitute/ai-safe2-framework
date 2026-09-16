# 🟠 AI SAFE² CLI 0.6.0: Know What Changed Before You Release

**SYSTEM IDENTITY • ASSESSMENT SCOPE • CHANGE ATTRIBUTION • RELEASE READINESS**

<p>
  <a href="#why-this-matters">Why It Matters</a> ·
  <a href="#before-and-after">Before and After</a> ·
  <a href="#whats-new">What's New</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#understand-the-result">Results</a> ·
  <a href="#security-boundaries">Security</a> ·
  <a href="#validation">Validation</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/329">Release PR</a>
</p>

---

<a id="why-this-matters"></a>
## 💡 Why should I care and use this now?

A scan can identify findings. It cannot tell you whether the scanner assessed
the right deployment boundary, whether a proposed change introduced the finding,
or whether the available evidence is sufficient for a release decision.

**CLI 0.6.0 connects those questions without replacing human authority.**

- Define the system and exact deployable scope under assessment.
- Separate inherited findings from introduced, changed, resolved, and unknown findings.
- Produce canonical agent JSON and a readable release-readiness card.
- Preserve failed checks, incomplete coverage, assumptions, residual risks, owners,
  rollback guidance, and missing evidence as distinct facts.

<a id="before-and-after"></a>
## 🔄 Before and after

<table>
  <thead>
    <tr><th>Before CLI 0.6.0</th><th>With CLI 0.6.0</th></tr>
  </thead>
  <tbody>
    <tr><td>A clean result could hide an incomplete or incorrect assessment boundary.</td><td>Every inventoried path is included, excluded, partial, not applicable, or unknown.</td></tr>
    <tr><td>Current findings did not show whether the proposed change introduced them.</td><td>A trusted-baseline comparison separates inherited, introduced, changed, resolved, and unknown findings.</td></tr>
    <tr><td>Identity, scope, checks, risks, ownership, and rollback remained separate records.</td><td>One hash-bound synthesis produces agent JSON and a human decision card.</td></tr>
    <tr><td>A green score could be mistaken for permission to release.</td><td>Every readiness result keeps <code>release_authorized: false</code> and names the human decision owner.</td></tr>
  </tbody>
</table>

<a id="whats-new"></a>
## 🧰 What’s new?

<table>
  <thead>
    <tr><th>Command or capability</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td><code>safe2 evidence scope</code></td><td>Inventory the declared deployment relationship of repository or built-artifact paths.</td></tr>
    <tr><td><code>safe2 evidence attribute</code></td><td>Compare normalized findings across an explicitly trusted baseline and current revision.</td></tr>
    <tr><td><code>safe2 evidence readiness</code></td><td>Produce canonical release-readiness JSON and an escaped Markdown card.</td></tr>
    <tr><td>CLI 0.6 self-assessment declarations</td><td>Provide a real non-model CLI identity and built-wheel scope instead of reusing a generic agent demo.</td></tr>
    <tr><td>Hardened JUnit intake</td><td>Parse untrusted XML with <code>defusedxml</code> while retaining size, encoding, structure, and declared-total checks.</td></tr>
  </tbody>
</table>

Existing CLI commands and evidence contracts remain available. AI SAFE² remains
v3.1 with 161 core controls and CP.1 through CP.10. The UAS profile remains a
separate 27-requirement regulatory extension. NEXUS remains an optional v0.3
reference implementation.

<a id="quick-start"></a>
## 🚀 Quick start

### 1. Install and verify

```console
python -m pip install "ai-safe2[all]==0.6.0"
safe2 --version
```

Expected version output: `safe2, version 0.6.0`.

### 2. Start from the included contracts

```console
safe2 schema export assessment-scope-source-v1
safe2 schema export change-attribution-source-v1
safe2 schema export release-readiness-source-v1
```

Copy the included
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/data/release-readiness-source-demo.json">release-readiness source template</a>
and replace every placeholder with evidence for the exact revision under review.

### 3. Produce the decision-support artifacts

```console
safe2 evidence readiness readiness-source.json \
  --system-identity system-identity.json \
  --assessment-scope assessment-scope.json \
  --change-attribution change-attribution.json \
  --output release-readiness.json \
  --card release-readiness.md \
  --strict
```

> **Safety note:** The command validates and hashes supplied evidence. It does not
> execute hosted checks, authenticate provider claims, discover every risk, or
> authorize a release.

<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/RELEASE-READINESS.md">Read the complete release-readiness guide</a>.

<a id="understand-the-result"></a>
## 🚦 Understand the result

<table>
  <thead>
    <tr><th>Status</th><th>Meaning</th></tr>
  </thead>
  <tbody>
    <tr><td>🔴 <strong>hold</strong></td><td>A required check failed or was cancelled, the scope is unsafe or ambiguous, or a high-impact introduced finding or open risk remains.</td></tr>
    <tr><td>🟠 <strong>review</strong></td><td>Required evidence is missing, pending, unavailable, partial, unknown, or still requires a documented risk decision.</td></tr>
    <tr><td>🟢 <strong>ready_for_human_decision</strong></td><td>No supplied technical blocker or evidence gap remains. The named human may decide whether to release.</td></tr>
  </tbody>
</table>

`ready_for_human_decision` is not an automatic approval, safety guarantee,
certification, or AI SAFE² conformance claim.

<a id="security-boundaries"></a>
## 🛡️ Security and evidence boundaries

- Inputs use bounded, versioned contracts and reject duplicate or mismatched identities.
- Scope inventory does not follow symbolic links or Windows reparse points.
- Output files are new, distinct, no-overwrite paths.
- Strict mode preserves evidence before returning a failing exit status.
- Human-card text is escaped before rendering.
- JUnit XML uses a hardened parser and rejects DTD/entity input.

Important limits:

- A hash proves byte binding, not truth, execution, or authorship.
- A declared trusted baseline is not independently authenticated by the comparison command.
- Static findings do not prove runtime exploitability or control failure.
- Technical readiness does not authorize release or establish organizational conformance.

<a id="validation"></a>
## 🧪 Validation and compatibility

- Clean-wheel installation and the complete 19-schema workflow passed on Python
  3.11, 3.12, 3.13, and 3.14.
- The repository suite passed with 783 tests and 7 documented skips before the
  final release-candidate checks.
- Medium/high independent Bandit review reported no runtime findings after the
  JUnit parser hardening.
- The exact 0.6 wheel scope contained 198 included files with zero conflicts,
  unsafe links, truncation, partial paths, or unclassified paths.
- Comparison with merged CLI 0.5.0 commit `916bdc1` found 153 inherited static
  findings and zero introduced, changed, resolved, or unknown findings.
- Final hosted checks for the exact release revision are recorded in
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/329/checks">PR #329</a>.

The historical tag named for CLI 0.5.0 builds as package version 0.4.0. The 0.6
release process therefore requires verifying that the final tag builds and
reports exactly version 0.6.0 before publication.

## 🧭 What stays the same?

- AI SAFE² Framework: v3.1, 161 core controls.
- Cross-Pillar controls: CP.1 through CP.10.
- UAS: separate 27-requirement regulatory profile.
- NEXUS: optional reference implementation, versioned independently.
- Human approval, risk acceptance, and conformance decisions remain human-owned.

## ➡️ What comes next?

- CLI 0.7: continuous task evidence and operational truth across harness boundaries.
- Additional provider-neutral adapters and integrations after the core evidence layer stabilizes.

These are roadmap priorities, not capabilities claimed by this release.

---

**Use the CLI to make the release evidence inspectable, then let the accountable human decide.**

<p>
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md">Get Started</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/docs/RELEASE-READINESS.md">Readiness Guide</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues">Report an Issue</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework">Framework Home</a>
</p>
