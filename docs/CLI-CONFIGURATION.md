# AI SAFE² CLI Configuration

The CLI uses a small, versioned project configuration so agents, people, and CI
can reproduce the same declared setup. Configuration is not evidence that a
runtime followed the settings. Assessment artifacts must still record observed,
declared, missing, and conflicting evidence separately.

## Quick start

```bash
safe2 init . --profile local
safe2 config show
safe2 config validate .safe2/config.toml
```

`safe2 init` creates `.safe2/config.toml` and never replaces an existing path.
Review and commit the file when it represents shared project policy. Keep
credentials and environment-specific secrets out of it.

## Precedence

The selected source is deterministic:

1. An explicit configuration path supplied to the command.
2. The `SAFE2_CONFIG` environment variable.
3. The nearest `.safe2/config.toml`, starting at the requested project path.
4. Built-in secure defaults.

`safe2 config show` returns the selected source as `explicit`, `environment`,
`project`, or `defaults`. Environment variables do not silently override
individual policy values in this contract.

## Profiles

| Profile | Intended use | Difference from secure defaults |
|---|---|---|
| `local` | A developer or agent working in one project | 10,000-file inventory ceiling |
| `ci` | Bounded automated assessment | 50,000-file inventory ceiling |
| `enterprise` | Larger governed project assessment | 50,000-file inventory ceiling |

Profiles are starting configurations, not assurance levels, certifications, or
authorization to collect more data. Every profile defaults to:

- no prompt collection;
- no file-content collection;
- no environment-value collection;
- no network export;
- JSON as the canonical artifact format; and
- no overwrite of existing evidence.

## Security boundaries

The v1 reader accepts UTF-8 TOML no larger than 1 MiB. It rejects symbolic-link
files, non-regular files, unknown keys, absolute or parent-traversing output
paths, and malformed values. These checks reduce configuration ambiguity and
path confusion; they do not establish that the project, host, or configuration
is trustworthy.

The generated file does not enable background services, install integrations,
read project content, or transmit telemetry. Later workflows must make those
boundaries explicit before acting.

## Recovery

If initialization reports that a configuration already exists, inspect it with
`safe2 config validate` and preserve it. To replace it, move the existing file
to a reviewed backup location and run initialization again. The CLI does not
provide a force-overwrite option.
