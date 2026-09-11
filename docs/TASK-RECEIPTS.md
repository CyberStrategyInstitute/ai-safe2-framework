# AI SAFE² task receipts
### Connect declared outcomes to evidence and resource use without inventing certainty

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![CLI](https://img.shields.io/badge/CLI-0.3.0-F6921E?style=flat-square)](../safe2/README.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md) | [NEXUS](../NEXUS/README.md) | [CLI](../safe2/README.md)

---

## What works in this increment

Executable paths must not be symbolic links, including interpreter aliases used
by some Linux installations. Select the real binary explicitly (for example,
`python -c "import pathlib,sys; print(pathlib.Path(sys.executable).resolve(strict=True))"`).
Confirm that this interpreter has the required dependencies: resolving a virtual
environment symlink can select the base interpreter instead. SAFE2 does not
silently resolve user-supplied executable paths or relax its no-link checks.

Release preparation also verified 684 tests passing with 5 skips across CLI and
scanner tests on Windows Python 3.12. The 0.3.0 source distribution and wheel
built successfully, and an installed-wheel smoke run verified receipts, seven
contracts, fresh pytest capture, and standalone verification outside checkout
imports. Hosted Linux CI still must pass before merge.

`safe2 feedback receipt` checks declared SHA-256 hashes against bounded local
artifact bytes, interprets imported structured test/tool reports, and produces JSON
or a human-readable Markdown receipt. It never
executes target code, contacts providers, or converts matching bytes into a claim
that the work is complete. This is the first implementation step, not the full
live usage/claim-verification platform.

| Observation | Result | Meaning |
|---|---|---|
| Expected and observed hashes match | supported | This artifact's observed bytes match the declaration |
| Hashes differ | contradicted | The artifact differs from the declared version |
| Missing, unsafe, unreadable, or oversized artifact | unverifiable | We cannot establish this criterion |
| Bound test report records failures/errors or nonzero exit | contradicted | The report does not support an all-passed claim |
| Bound report records nonempty run, no skips, all passed, exit 0 | supported | The report records all tests passing; execution is not authenticated |
| Wrong task/revision/environment, changed report, inconsistent counts, no tests, or skips | unverifiable | Evidence is inapplicable, invalid, or incomplete |

Missing evidence is not proof of deception. Hashes identify bytes, not truth or
authorship. An agent can supply a matching hash for incorrect work. Independent
acceptance criteria and behavioral validation are still required.

## Try it from a repository clone

```console
safe2 schema export task-receipt-input-v1
safe2 feedback receipt safe2/data/task-receipt-demo.json --artifact-root safe2/data --format markdown
safe2 feedback receipt safe2/data/task-receipt-demo.json --artifact-root safe2/data --output receipt.json
safe2 feedback receipt safe2/data/task-test-receipt-demo.json --artifact-root safe2/data --format markdown
safe2 feedback receipt safe2/data/task-tool-receipt-demo.json --artifact-root safe2/data --format markdown
```

The test-report command uses a clearly labeled synthetic test report: 18 passed, 2 failed,
exit 1. The `all-tests-passed` criterion must be contradicted, with a recommendation
to review the failures. It is a replay demo, not an actual 20-test execution.

The tool-report command compares a `succeeded` claim with a synthetic `unavailable`
search outcome and returns a contradicted criterion. In a copy of the input,
change `claimed_outcome` to `unavailable` to see supported disclosure. The report
bytes and expected digest do not change. Neither result verifies task completion.

The demo expects the UTF-8 bytes `hello` followed by LF. If a checkout converts
the file to CRLF, the correct outcome is a digest mismatch, not silent
normalization. Use the repository's LF attributes for a portable reproduction.
The output file must not exist; parent directories must already exist.

Exit 0 means a receipt was produced, including contradicted or unverifiable
criteria. It is not an authorization gate. Invalid input or output errors return
nonzero. Do not use this command's success exit as permission to install/deploy.

For your own artifact, provide a task ID, optional parent task ID, harness label,
one or more unique artifact criteria, and a usage list following the schema.
Use a trusted immutable artifact root and normalized relative paths. Never point
an untrusted input at a broad home/system root. Reads are capped at 1 MB per
artifact and 100 criteria; large artifacts require a future streaming validator.
Links/reparse paths and traversal are rejected or reported unverifiable. This is
not an operating-system sandbox against concurrent directory replacement.

## Direct local process capture

`safe2 feedback capture-process` now directly observes an explicitly requested
local process. This is different from importing a report: the collector launches
the process and measures its return code, elapsed time, and bounded output
fingerprints itself. It does not establish test coverage or task completion.

PowerShell demo using the current repository's installed development interpreter:

```powershell
$receiptPython = (Resolve-Path .venv-challenge/Scripts/python.exe).Path
safe2 feedback capture-process --execute --cwd . --task-id demo-process --revision working-tree --environment local-demo --call-id python-1 --tool python --output process-report.json -- $receiptPython -I -c "print('hello from the process demo')"
```

For another install, supply your own absolute executable path. The `.venv-challenge`
directory is a local contributor environment, not created by this command or
required for installed users. Use a new output filename for each run.

Then use the generated report with a `tool_report` receipt criterion, binding its
actual SHA-256 and matching task/revision/environment/tool/call labels. It can be
signed separately using `sign-report`. The same API can import third-party
reports, but the optional `process_observation` field is not proof of origin when
it arrives from an untrusted source. Authenticate the collector separately.

| Observation | Report outcome | Capture command exit |
|---|---|---|
| Process exits 0; output capture completes | succeeded | 0 |
| Process exits nonzero | failed | 1 |
| Timeout | failed; partial output hashes unavailable | 1 |
| Executable unavailable | unavailable | 1 |
| Other launch error | failed | 1 |
| Output limit or incomplete pipe draining | unknown; capture incomplete | 1 |

Zero exit means process-level success only: a test runner that finds no tests,
ignores failures, or prints fabricated success is not validated by this collector.
For tests, also use a report adapter with independent acceptance criteria.

### Execution and privacy boundaries

- Execution requires `--execute`, an explicit working directory, and an absolute
  executable path. Nothing is executed from an evidence document. Arguments after
  `--` are passed without shell interpolation; Windows batch files are rejected
  unless the operator explicitly chooses a shell as the executable.
- Output is reserved exclusively before launching. Existing or unwritable output
  prevents launch. A crash or later write failure may leave an empty/incomplete
  report; a capture error does not mean the command never ran. Inspect state before
  retrying commands with side effects.
- The process inherits only SYSTEMROOT/WINDIR/TEMP/TMP when present, plus fixed
  PYTHONUTF8/NO_COLOR settings. PATH, API keys, and other environment variables are
  not forwarded. Programs needing additional configuration may fail; that is
  recorded rather than silently granting them more environment access.
- Stdin is closed. Raw argv/stdout/stderr are not persisted by the collector;
  bounded output remains in memory long enough to hash. Fingerprints are not
  anonymization. A child can still write files or logs itself.
- Time and output caps bound the direct process observation. This is **not a
  sandbox**: same-user filesystem/network access and descendant processes are not
  contained. The child may read credentials from disk or leave descendants running.
  Run only authorized commands in an externally isolated environment where needed.
  Do not use this collector to execute untrusted downloaded skills on your host.
- The collector loads no signing key and does not automatically sign what it ran.
  Keep a separate signing/verification boundary and protect the collector, key,
  executable, report location, and operating-system account from the tested agent.
- Revision and environment labels are operator declarations, not measured source
  snapshots. The command fingerprint does not fingerprint every executable/script,
  dependency, configuration file, or network input. These remain reproducibility gaps.

## Capture pytest and its fresh report together

To independently recheck an existing capture, run
`safe2 feedback verify-pytest pytest-capture.json`. This reads bounded JSON only;
it does not run tests or follow report references. It recomputes embedded hashes,
checks process/test context and exit-code agreement, and recalculates the test
assessment instead of trusting the saved verdict. Exit 0 means **internally
consistent**, including consistent failing or skipped runs. Inspect
`all_tests_passed_claim.status` separately. Missing or altered evidence is not
proof of deception. Anyone able to rewrite the entire unsigned bundle can also
recompute its hashes; this is not authentication, replay protection, or trusted
execution. The current `sign-report` command does not accept these bundles.

`safe2 feedback capture-pytest` selects a new temporary JUnit location for each
invocation, runs an explicitly selected Python interpreter with pytest, and uses
the observed exit code when normalizing that newly produced report. It never
looks for an old `results.xml` in the working directory.

```powershell
$receiptPython = (Resolve-Path .venv-challenge/Scripts/python.exe).Path
safe2 feedback capture-pytest --execute --python $receiptPython --cwd . --task-id self-check --revision working-tree --environment local-demo --call-id pytest-1 --timeout 120 --output pytest-capture.json tests/test_junit_import.py
```

Installed users should supply their own absolute Python path with pytest installed.
Select 1–32 existing files/directories under the working directory; pytest node IDs
and arbitrary extra runner flags are not supported. Project pytest configuration
and installed plugins may still influence the run. This command executes test code
with your account's permissions and inherits the direct-process capture limitations.

The `pytest-capture-v1` artifact contains the process report, normalized test report
when available, canonical hashes of both, and the all-tests-passed assessment.
No separate operator-supplied exit code is accepted. Incomplete process capture,
missing/malformed/oversized XML, or unsupported XML conventions cannot yield a
passing assessment. Reported failures contradict it; skips remain unverifiable.
Exit 0 requires a nonempty all-passed report without skips and observed exit 0.
Other results return nonzero while preserving the available capture evidence.

The collector owns and removes its temporary XML directory; it does not remove
the caller's existing reports. Raw XML is discarded after normalization to avoid
retaining test logs/secrets. Output fingerprints and normalized counts therefore
do not support later independent replay of the discarded XML; retain separately
approved evidence in a trusted CI service when that assurance is required.

Fresh-path association prevents accidental stale pairing, **not malicious report
forgery** by the same-user test process or a compromised runner/plugin. Source,
dependencies, executable contents, and declared revision are not independently
snapshotted. No file-size quota constrains the child's temporary writes while it
runs; only final XML reads and captured stdout/stderr are bounded. Use external
filesystem/network/process isolation for untrusted workloads. The result remains
unsigned and is not remote attestation, framework conformance, or task acceptance.

## Usage and provenance

### Imported test-result contract

A `test_report` criterion includes `path`, `expected_sha256`, `expected_revision`,
and `expected_environment`. The receipt's task ID must also match the report.
Unlike a plain byte-identity claim, a changed test-report digest means that report
cannot answer the requested test assertion; it does not establish failed tests.

The report follows `safe2.test-result.v1`, exported using
`safe2 schema export test-result-v1`. It contains task/revision/environment IDs,
a source reference, process exit code, and total/passed/failed/errors/skipped
counts. Counts must reconcile. No test names, captured output, or instructions
are executed or copied into the receipt. Reports are bounded to 1 MB.

`safe2 feedback import-junit` now converts a conservative JUnit XML subset into
this format. It counts individual cases, checks suite totals, and rejects duplicate
case identities, conflicting outcomes, disabled metadata, and unsupported testcase
attributes/extensions. Expected failures represented as skipped remain skipped;
rerun/flaky extensions require explicit normalization, not silent promotion to pass.
Unknown fields in the normalized JSON still fail structural validation.

```console
safe2 feedback import-junit results.xml --task-id task-1 --revision revision-1 --environment ci-1 --exit-code 0 --output tests.json
```

Supply the actual runner exit code, not a default assumption. Exit 0 from the
importer means conversion succeeded, even if tests failed. XML is limited to UTF-8,
1 MB, 10,000 uniquely identified cases, and 32 nested suite levels. DTDs, entity
declarations, unsupported XML structures, and conflicting totals are rejected.
Raw test names, captured logs, and failure text are not copied to the normalized
report. A source digest binds the original XML bytes. This is not automatic proof
the XML belongs to the supplied revision/run: those labels and exit code remain
operator declarations. Retain a separately collected process record and original
   XML. For collector-owned fresh-run association, use `capture-pytest` above.

The criterion's narrow assertion is “this matching report records all tests
passing.” It is NOT “these tests independently ran successfully on this code.”
No process is launched, no source signature is verified, and revision/environment
labels are declarations. A forged matching report can pass consistency checks;
authenticated collection and operator-owned precommitted criteria remain required
before promoting it to independently verified execution.

### Tool outcomes and accurate disclosure

A `tool_report` criterion checks a specific claim (`succeeded`, `unavailable`, or
`failed`) against a `safe2.tool-result.v1` report. In addition to task, revision,
environment, and digest, it binds `expected_tool` and `expected_call_id`. A report
for a different call cannot stand in for the requested evidence.

| Claim | Matching report says | Criterion result |
|---|---|---|
| succeeded | unavailable, failed, or not_attempted | contradicted |
| unavailable | unavailable | supported disclosure, not completed work |
| failed | failed | supported disclosure, not completed work |
| succeeded | succeeded | supported report consistency, not useful-result verification |
| any supported claim | unknown | unverifiable |
| any supported claim | different task/revision/environment/tool/call or changed bytes | unverifiable |

Other concrete outcome disagreements are contradicted. Missing logs do not prove
the tool was never called. `not_attempted` is an explicit report assertion, not
inferred from absent evidence. A successful search call does not prove useful
results, inspected sources, or factual correctness. Unavailability applies to the
specific call/environment, not all future attempts or all users.

The complete 3-claim by 5-outcome matrix is covered in the replay tests. No live
tool probe or harness interception is performed. Source labels are not
authentication; forged reports remain possible. Both correct disclosure and
correct completion claims need authenticated provenance for higher assurance.

### Authenticate report origin and freshness

Optional Ed25519 detached signatures now bind exact report bytes, signer label,
key fingerprint, algorithm, and validity window under a report-specific signature
domain. Install `ai-safe2[challenge]` for the cryptographic dependency. Trust comes
from an operator-supplied public key, never a key discovered in a report or online.

With your existing unencrypted Ed25519 PKCS8 PEM private key and its independently
trusted SubjectPublicKeyInfo PEM public key:

```console
safe2 feedback sign-report report.json --private-key collector.pem --signer-id collector-1 --ttl 3600 --output report.signature.json
safe2 feedback verify-report report.json report.signature.json --trusted-public-key collector.pub.pem
safe2 feedback receipt input.json --artifact-root evidence --trusted-public-key collector.pub.pem --require-authentication --format markdown
```

Add `attestation_path` to each test/tool criterion, relative to `--artifact-root`.
Ensure report and signature are under that root. These are illustrative filenames;
the commands do not generate keys or collect a run. Signature outputs must not
already exist. Keep private keys out of the repository and inaccessible to the
evaluated agent. Do not provide a private key to the receipt/verification process.

- TTL is 1–86,400 seconds. Future-dated or expired signatures fail; expiry is
  exclusive. Local clock checking has no skew grace period. Signed timestamps
  are signer assertions, not trusted timestamps or execution times.
- `--require-authentication` makes missing/uncheckable/untrusted signatures
  unverifiable for test/tool criteria and requires an explicit public key.
  Plain artifact criteria remain byte checks, not authenticated reports.
- Without that flag, unsigned consistency checks remain possible and labeled.
  When a supplied signature is checked with a key, failure still makes the
  criterion unverifiable instead of silently falling back to unsigned evidence.
- `verify-report` exit 0 means origin/integrity/freshness passed, not that a task,
  test, or tool succeeded. A signed failure can still contradict a success claim.
  `receipt` retains reporting-only exit semantics even with required authentication.

Signing an imported report does not witness execution. A trusted signer can sign
an inaccurate report; a signer label is not verified organization identity. Key
custody, revocation, role/scope authorization, precommitted criteria, and trusted
execution collection are still separate responsibilities. No replay cache prevents
reuse within the validity window; context checks reject mismatched task/call/
revision/environment, not repetition in the same context.

Retain report, signature, expected context, and externally trusted public key for
audit. Receipts remain unsigned. Historical verification needs additional trusted
timestamp/audit evidence; do not backdate the verifier clock to bypass expiry.

### Usage declarations

Usage entries distinguish provider-reported values, estimates, and unknowns.
Unknown is `null`, never zero. Reported/estimated entries require a source ID;
that ID is not dereferenced or authenticated by this version. No subscription
charge allocation, quota-per-task attribution, aggregation, or savings claim is
made by the receipt command. Duplicate event IDs within an input are rejected.

`safe2 feedback usage INPUT...` now correlates up to 32 task input declarations
(1 MB each). It does not read their referenced artifacts or execute commands:

```console
safe2 feedback usage parent-input.json child-input.json --output usage.json
```

Identical task inputs are deduplicated. Conflicting snapshots of one task, lineage
cycles, and a usage event claimed by multiple tasks fail rather than being summed.
Missing parents are listed; absent usage remains absent, not zero. Totals are
per task, metric, and basis. Reported values never merge with estimates. Decimal
sums are emitted as strings to avoid adding binary floating-point error during
aggregation; this does not recover precision already lost in input numbers.

Use unique incremental event IDs and exclusive ownership. Overlapping cumulative
snapshots or the same work under different IDs cannot be detected automatically.
Summed elapsed durations are not wall time across parallel agents. No family
rollup, account bill reconciliation, subscription quota attribution, savings, or
cost-per-verified-outcome figure is claimed. Output follows `usage-summary-v1`.

Inputs should contain sanitized metadata, not prompts, credentials, or raw tool
output. The receipt omits artifact paths and content; it retains task IDs and
digests, which can themselves be sensitive. Store outputs under appropriate
access controls and retention policies. Hashes are not anonymization.

Retain the input alongside the receipt. `input_sha256` identifies canonical JSON
(sorted keys and compact separators), not the input file's raw formatting. The
receipt is not signed and does not bundle its artifacts. Reproducing a historical
observation requires the preserved input and the corresponding immutable artifact
snapshot; rerunning against today's changed files is a different observation.

## Plan and release boundaries

Local validation of this increment: full `tests/` suite on Python 3.12 returned
676 passed and 5 platform-specific skips. Before the standalone verifier addition, the focused receipt/authentication/capture/import/usage suite
returned 149 passed and 1 symlink-permission skip on each of Python 3.11, 3.12,
3.13, and 3.14 on Windows. Targeted lint/type checks, repository UX, agent manifest,
and whitespace checks passed. The synthetic failing-report CLI demo produced one
contradicted criterion and no task-completion claim. These are local checks, not
new Linux CI, signed execution evidence, or a published-release claim.
The synthetic unavailable-search demo also produced one contradicted criterion
for a success claim; no live search was invoked by that demo.
Authentication regressions cover modified bytes and metadata, wrong trusted keys,
expiry boundaries, required-signature downgrade attempts, and CLI sign/verify
round trips using fresh temporary test keys. No operational collector key was
created, accessed, or committed during this validation.
Direct-process validation additionally ran harmless real Python children for
success, nonzero exit, timeout, output overflow, and minimal-environment checks.
An unsigned local CLI demo report was captured at
`.safe2/process-capture-validation-20260911.json` (ignored local artifact) and
passed `tool-result-v1` validation. It records process success, not framework
conformance, test-suite coverage, or completed task acceptance.
An earlier full-suite JUnit report was imported into
`.safe2/junit-normalized-20260911.json`: 659 total, 654 passed, 5 skipped, no failures
or errors. Its schema passed and its all-tests-passed criterion remained
unverifiable (`test_report_has_skips`), not silently promoted to all passed.
`.safe2/usage-demo-20260911.json` passed the usage summary schema after deduplicating
an identical task input. These generated artifacts remain local and ignored.
The fresh-path pytest command also ran the 20 JUnit-import regression tests and
produced `.safe2/pytest-bound-validation-20260911.json`. Its all-passed assessment
was supported and its capture schema validated. The process/report pairing was
created by the collector, without a caller-supplied exit code or existing XML.

1. **Implemented locally:** input/output contracts, artifact identity validator,
   bound test/tool-report consistency checks, explicit
   uncertainty, JSON/Markdown receipts, and adversarial input tests.
2. **Implemented locally:** expiring detached report signatures and an optional
   required-authentication policy. This authenticates origin, not execution.
3. **Implemented locally:** explicit local process capture, minimal inherited
   environment, bounded output, timing, exit codes, and output fingerprints.
   This is not an isolated execution service or test-result adapter.
4. **Implemented locally:** bounded JUnit import and per-task usage correlation
   with duplicate-ownership and lineage checks. Run/billing provenance remains declared.
5. **Implemented locally:** collector-selected fresh pytest JUnit paths, observed
   exit-code association, normalized reports, and paired artifact hashes.
   Standalone `verify-pytest` recomputes internal consistency without execution.
   Its 22 capture/verifier tests passed on Windows Python 3.11–3.14, and it
   successfully rechecked the earlier real 20-test capture. Unsigned bundles
   remain forgeable; consistent evidence is not authenticated execution.
6. **Next:** isolated trusted execution and independently snapshotted run inputs,
   operator-owned acceptance criteria bound before execution, durable provenance,
   and replayable evaluations of correct/incorrect completion claims.
   verified provider usage versus dated estimates, and cost per independently
   verified outcome.
7. **Optional Headroom adapter:** observe transformation/retrieval events while
   preserving originals separately under authorized retention. Compare identical
   task suites with optimization off/on; include overhead, retries, coverage,
   failure disclosure, and outcome quality. No adapter is shipped in this increment.
8. **Harness integrations:** supported hooks/imports first; enforceable pre-action
   gates only with explicit authorization. No universal background interception.

Headroom's [documented pipeline](https://github.com/headroomlabs-ai/headroom)
offers a prospective extension seam; its source remains an independent provider,
not a mandatory dependency or trusted grader. Pin and test its interface before
implementation. Review default telemetry, retained originals, and learned
instruction changes as separate privacy/security concerns.

This work adds no framework controls, CP.11, AISM maturity score, calibrated
honesty probability, or Challenge 001 live-backend claim. Existing friction
records remain backward-compatible; `verified_done` remains a reference-attested
legacy outcome and must not be relabeled independently verified.
