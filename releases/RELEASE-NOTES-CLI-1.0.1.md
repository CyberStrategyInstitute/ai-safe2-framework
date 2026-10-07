# 🟠 AI SAFE² CLI 1.0.1: Green Means Green

**MCP SCORING • MCP GATES • SKILL TRUST GATE • PROJECT GATE • VERIFIED PYPI RELEASE**

<p>
  <a href="#why-this-matters">Why It Matters</a> ·
  <a href="#before-and-after">Before and After</a> ·
  <a href="#whats-new">What's New</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#security-boundaries">Security</a> ·
  <a href="#validation">Validation</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/396">Release PR</a>
</p>

<p><strong>Explore the repository:</strong>
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/README.md#the-shortest-safe-start">Start Here</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/MIGRATION.md#upgrade-to-101">Upgrade Notes</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md#command-map">Command Map</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/docs/assessments/2026-10-06-false-assurance">Assessment Evidence</a>
</p>

---

<a id="why-this-matters"></a>
## 💡 Why should I care and use this now?

A gate that says "safe" when it is not is worse than no gate. We ran an adversarial
battery against our own tooling and found exactly that.

**Can you trust a green result from this CLI?** In 1.0.0 and 0.9.0, not always.
In 1.0.1, every case we found fails closed.

- An MCP server whose tool description instructs credential theft no longer passes CI.
- Hostile skills are rejected, not approved.
- A project running `shell=True` and `eval()` on model output no longer clears Tier 2.
- 1.0.1 is the first 1.0 build on PyPI. 1.0.0 shipped on GitHub only.

<a id="before-and-after"></a>
## 🔄 Before → After

<table>
  <thead>
    <tr><th>Case</th><th>1.0.0 / 0.9.0</th><th>1.0.1</th></tr>
  </thead>
  <tbody>
    <tr><td>MCP server with a credential-theft tool description, a self-published attestation and empty OAuth metadata</td><td>87/100 "Acceptable", badge earned, passed <code>--ci-fail-below 70</code></td><td>29/100, badge withheld, <code>safe2 gate mcp</code> exits 1</td></tr>
    <tr><td>Self-attested controls (<code>.well-known/mcp-security.json</code>)</td><td>Added up to 25 points</td><td>Reported as claimed, never scored</td></tr>
    <tr><td>16 hostile skills (paraphrased overrides, Unicode tags, homoglyphs, env exfiltration, persistence, trigger hijack)</td><td>9 approved</td><td>16 rejected</td></tr>
    <tr><td>Project with <code>shell=True</code> and <code>eval()</code> on LLM output</td><td>Tier 2 pass at 90/100</td><td>Fails at 49/100; a CRITICAL finding caps the score</td></tr>
    <tr><td><code>safe2 gate mcp PATH</code> on a TypeScript server, an obfuscated server, or a vulnerable file renamed to <code>test_server.py</code></td><td>0 findings, pass</td><td>Detected, exit 1. A clean server still passes.</td></tr>
    <tr><td>Poisoned tool output through <code>wrap-stdio --block</code>; rug-pulled catalog through <code>wrap-proxy --pin-schema</code></td><td>Delivered to the client</td><td>Withheld</td></tr>
    <tr><td>Control cited in finding text</td><td>Could differ from the control in the JSON</td><td>Always the emitted v3.1 CP.5.MCP control</td></tr>
    <tr><td><code>pip install ai-safe2==1.0.x</code></td><td>Failed: 1.0.0 never reached PyPI</td><td>Works; the release workflow installs it from PyPI to confirm</td></tr>
  </tbody>
</table>

<a id="whats-new"></a>
## 🧰 What's new?

