# AI SAFE² CLI Runtime Compatibility

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Runtime](https://img.shields.io/badge/CLI-Runtime_Compatibility-808080?style=flat-square)](./PYTHON-COMPATIBILITY.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Support policy

CLI 0.2.0 retains Python 3.11 as its minimum. Release CI covers standard CPython
3.11–3.14 on Linux: all optional dependencies, tests, package build, and installed
Challenge acceptance. Configured jobs are not passing results: check the release
commit's CI. Classifiers identify intended compatibility, not certification.

Prefer patched Python 3.13 for new environments once validation passes. Future
versions, prereleases, free-threaded builds, and alternative interpreters are not
automatically validated. The installer range `>=3.11` is not a support guarantee.
Windows/macOS require separate execution evidence; NEXUS has a separate matrix.

Track interpreter support dates, native wheels (`cryptography`, `pydantic-core`,
`ast-grep-py`, provider `yara-python`), and Click/HTTPX/AnyIO/Starlette/FastAPI/Uvicorn
changes. Test security updates; do not retain vulnerable dependencies for convenience.
See [Python lifecycle](https://devguide.python.org/versions/) and
[free-threading guidance](https://docs.python.org/3/howto/free-threading-python.html).

## Optional NVIDIA SkillSpector setup

The adapter already exists and preserves provider version, source JSON, attribution,
and `conformance_claim: false`. SkillSpector is not bundled, including in the `all`
extra. Missing installation produces an explicit error, not a successful assessment.

[NVIDIA package metadata](https://github.com/NVIDIA/SkillSpector/blob/main/pyproject.toml)
checked 2026-09-09 declares 2.11.1, Apache-2.0, and Python >=3.12,<3.15.
Use a separate provider environment to avoid dependency conflicts:

```console
uv venv --python 3.13 .venv-skillspector
```

Windows:

```powershell
uv pip install --python .venv-skillspector/Scripts/python.exe "git+https://github.com/NVIDIA/SkillSpector.git@704bc9544260c2f41222dc0f92982521709496ab"
.venv-skillspector/Scripts/skillspector.exe --version
safe2 evidence skillspector ./candidate-skill --no-llm --executable .venv-skillspector/Scripts/skillspector.exe --output skillspector-evidence.json
```

Linux/macOS:

```sh
uv pip install --python .venv-skillspector/bin/python "git+https://github.com/NVIDIA/SkillSpector.git@704bc9544260c2f41222dc0f92982521709496ab"
.venv-skillspector/bin/skillspector --version
safe2 evidence skillspector ./candidate-skill --no-llm --executable .venv-skillspector/bin/skillspector --output skillspector-evidence.json
```

The package was unavailable from the configured registry; the commands pin the
official v2.11.1 source revision. See the completed
[live acceptance run](./SKILLSPECTOR-LIVE-VALIDATION.md) and its captured results.
Choose a trusted executable outside the submitted package and verify its version.
`--no-llm` is the default. `--llm` may transmit content/incur provider costs.
A venv separates dependencies, not OS privileges or network access.

The adapter bounds inventory, reads, output and execution time, compares before/after
hashes, and accepts scan exit codes 0/1. An attributed report can describe an unsafe
skill; evidence collection is not an installation gate. Length-framed target hashes
in this hardening are not interchangeable with older target fingerprints.
Before/after hashes cannot detect changes reverted between observations.

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
