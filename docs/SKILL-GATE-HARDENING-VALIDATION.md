# Skill-gate hardening validation

[Advisory](./advisories/2026-09-09-skill-gate-executable-scope.md) | [Runtime policy](./PYTHON-COMPATIBILITY.md) | [Release notes](./RELEASE-NOTES-CLI-0.2.0.md)

## Observed results — 2026-09-09

| Local Windows runtime | Full CLI/scanner suite |
|---|---|
| CPython 3.11.15 | 518 passed, 4 skipped |
| CPython 3.12.14 | 518 passed, 4 skipped |
| CPython 3.13.14 | 518 passed, 4 skipped |
| CPython 3.14.6 | 518 passed, 4 skipped |

The four skips require POSIX FIFOs or Windows symlink privileges. The configured
Linux CI matrix is 3.11–3.14 and must pass after the combined update is pushed.
Previous PR check results do not validate these unpushed changes.

Fresh isolated 3.11/3.13/3.14 environments installed all optional/development
dependencies successfully. Newer runtimes exposed a deprecated reserved-path API;
the implementation now uses `os.path.isreserved` where available, retaining the
older fallback. Full 3.11/3.13/3.14 suites were rerun after that change without
the prior path warnings; targeted 3.12 integrity/security tests also passed.

Ruff, mypy, repository UX, agent manifest, and whitespace checks passed.
The source distribution and wheel were rebuilt. A non-editable Python 3.14 wheel
installation, run outside the source root, generated and verified a starter bundle
with all 31 internal checks passing. The inert hostile fixture returned REJECT,
exit 1, with 3 findings and explicit coverage of 2/2 text files.

Local validation records: `.safe2/compat-3.11/results-final.xml`,
`.safe2/compat-3.13/results-final.xml`, `.safe2/compat-3.14/results-final.xml`.
These generated files are intentionally not committed.

## What this does not establish

- Unit tests use controlled provider responses. A subsequent
  [live SkillSpector acceptance run](./SKILLSPECTOR-LIVE-VALIDATION.md) passed on
  two static fixtures; it does not reproduce the earlier supplied external study.
- No macOS execution, Linux execution of the new changes, free-threaded interpreter
  qualification, CVE assignment, or deployment-safety certification is claimed.
- MCP/project sibling scope limitations remain documented in the advisory.
- File checks and before/after hashes are not an OS sandbox or continuous monitoring.
- Regex findings are review signals; an APPROVE verdict is not proof of safety.

Publish only after reviewing the combined diff and passing the updated CI matrix.
Use the newly rebuilt security-ready artifacts, not the earlier pre-hardening wheel.