<table>
  <thead>
    <tr><th>Command or capability</th><th>Change</th><th>Code</th></tr>
  </thead>
  <tbody>
    <tr><td><code>safe2 score mcp</code> / <code>safe2 gate mcp URL</code></td><td>Score cannot be bought by self-attestation or unvalidated OAuth metadata. Hostile schema content caps the score, withholds the badge and fails the gate.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/aisafe2_mcp_tools/score/assessor.py">score/assessor.py</a></td></tr>
    <tr><td><code>safe2 scan mcp</code> / <code>safe2 gate mcp PATH</code></td><td>Python and TypeScript sinks previously missed, obfuscated execution, correct line attribution, no evasion by file name. Generic advisories no longer fail clean servers.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/aisafe2_mcp_tools/scan/pattern_scanner.py">scan/pattern_scanner.py</a></td></tr>
    <tr><td><code>safe2 mcp wrap-stdio</code> / <code>wrap-proxy</code></td><td>Block mode withholds poisoned content; schema pinning withholds a changed catalog; audit records name the tool and method.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/aisafe2_mcp_tools/wrap/wrapper.py">wrap/wrapper.py</a></td></tr>
    <tr><td><code>safe2 gate skill</code></td><td>New rules TG-013 to TG-024. All 16 hostile test skills are rejected.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/engines/skill_gate.py">engines/skill_gate.py</a></td></tr>
    <tr><td><code>safe2 gate</code> (project)</td><td>A CRITICAL finding caps the score.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/scanner/scanner.py">scanner/scanner.py</a></td></tr>
    <tr><td>Release pipeline</td><td>Dated <code>&lt;date&gt;_CLI_X.Y.Z</code> tags publish; the upload is verified by installing from PyPI; a weekly audit flags any release missing from PyPI.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/.github/workflows/publish.yml">publish.yml</a></td></tr>
  </tbody>
</table>

Commands and schemas are unchanged from 1.0.0. **Scores and gate results can change,
so re-run gates rather than reusing 1.0.0 or 0.9.x results.** DEP findings now cite
`MCP-4` (was `MCP-3`), matching the v3.1 control map.

<a id="quick-start"></a>
## 🚀 Quick start

```console
python -m pip install --upgrade "ai-safe2[all]==1.0.1"
safe2 --version
safe2 self-check --strict
```

```console
safe2 gate mcp ./my-mcp-server
safe2 score mcp https://my-server.example/mcp
safe2 gate skill ./my-skill --strict
```

> **Safety note:** `safe2 score mcp` sends live MCP requests to the URL you give it. Point it only at servers you are allowed to test.

<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/MIGRATION.md#upgrade-to-101">Read the upgrade notes</a>.

<a id="security-boundaries"></a>
## 🛡️ Security and evidence boundaries

- Pattern detectors are a floor. Paraphrased or novel payloads can still pass.
- A remote score is a black-box view. It cannot see server code, internal logging or egress controls.
- A passing gate is decision evidence, not a conformance claim or a release approval.
- NEXUS and the MCP knowledge server are separate packages. Their fixes are in the repository but ship in their own releases.

<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/SECURITY.md#supported-versions">Supported versions and reporting</a>.

<a id="validation"></a>
## 🧪 Validation and compatibility

- Four-area adversarial battery: 126 pass, 0 fail. 62 cases that failed on 1.0.0 now pass, with no regressions.
- Local CI mirror: 31/31 gates, including OPA 0.65.0 and 1.4.2, semgrep and gitleaks.
- Every regression test was run red on the pre-fix code and green after.
- The publish workflow for this tag runs the full test suite, builds, uploads and installs from PyPI before reporting success.
- All results are self-assessed by the maintainers' tooling. They are not independent validation.

<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/393">Fix PR #393</a> ·
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/395">Consistency PR #395</a> ·
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/docs/assessments/2026-10-07-version-consistency">Evidence and reproduce commands</a>

## 🧭 What stays the same?

AI SAFE² v3.1, the 161 core controls, the 19-control CP.5.MCP profile, and every `safe2` command name and output schema.

## ➡️ What comes next?

- A NEXUS release carrying the Guardian, AgBOM and OPA fixes.
- ACT tiers bound to the registered agent identity (#394).

These are roadmap items, not capabilities in this release.

---

**Upgrade, re-run your gates, and trust the green.**

<p>
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/README.md#the-shortest-safe-start">Get Started</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/safe2/README.md">Complete Guide</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues">Report an Issue</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework">Framework Home</a>
</p>
