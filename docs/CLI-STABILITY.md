# AI SAFE² CLI 1.0 Stability and Deprecation Policy

CLI 1.0 treats the following as public compatibility surfaces:

- documented `safe2` command and option names;
- documented exit-code meanings;
- schema identifiers exported by `safe2 schema list`;
- configuration precedence and canonical machine-readable JSON fields; and
- package entry point `safe2` on supported CPython versions.

Patch releases may correct security defects, validation mistakes, misleading
claims, or behavior that violates a documented boundary. They may add optional
fields, commands, schemas, or adapters. They must not silently reinterpret old
evidence as stronger evidence.

An incompatible public change requires a major version unless retaining the old
behavior would preserve a known security vulnerability. Deprecations are
documented in release notes and remain available through the next minor release
when safe to do so. The legacy `mcp-score`, `mcp-scan`, and `mcp-safe-wrap`
aliases are deprecated in 1.0; their supported replacements are under `safe2`.

Artifacts remain bound to their producing schema and CLI versions. Consumers
must preserve unknown fields, reject schema violations, and distinguish unknown,
partial, unavailable, and not-applicable evidence. A successful migration never
creates a conformance, deployment, release, or human-approval claim.

Supported release environments are defined in
[runtime compatibility](PYTHON-COMPATIBILITY.md). A configured CI job is not
proof it passed; use the checks on the exact release revision.
