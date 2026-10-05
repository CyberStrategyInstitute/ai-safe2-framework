# Installation Self-Check

Run the self-check immediately after installing a wheel or upgrading an existing
environment:

```bash
safe2 self-check
safe2 self-check --format json --output safe2-installation.json --strict
```

The check is offline and does not inspect project content. It records the CLI and
Python versions, verifies Python 3.11–3.14 qualification, confirms required
distributions and the `safe2` console entry point are present, loads every
packaged JSON Schema, validates each schema definition, and fingerprints the
contract catalog.

`pass` means those installation surfaces were readable and present. `hold` means
the runtime has not been qualified or package/entry-point metadata could not be
resolved. `fail` means the Python version is unsupported, a required dependency
is missing, or a packaged contract is absent/invalid. With `--strict`, exit codes
are 0 pass, 1 fail, and 2 hold.

This is not a supply-chain signature check, vulnerability scan, dependency-license
audit, project assessment, harness test, or framework conformance decision. Use
trusted package indexes and lockfiles, verify release provenance separately, and
run `safe2 assess` for project-level evidence.
