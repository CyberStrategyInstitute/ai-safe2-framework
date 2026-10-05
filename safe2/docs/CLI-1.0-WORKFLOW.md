# AI SAFE² CLI 1.0 Operator Workflow

This is the shortest complete path from installation to reviewable evidence.
Run it only against systems and projects you are authorized to inspect.

After `safe2 init .`, create `system-identity-source.json` from observations
you can support. Use the exported schema and the repository's
[`system-identity-source-demo.json`](../data/system-identity-source-demo.json)
as a structural example. Replace every demo value; a copied example is not an
observation of your system.

```console
safe2 self-check --strict
mkdir review-project
cd review-project
safe2 init .
safe2 doctor . --assess --assets --output environment.json
safe2 schema export system-identity-source-v1 --output system-identity-source.schema.json
# Create system-identity-source.json here before continuing.
safe2 evidence system system-identity-source.json --output system-identity.json
safe2 assess . --output-dir assessment
safe2 evidence manifest system-identity.json assessment/assessment.json --subject-id reviewed-system --output evidence-manifest.json
safe2 acceptance run ./safe2-acceptance --strict
safe2 acceptance verify ./safe2-acceptance
```

Add task receipts, claim audit, AISM ingestion, Challenge Lab runs, or attributed
provider adapters when the decision requires them. Those layers answer different
questions and do not become equivalent merely because they share a manifest.

The workflow produces evidence and decision support. It does not install a
daemon, intercept agent execution, authorize deployment, establish framework
conformance, or replace the accountable human decision owner. The Codex and
OpenTelemetry adapters consume explicit exports; direct harness hooks remain
post-1.0 integration work.

Use [the command guide](../README.md), [evidence boundaries](../../docs/EVIDENCE-ASSURANCE.md),
[stranger acceptance](STRANGER-ACCEPTANCE.md), and [migration guidance](../../MIGRATION.md)
to tailor this flow without weakening its claims.
