# AI SAFE² CLI 1.0 Release Qualification Record

## Release candidate

- Package: `ai-safe2`
- Candidate version: `1.0.0`
- Framework interpreted: AI SAFE² v3.1.0; the framework remains 161 controls
  and CP.1 through CP.10.
- Qualification scope: packaging, clean installation, public command surfaces,
  packaged contracts/examples, offline stranger acceptance, uninstall behavior,
  compatibility documentation, and release automation.

## Capability gate

| Requirement | Evidence at PR creation | Final release condition |
|---|---|---|
| Clean wheel and source distribution | Built locally from the candidate source | Hosted build and artifact checks pass on the exact revision |
| Installed package, outside source imports | Windows CPython 3.12 clean-wheel qualification passed | Ubuntu, Windows, and macOS jobs pass on Python 3.11 and 3.14 |
| Runtime range | Existing Linux matrix covers Python 3.11–3.14 | Exact-revision matrix remains green |
| Stranger acceptance | Self-check, fixed benign/hostile replay, and verification passed locally | Same public workflow passes from each hosted wheel |
| Public surface | Version, schemas, examples, key command help, and console entry point checked | Stability policy and command checks remain green |
| Upgrade and recovery | Migration, clean-environment upgrade, rollback, and evidence-retention guidance documented | Release note links the final guidance |
| Uninstall | Active-environment distribution metadata and entry point removal passed locally | Hosted uninstall checks pass on all matrix platforms |
| Security and independent review | Pending on the candidate PR | CodeQL, dependency/secret/repository checks, PR-Agent, and Greptile pass with no unresolved release blockers |

## Security and evidence boundaries

The qualification runner executes only packaged examples and fixed inert
acceptance fixtures. It does not connect to user harnesses, cloud instances, or
agent accounts. It does not prove scanner precision, runtime enforcement,
organizational AISM maturity, AI SAFE² conformance, publisher identity, or the
absence of vulnerabilities.

The Ubuntu/Windows/macOS jobs establish repeatability for the tested wheel and
interpreter combinations. They do not certify every OS release, architecture,
WSL distribution, optional third-party provider, or future dependency version.

## Deferred from the 1.0 core

Native direct hooks for Codex, Claude Code, Hermes, OpenClaw, and other harnesses;
cloud/network inventory; additional provider adapters; refreshed sovereign
runtime examples; and new Challenge Lab protocols remain post-1.0 integration
work. Open framework and research proposals are not silently incorporated into
the stable CLI contract.

## Release decision

Merge, tag creation, PyPI publication, deployment, risk acceptance, and public
release remain human-owned decisions. Replace pending statements with links to
the exact hosted checks before announcing 1.0.0.
