# AI SAFE² Support Policy

## Support channels

- Use [GitHub Issues](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues) for reproducible defects, documentation problems, interoperability findings, and feature requests.
- Use `security@cyberstrategyinstitute.com` for suspected vulnerabilities or sensitive security reports; do not disclose exploitable details publicly.
- Use repository Discussions, when enabled, for implementation questions that are not defects or security reports.

This open-source project does not promise service-level response or resolution times. Security reports are acknowledged under the timeline in [SECURITY.md](SECURITY.md). Other reports are prioritized by severity, reproducibility, affected users, and maintainer capacity.

## Compatibility and maintenance

- The current supported framework line is AI SAFE² v3.1.x.
- The `ai-safe2` CLI has an independent 0.x beta version. Until 1.0, minor releases may include interface changes; release notes and migration guidance will identify them.
- Machine-readable schemas carry their own versioned identifiers. Consumers should validate `schema_version` and fail visibly on unsupported versions.
- NEXUS, Gateway, profiles, and scanners retain independent component versions. Installing one does not establish framework conformance.
- Critical security fixes may be released outside any regular cadence. No fixed feature-release cadence is guaranteed.

## What maintainers need

Include the affected version, operating system, installation method, command or integration surface, minimal reproduction, expected and observed behavior, and sanitized output. Remove credentials, prompts, customer data, and other sensitive material.

Maintainers may close reports that cannot be reproduced, concern unsupported versions, duplicate an existing report, or request individual compliance certification. AI SAFE² outputs are decision-support evidence; organizational conformance and risk acceptance remain with accountable owners.
