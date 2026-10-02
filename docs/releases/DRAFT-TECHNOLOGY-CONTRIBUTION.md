# 🟠 AI SAFE² v3.1 Documentation Update: Assess Technology Contributions with Clear Evidence

**Organizational maturity • Scoped technology contributions • Claim-level evidence**

**Draft announcement:** Prepared for the merged documentation update in PR #372.
This note has not been published as a GitHub release. Framework and CLI versions
are unchanged; the new review instruments remain proposed v1.0 guidance.

<p>
  <a href="#why-this-matters">Why It Matters</a> ·
  <a href="#before-and-after">Before and After</a> ·
  <a href="#whats-new">What's New</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#understand-the-result">Results</a> ·
  <a href="#security-boundaries">Boundaries</a> ·
  <a href="#validation">Validation</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/372">Merged PR #372</a>
</p>

<p><strong>Explore the repository:</strong>
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/README.md#assess-organizations-technologies-and-evidence-separately">Framework Summary</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md">Technology Profile</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/templates/TECHNOLOGY-CARD.md">Technology Card</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/research/technology-contribution-examples.md">Nine Examples</a>
</p>

---

<a id="why-this-matters"></a>
## 💡 Why should I care?

A promising product, paper, or benchmark can address a control gap without
establishing your organization's maturity. Security leaders need to see what
the technology does, where it works, and which evidence supports the claim.

**Does this candidate address our actual control gap, and what remains uncovered?**

This update adds a structured review method and reusable card to answer that
question. It separates organizational maturity, a technology's scoped contribution,
and the assurance of each claim. It also adopts the name
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/AISM/README.md">AI Sovereign Maturity (AISM) Model</a>.

<a id="before-and-after"></a>
## 🔄 Before → After

<table>
  <thead><tr><th>Before this update</th><th>With this documentation update</th></tr></thead>
  <tbody>
    <tr><td>Organizational scoring had no dedicated technology-review entry point.</td><td>A separate profile records control effects, coverage, evidence, boundaries, and residual risk.</td></tr>
    <tr><td>Product capability, test evidence, and maturity could be conflated.</td><td>The review distinguishes organizational maturity, technology contribution, and claim-level assurance.</td></tr>
    <tr><td>New research needed translation into concrete adoption decisions.</td><td>Nine source-attributed examples frame validation work, complementary controls, and ownership.</td></tr>
  </tbody>
</table>

<a id="whats-new"></a>
## 🧰 What’s new?

<table>
  <thead><tr><th>Capability</th><th>Purpose</th><th>Documentation or artifact</th></tr></thead>
  <tbody>
    <tr><td>Proposed AISM Technology Contribution Profile v1.0</td><td>Review what an artifact addresses, implements, enforces, validates, evidences, or challenges.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md">Profile and adoption rule</a></td></tr>
    <tr><td>Proposed AI SAFE² Evidence Assurance v1.0</td><td>Attribute evidence strength, origin, independence, and limitations to each claim.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/EVIDENCE-ASSURANCE.md">Assurance rubric and compatibility</a></td></tr>
    <tr><td>Reusable Technology Card</td><td>Capture version, scope, controls, mechanisms, evidence, failure behavior, retained authority, and adoption conditions.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/templates/TECHNOLOGY-CARD.md">Copy the card template</a></td></tr>
    <tr><td>Validation and incident guidance</td><td>Plan clean/attacked pairs, side-effect and bypass tests, policy-integrity checks, reconstruction, and notification ownership.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-VALIDATION.md">Validation guide</a> · <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/INCIDENT-EVIDENCE.md">Incident evidence</a></td></tr>
    <tr><td>Nine review candidates</td><td>Turn the supplied research and accountability examples into scoped acceptance work, without adopting unsupported scores.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/research/technology-contribution-examples.md">Examples and adoption backlog</a></td></tr>
    <tr><td>Repository-wide interpretation and navigation</td><td>Connect the method to pillars, AISM, implementation/tool guidance, research, Challenge Lab, and agent discovery.</td><td><a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-PROFILE-REPO-REVIEW.md">Coverage review</a></td></tr>
  </tbody>
</table>

<a id="quick-start"></a>
## 🚀 Quick start

No installation is required for this documentation workflow.

1. Identify the control gap and the artifact's exact version and deployment boundary
   using the <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md#assessment-workflow">assessment workflow</a>.
