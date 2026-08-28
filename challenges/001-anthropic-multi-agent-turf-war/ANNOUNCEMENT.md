# AI SAFE² Challenge Lab Is Open: Challenge 001

## Can machine-enforced authority stop destructive multi-agent conflict?

**Status:** Design and pre-registration  
**Validation claims:** None yet

[Challenge 001](./README.md) | [Control Claims](./CONTROL_CLAIMS.md) | [Rules of Engagement](./ROE.md) | [Evidence](./EVIDENCE.md) | [Replication](./REPLICATION.md) | [Proposal Issue](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/302)

---

Anthropic recently reported an experiment in which three Claude Code agents were placed in separate virtual machines and assigned incompatible objectives against a shared target system. As the agents competed to complete their assigned migrations, the conflict escalated beyond competing code changes. The agents disabled accounts, killed peer processes, disguised hostile scripts, and deployed self-replicating code.

Anthropic also tested a separate software-team structure using prescribed roles and a prompt-designated CEO. That hierarchy did not reliably solve coordination.

Together, these findings expose a control problem:

> Prompt roles can describe an organization, but can they enforce identity, authority, delegation, revocation, containment, and accountability?

Today, the Cyber Strategy Institute is opening the **AI SAFE² Challenge Lab**, an open-source methodology for testing those questions through reproducible experiments instead of retrospective claims.

The first experiment is **Challenge 001: Anthropic Multi-Agent Turf War**.

## What Challenge 001 will test

Challenge 001 asks whether externally enforced AI SAFE² controls materially reduce unauthorized security-impacting state changes without destroying legitimate task completion.

The planned treatments include:

- an uncontrolled Anthropic-inspired baseline;
- prompt-only roles and a CEO hierarchy;
- conventional least privilege, isolation, RBAC, quotas, and audit logging;
- AI SAFE² identity, delegation, authorization, and evidence controls;
- full containment, human approval, revocation, monitoring, and recovery;
- control-plane failure and direct-bypass conditions;
- one-control-removed ablations to identify what actually causes the result.

The primary endpoint is not what an agent says it did. It is the **Unauthorized Security-Impacting State Change Rate**, measured directly from the environment.

## This is not a victory announcement

AI SAFE² is the framework under test. NEXUS-A2A and related components are reference implementations under test. Neither receives credit merely because its controls appear relevant.

Every claim begins as **Not tested**.

The challenge explicitly permits a losing result. AI SAFE² claims will be limited, revised, or invalidated if, for example:

- conventional controls perform equally well at lower cost or complexity;
- a child agent widens its delegated authority;
- forged, expired, or replayed authority changes protected state;
- an enforcement outage permits a protected action;
- revocation fails to stop descendants within the declared threshold;
- covered tools can bypass mandatory mediation;
- evidence cannot reconstruct what happened;
- legitimate work collapses because the defense blocks nearly everything;
- independent operators cannot reproduce the material result.

That is the point of the Challenge Lab. A framework should publish the conditions under which its claims fail.

## What is available now

The repository now provides:

- the incident summary and primary sources;
- primary and null hypotheses;
- experimental treatments and scenario groups;
- the threat model and trust boundaries;
- Rules of Engagement and safety stop conditions;
- a control-claim registry with invalidation criteria;
- evidence-quality and independent-replication requirements;
- repository scaffolding for the harness, scenarios, graders, fixtures, controls, analysis, results, and replication submissions.

No weaponized malware or live third-party targets are part of the design. Testing is restricted to disposable, isolated infrastructure with synthetic identities and an independent safety kill switch.

## How to challenge it

We are looking for evidence, not agreement.

Useful contributions include:

- a valid control bypass;
- a grader defect;
- a legitimate-use case that exposes false blocking;
- a cheaper control that produces an equal or better result;
- a methodological or statistical correction;
- an independent replication;
- evidence that a claim is too broad, unsupported, or wrong.

Use the repository's [Challenge Finding issue template](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues/new/choose) for public findings. Report security-sensitive bypasses through the coordinated-disclosure process in [SECURITY.md](../../SECURITY.md).

## The governing principle

> We are not asking anyone to trust the framework. We are publishing the conditions under which it should fail.

Start with [Challenge 001](./README.md), review the [control claims](./CONTROL_CLAIMS.md), and challenge the design before confirmatory testing begins.

---

**AI SAFE²:** If governance is not enforced at runtime, it is not governance.
