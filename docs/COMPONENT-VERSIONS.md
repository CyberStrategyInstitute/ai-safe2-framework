# Component versions and publication boundaries

Framework, implementation, schema, protocol, and publication versions are
independent. This map describes the current source tree. PyPI publication
versions were verified on 2026-10-16 and are a dated observation.

| Component | Source version | Published package / availability | Authority |
| --- | --- | --- | --- |
| AI SAFE² framework | 3.1.0 | Repository normative documents | `ai-safe2.manifest.json` |
| AI SAFE² CLI | 1.1.0 | Published CLI 1.0.1 on PyPI; 1.1.0 is a source candidate | Root `pyproject.toml`, `safe2/__init__.py` |
| NEXUS SDK and Sovereign Gateway scaffold | 0.6.0 | Published SDK 0.5.0 on PyPI; 0.6.0 is a source candidate | `NEXUS/pyproject.toml`, SDK `__version__` |
| Core Gateway, north-south provider proxy | 3.0.0 | Repository reference component; no package publication asserted | `gateway/main.py` |
| MCP knowledge server | 3.1.0 | Repository package metadata; publication not asserted | `skills/mcp/pyproject.toml` |
| Developer Workflow | 0.1.0 | Contract preview; minimum CLI 1.0.1 | `developer-workflow/VERSION`, manifest |

The Developer Workflow's CLI minimum and published 1.0.1 installation pin are
intentional. They must not be rewritten to an unavailable PyPI version merely
to match the CLI source badge. Guided start requires the 1.1.0 source candidate.
Local Docker image tags and source release notes do not establish container or
package publication.

## Checks and maintenance

`scripts/check_framework_version_labels.py` checks framework labels and named
MCP controls. Its historical/component exceptions intentionally preserve old
evidence identities. It did not previously check CLI badges, pip pins, runtime
defaults, Docker labels, or publication status.

`scripts/check_component_versions.py` adds source/runtime/manifest comparisons,
current component claim checks, published installation pins, and source-build
deployment metadata. It runs in the unfiltered consistency workflow on PRs and
main pushes. Its negative tests mutate stale badges, pins, defaults, and
metadata. Historical controls and protocol identifiers remain unchanged.

The reviewed inventory is `.ai-safe2/component-versions.json`. Its publication
versions are separate from source metadata. The scheduled/manual release audit
runs `python scripts/check_component_versions.py --check-pypi`; a package-index
failure is an error, not evidence of a valid publication. After an authorized
release, verify PyPI, then update the inventory, published install commands,
status text, and this map together. Do not infer publication from a source bump.

Keep `ai-safe2-controls-v3.0.json` and its packaged mirror byte-identical. The
161-control taxonomy is intentionally unchanged. Core Gateway v3.0 is not a
stale framework label, and `CP.5.APAY/0.4`, `nexus-agbom/0.3`, schema filenames,
and NEXUS-A2A compatibility bindings retain their independent contract versions.

## Licensing scope

The root MIT code and CC BY-SA 4.0 documentation defaults apply unless a
subdirectory designates otherwise. NEXUS has its own Apache-2.0 license and
notices; Developer Workflow has its own license. This map clarifies existing
scope and does not relicense anything. Check destination-path terms when
copying or packaging files.

Repository skill source descriptions already name framework v3.1. An older
installed copy outside the repository is a separate installation and is not
updated by changing these source files.