2. Copy the <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/templates/TECHNOLOGY-CARD.md">Technology Card</a>.
   Record each control effect, supporting artifact, coverage, uncertainty, and failure mode.
3. Review the <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/research/technology-contribution-examples.md#worked-bounded-card-contractwarden-design-review">bounded ContractWarden design example</a>,
   then apply the <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md#purchasing-and-adoption-rule">adoption rule</a>
   with a named decision owner and acceptance conditions.

> **Review boundary:** Completing a card does not authorize execution, deployment,
> external notification, or a conformance claim. The documented tests are proposals,
> not experiments performed by this update.

<a id="understand-the-result"></a>
## 🚦 Understand the result

<table>
  <thead><tr><th>Review instrument</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td>AISM Sovereignty Score</td><td>Organizational maturity across five pillars and six dimensions.</td></tr>
    <tr><td>Technology contribution</td><td>The capability demonstrated for named controls within the stated boundary.</td></tr>
    <tr><td>Evidence Assurance v1.0</td><td>The evidence supporting a specific attributed claim, with independence recorded separately.</td></tr>
    <tr><td>Not assessed</td><td>The review has not established a score or assurance rating; missing evidence stays visible.</td></tr>
  </tbody>
</table>

A technology contributes evidence. An organization earns its maturity level.
Do not label a product “AISM Level 4” or treat released code as independent validation.
The <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/EVIDENCE-ASSURANCE.md#existing-cli-grades-and-challenge-lab">compatibility guidance</a>
also keeps the new assurance rubric separate from existing CLI grades and Challenge Lab levels.

<a id="security-boundaries"></a>
## 🛡️ Security and evidence boundaries

This update documents how to review control mechanisms and evidence. It does not
install an enforcement system, independently validate the example technologies,
or certify an organization.

- Runtime integrations, new experiments, and TCP CLI/dashboard support remain backlog proposals.
- Existing CLI E0-E5 numeric grades cannot be relabeled as assurance-v1.0 ratings.
- An incident notification or subpoena is not proof of a breach or technical effectiveness.
- Tests must state their actual platform, tool paths, enforcement planes, bypasses, and exclusions.

Use the <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-VALIDATION.md">validation guide</a>
and <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/INCIDENT-EVIDENCE.md">incident evidence workflow</a>
to define the next review steps.

<a id="validation"></a>
## 🧪 Validation and compatibility

Hosted checks passed for PR #372's final source revision
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/commit/7cf647760590455612715ba2f7068cd2e71879ec">7cf6477</a>,
including the Python 3.11-3.14 CLI/AISM matrix, NEXUS tests, Markdown lint,
repository/manifest consistency, security gates, and CodeQL analysis.
These checks validate the repository change; they do not validate the external examples.

<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/372/checks">Inspect the hosted checks</a> ·
<a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-PROFILE-REPO-REVIEW.md#verification">Review reproducible verification instructions</a>.

## 🧭 What stays the same?

Framework and CLI versions, organizational scoring, existing CLI evidence weights,
schemas, native tool scores, and frozen Challenge 001 remain unchanged. AI SAFE²
retains 161 core controls; MCP retains 19 profile controls, and UAS retains 27
profile requirements. The documentation names the model **AI Sovereign Maturity
(AISM) Model** while preserving historical records and distinct instrument names.

## ➡️ What comes next?

Complete artifact-specific cards, assign experiment and incident-review owners,
and collect the evidence needed for adoption decisions. Future machine schemas,
CLI commands, adapters, and dashboard views require separate implementation and validation.

The <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/research/technology-contribution-examples.md#delivery-backlog-and-ownership">adoption backlog</a>
records those next steps. They are not capabilities claimed by this update.

---

**Start with one control gap and complete a Technology Card for the candidate.**

<p>
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/templates/TECHNOLOGY-CARD.md">Get the Technology Card</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md">Complete Guide</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues">Report an Issue</a> ·
  <a href="https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/70fd8864534012424810709e68b4dd46ff79823c/README.md">Framework Home</a>
</p>

<!-- Draft provenance: repository paths above are pinned to merged PR #372 at
70fd8864534012424810709e68b4dd46ff79823c. No release tag or publication date is
invented. Angle: help a security leader select a candidate using scoped control
effects and claim evidence; distinct from prior runtime-control advocacy because
this note delivers an artifact-review and adoption workflow. Remove this comment
before publication, retain the draft notice until publication is authorized, and
recheck the announced release's status, links, and evidence at that time. -->
