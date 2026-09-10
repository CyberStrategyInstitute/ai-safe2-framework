# NVIDIA SkillSpector live acceptance — 2026-09-09

[CLI setup](./PYTHON-COMPATIBILITY.md) | [Security advisory](./advisories/2026-09-09-skill-gate-executable-scope.md) | [Release notes](./RELEASE-NOTES-CLI-0.2.0.md)

## Result: passed for these static fixtures

Real NVIDIA SkillSpector 2.11.1 was installed in a separate Windows CPython 3.13.14
environment from the official v2.11.1 source revision:
`704bc9544260c2f41222dc0f92982521709496ab`.

| Fixture | Direct exit | Provider score | Recommendation | Issues | Adapter source exit |
|---|---|---|---|---|---|
| Clean local summarizer | 0 | 0 / LOW | SAFE | 0 | 0 |
| Inert hostile instructions | 1 | 100 / CRITICAL | DO_NOT_INSTALL | 7 | 1 |

Both paths used `scan PATH --format json --no-llm`. Target hashes remained unchanged.
Direct and adapter risk assessments matched. Full issue objects matched after
excluding only upstream per-run `finding_id` values; original evidence was not
rewritten. This checks agreement between invocations, not independent replication.

The public `safe2 evidence skillspector --executable ...` CLI also succeeded on the
hostile fixture. Its collection exit was 0 while `source_exit_code` remained 1:
successful evidence collection must not be mistaken for skill approval.
Strict evidence-manifest validation passed. AISM retained all 30 cells as null.

No model credentials were forwarded in the test environment. Provider metadata
reported `llm_requested: false` and empty `inference_usage`; stderr reported missing
semantic-analyzer keys. No fixture commands were executed. No OS firewall rule or
independent network trace was captured, so this is not proof of zero network traffic
or a complete filesystem/credential sandbox.

## Reproduce

The configured package registry did not provide `skillspector==2.11.1`. Install
the immutable official source revision, not an unpinned main branch:

```powershell
uv venv --python 3.13 .venv-skillspector
uv pip install --python .venv-skillspector/Scripts/python.exe "git+https://github.com/NVIDIA/SkillSpector.git@704bc9544260c2f41222dc0f92982521709496ab"
.venv-skillspector/Scripts/skillspector.exe --version
.venv-skillspector/Scripts/skillspector.exe scan tests/fixtures/skillspector-live/clean --format json --no-llm
.venv-skillspector/Scripts/skillspector.exe scan tests/fixtures/skillspector-live/hostile --format json --no-llm
safe2 evidence skillspector tests/fixtures/skillspector-live/hostile --no-llm --executable .venv-skillspector/Scripts/skillspector.exe --output hostile-evidence.json
safe2 aism ingest hostile-evidence.json --subject-id fixture-check --subject-name "Static fixture, not deployment" --output unscored-assessment.json
```

On Linux/macOS replace `Scripts/python.exe` and `Scripts/skillspector.exe` with
`bin/python` and `bin/skillspector`. Use a credential-free environment and preferably
enforce outbound blocking after installation. Dependency versions can change even
with a pinned provider revision; retain an inventory and rerun acceptance on updates.

## Captured evidence

Local artifacts are retained under `.safe2/skillspector-acceptance/`: raw stdout
and stderr, parsed direct outputs, attributed adapter outputs, CLI evidence,
dependency inventory, AISM assessment, hashed manifest, run record, and acceptance
assertions. The exact clean/hostile fixture contents are checked in under
`tests/fixtures/skillspector-live/`. Raw machine-specific paths remain local.

| Artifact | SHA-256 |
|---|---|
| clean-evidence.json | `805e3e31a8dab09be62072c4392009d817702d05a9098f201414c614f9260a21` |
| hostile-evidence.json | `255292997b69a0520f8a6016d38f4b7a6b65d80e87f5d218e94cd4656fc66404` |
| manifest.json | `bc9528c5993ef8d9030b4782c33c92b81c6ca007344defc9b73577282aa97a82` |

These observations do not reproduce the earlier supplied 16-issue/64-component
comparison, validate semantic mode, certify arbitrary packages, or imply NVIDIA
endorsement. The provider score is not an AISM maturity score or calibrated probability.
