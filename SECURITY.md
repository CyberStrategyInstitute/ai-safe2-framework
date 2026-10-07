# Security Policy

## Supported Versions

Framework, CLI and component versions are independent. The current framework is
AI SAFE² v3.1. The `ai-safe2` CLI is at **1.0.0** in this repository and in the
GitHub release `2026-10-5_CLI_1.0.0`; **PyPI currently serves 0.9.0**, so
`pip install ai-safe2` does not yet install 1.0.0. Verify the version you run
with `safe2 --version` and check release status against the published release,
not a branch. CLI 0.2.0 and later include the skill-gate hardening described in
[CSI-2026-001](docs/advisories/2026-09-09-skill-gate-executable-scope.md). See the
[advisory index](docs/advisories/README.md) for risks and remediation.

| Surface | Version | Security support |
| ------- | ------- | ---------------- |
| AI SAFE² Framework | 3.1.x | Current |
| `ai-safe2` CLI package | 1.0.x | Current (GitHub release; fixes land here) |
| `ai-safe2` CLI package on PyPI | 0.9.0 | Latest PyPI build until 1.0.x is published there; upgrade to 1.0.x for fixes |
| NEXUS reference implementation | 0.5.x | Current component |
| Gateway | 3.0.x | Current component (north-south plane) |
| Older framework, CLI and component releases | Earlier | No routine fixes |

## Reporting a Vulnerability
Since this is a Governance Framework, a "vulnerability" is defined as:
1.  **Logical Flaw:** A control that, if implemented, introduces a security risk.
2.  **Code Flaw:** A bug in the `safe2` CLI, the AI SAFE² MCP server (`skills/mcp/`), NEXUS, the Gateway, or a published JSON schema or dataset.
3.  **Missing Critical Vector:** A widely exploited attack (e.g., DeepSeek Jailbreak) not covered by the current taxonomy.

### How to Report
Please **DO NOT** open a public GitHub Issue for critical code exploits (Zero-Days).
*   **Email:** `security@cyberstrategyinstitute.com`
*   **Subject:** `[SECURITY] - AI SAFE2 Vulnerability Report`

We will acknowledge your report within 48 hours.
