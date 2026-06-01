# Contributing to NEXUS-A2A

Thank you for your interest in contributing to the NEXUS-A2A protocol and SDK.
NEXUS addresses a structural security gap in agentic AI that no single organization
can close alone. Your contributions matter.

---

## What We Need

In priority order:

1. **Security reviews** of the Guardian policy logic in `opa/` and `nexus_sdk/guardian.py`
2. **Test coverage** for edge cases in CAEL envelope validation and delegation chain enforcement
3. **Bridge implementations** for additional agent frameworks (AutoGen, Semantic Kernel, Vertex AI ADK)
4. **Production embedding** integration for the Memory Vaccine (Phase 4 gap)
5. **IETF/standards body** engagement on the L1-L2 draft in `governance/ietf-draft-nexus-l1-l2.md`
6. **ACS workstream coordination** (see governance/GOVERNANCE.md for the joint contribution pathway)

---

## Ground Rules

### No Em Dashes

All contributions (code, documentation, specifications) must use colons, semicolons,
or parentheses in place of em dashes (--). This is enforced in review.

### No Primary Source Fabrication

Compliance mapping claims must cite primary sources only (NIST, ISO, IETF RFCs,
EU Official Journal). Do not cite secondary summaries.

### Full Control Text

When adding or modifying AISM invariants or SAFE2 control mappings, include the
complete normative control language. Summaries do not suffice.

### Tests Required

Every new SDK feature requires a corresponding test. Tests must not use external
network calls for the core test suite. Use stub modes where real infrastructure
(OPA, SPIRE, sentence-transformers) is required.

---

## Development Setup

```bash
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework
cd ai-safe2-framework/nexus-a2a/sdk/python
pip install -e ".[dev]"
pytest tests/ -v
```

All 189 tests must pass before submitting a PR. Run the v0.3 compliance checker:

```bash
PYTHONPATH=. python ../../compliance/scoring/nexus-score.py --v03-checks
```

All 10 v0.3 controls must show [OK].

---

## Commit Style

Use conventional commits:

```
feat(guardian): add per-call argument inspection for SSRF patterns
fix(otel): correct OCSF deny mapping to POLICY_VIOLATION (6002)
docs(governance): add Phase 2 amendment pipeline detail
test(agbom): add chain integrity violation test
```

---

## Pull Request Requirements

1. Passing tests (189+)
2. No em dashes in any changed file
3. CHANGELOG.md entry under [Unreleased]
4. For specification changes: AI SAFE2 v3.0 control mapping in PR description
5. For new OPA policies: example input/expected output in the PR body
6. For new bridges: integration test demonstrating round-trip with a real framework

---

## Developer Certificate of Origin (DCO)

All contributions require a DCO sign-off. Add to every commit:

```
Signed-off-by: Your Name <your@email.com>
```

By signing off, you certify that:
- You wrote the contribution or have the right to submit it
- The contribution is made available under the Apache 2.0 license
- You understand that contributions to the NEXUS specification may be
  incorporated into IETF or other standards submissions by CSI with attribution

---

## Security Issues

Do not report security vulnerabilities in public GitHub issues. See SECURITY.md
for the responsible disclosure process.

---

## Governance Nominations

Interested in joining the NEXUS Technical Governance Committee (NEXUS-TGC)?
See governance/GOVERNANCE.md for the nomination process (open through September 1, 2026).

---

*Questions? Open a GitHub Discussion or email community@cyberstrategyinstitute.com*
