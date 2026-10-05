# Stranger Acceptance

A first-time evaluator can check an installed release without cloning the source
repository, granting credentials, enabling telemetry, or executing an untrusted
skill:

```bash
python -m venv .venv
# Activate the environment, then install the released wheel from your trusted source.
safe2 self-check --strict
safe2 acceptance run ./safe2-acceptance --strict
safe2 acceptance verify ./safe2-acceptance
```

The bundle contains the installation report, one fixed benign static-control
fixture, one fixed hostile static-control fixture, their expected and observed
decisions, exact hashes, a machine report, and a human card. Verification checks
the report seal, fixture bytes, and replayed decisions. Neither fixture is
executed, and the workflow uses no network.

This makes the first evaluation easy to reproduce; it does not make the result
independent. The CLI authors selected the controls and the CLI evaluates them.
Independent assurance begins when a separate evaluator runs the released artifact
in an environment and test corpus they control, preserves the resulting bundle,
and reports both successes and failures. A passing bundle is not proof of general
security, scanner precision, runtime enforcement, or AI SAFE² conformance.

After the controls replay, run `safe2 assess` against an explicitly authorized
project and use task receipts, claim audit, Challenge Lab, and an independent
reviewer for the assurance depth appropriate to the decision.
