# CSI-2026-001: Skill gate executable-scope bypass

[Advisory index](./README.md) | [CLI](../../safe2/README.md) | [Security reporting](../../SECURITY.md)

## Risk and status

| Field | Assessment |
|---|---|
| Date | 2026-09-09 |
| Affected implementation | CLI 0.1.0 and the reviewed legacy standalone script; pre-hardening 0.2.0 development builds |
| Fix target | CLI 0.2.0; publication status must be checked against the merged release |
| Severity | High, qualitative maintainer assessment; no CVSS score assigned |
| Impact | An APPROVE result could omit executable payloads based on filename |
| Prerequisite | An attacker supplies a skill package and the consumer treats the static gate as sufficient authorization |
| Report source | User-supplied hardening patch and changeset; core bypass reproduced by regression inputs |
| Exploitation | Not established by this review; absence of evidence is not proof of absence |

## Reproduction and root cause

The previous engine opened only `.md`, `.txt`, `.yaml`, `.yml`, `.json`, and
`.toml`. Identical text containing a remote-download-to-shell pattern was
detected as `payload.md` and skipped as `payload.sh`. TG-005 also required
a `cat`/`type` prefix, missing credential-path references without that prefix.

Run only the scanner, never the inert sample content:

```console
python -m pytest tests/test_skill_gate_engine.py tests/test_skill_gate_security.py -q
safe2 gate skill tests/fixtures/hostile --strict
```

The fixture gate must return REJECT (exit 1). The tests also check unknown
extensions, hidden directories, binary coverage, UTF-16, missing providers,
ambiguous JSON, mutation detection, and platform-appropriate unsafe paths.

## Remediation in this release

- Inspect bounded regular-file content regardless of extension or directory name.
  No silent `.git`, `node_modules`, build, or test-directory exclusions.
- Decode UTF-8 and BOM-marked UTF-16; binary and unsupported encodings emit
  TG-COVERAGE and require review, or REJECT in strict mode. Archives are not extracted.
- Reject links/reparse paths and special files. Inventory, reads, and bytes are
  bounded. Read errors and exceeded limits block the gate.
- Add TG-007 through TG-012: dynamic execution, prompt-injection directives,
  credential paths, raw-IP endpoints, credential-shaped strings, and piped data transfer.
  These are heuristic review signals, not proof of malicious intent.
- Report inspected-text counts and byte counts. Empty packages do not receive approval.
- Retire `scripts/skill_trust_gate.py`: exit 3 without scanning or writing reports.
  There is one maintained engine, not two drifting rule sets.
- Harden the existing SkillSpector adapter's inventory and original-path checks,
  use length-framed target hashes, reject ambiguous JSON, and expose `--executable`.

## Required user action

Install the merged CLI 0.2.0 release and re-scan previously approved packages
containing scripts. Replace standalone-script automation with
`safe2 gate skill PATH --strict`; any nonzero exit blocks unattended installation.
Scan a dedicated, immutable package directory, not your entire development checkout.
Do not omit packaged files just to obtain an APPROVE result.

## Evidence limits and residual risk

See the [hardening validation record](../SKILL-GATE-HARDENING-VALIDATION.md)
for reproduced results and release-gate status.

The supplied report's SkillSpector 2.11.1 score, 11 findings, clean 64-component
comparison, and historical test counts have not been independently reproduced here.
They are not release validation claims. Contract tests mock the provider. A separate
[live acceptance run](../SKILLSPECTOR-LIVE-VALIDATION.md) verified two new static
fixtures with the real provider; it does not reproduce that earlier comparison.
See [runtime and provider setup](../PYTHON-COMPATIBILITY.md).

Regex scanning cannot establish safety, detect every obfuscation, or distinguish
all educational examples from operational instructions. Binary inspection remains
manual/external. A before/after digest detects persistent changes, not changes
reverted between observations. These filesystem checks are not a sandbox against
a hostile process concurrently replacing parent directories. Use a trusted,
immutable local workspace and an isolated, least-privileged scanner environment.

Sibling scope review found that MCP scanning targets selected Python source and
excludes test/dependency directories; project scanning uses supported extensions,
exclusions, and skips unreadable files. Neither is a complete package gate.
Those engines were inspected, not comprehensively remediated in this advisory.
Their results must remain scoped evidence, not general installation approval.

AI SAFE² remains 161 core controls and CP.1–CP.10. No scanner result establishes
framework conformance, AISM maturity, NVIDIA endorsement, or independent replication.
