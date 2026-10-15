# CI execution evidence and failure attribution

CI must distinguish what the application did from what the runner, transport,
test harness, and evidence publisher did. A green test runner followed by a
broken wrapper is not a successful CI execution. An emulator that never became
healthy is not an application assertion failure.

The Developer Workflow packages this boundary as:

- `schemas/ci-execution-receipt-v1.schema.json`;
- `scripts/evaluate_ci_execution.py`;
- matching files in `repository-template/` for adopting repositories.

The evaluator is deterministic and local. It does not fetch CI logs, infer a
root cause from an error string, call an external provider, or authorize merge
or release.

## Required phase model

Model a check as explicit phases rather than one wrapper exit code:

1. `environment_preflight` — required runtime, accelerator, service, device,
   credential *presence check*, disk, port, or network boundary is available.
   Do not record secret values.
2. `build` — the candidate and any test artifact were created for the exact
   revision.
3. `test` — tests were discovered and executed; counts are internally
   consistent.
4. `postprocess` — reports, classification, cleanup needed for the result, and
   local evidence transformations completed.
5. `evidence_publication` — required artifacts and summaries were retained.

Repositories select the phases required for each capability. A missing,
`not_run`, `failed`, or `unavailable` required phase prevents `produced`.

## Failure classes

| Class | Meaning | Do not report as |
|---|---|---|
| `environment_preflight` | A required runner or environment prerequisite was absent or unusable | application failure |
| `build` | The candidate or test artifact could not be built | test failure |
| `test_transport` | The test target could not be reached, installed, started, or queried reliably | assertion failure |
| `test_harness` | Discovery, counting, orchestration, or the test framework was invalid | passing or failing product behavior |
| `application_assertion` | A test executed and an application assertion failed | infrastructure failure |
| `postprocess` | Tests may have completed, but required result processing failed | produced evidence |
| `evidence_publication` | Required artifacts or summaries were not retained | complete evidence |
| `unknown` | Available evidence cannot support a narrower class | an inferred root cause |

Classification is an attributable observation. When logs are ambiguous, use
`unknown`; do not guess from the final wrapper message.

## Source observation

An adopting repository creates an observation after its job phases complete:

```json
{
  "schema_version": "ai-safe2.ci-execution-observation.v1",
  "receipt_id": "device-tests-pr-44@abc123",
  "subject": {
    "identifier": "pr-44",
    "revision": "abc123",
    "capability": "device-privacy-tests"
  },
  "runner": {
    "provider": "github-actions",
    "image": "ubuntu-24.04",
    "operating_system": "Linux",
    "architecture": "x86_64",
    "environment_facts": {
      "hardware_acceleration": true,
      "target_api": 36
    }
  },
  "required_phases": [
    "environment_preflight",
    "build",
    "test",
    "postprocess"
  ],
  "phases": [
    {
      "name": "environment_preflight",
      "status": "passed",
      "exit_code": 0,
      "failure_class": null,
      "failure_reason": null
    },
    {
      "name": "build",
      "status": "passed",
      "exit_code": 0,
      "failure_class": null,
      "failure_reason": null
    },
    {
      "name": "test",
      "status": "passed",
      "exit_code": 0,
      "failure_class": null,
      "failure_reason": null
    },
    {
      "name": "postprocess",
      "status": "passed",
      "exit_code": 0,
      "failure_class": null,
      "failure_reason": null
    }
  ],
  "test_results": {
    "status": "passed",
    "minimum_required": 1,
    "discovered": 128,
    "executed": 128,
    "passed": 128,
    "failed": 0,
    "skipped": 0
  },
  "artifacts": [],
  "limitations": []
}
```

Generate and gate on the receipt:

```console
python scripts/evaluate_ci_execution.py \
  --input ci-execution-observation.json \
  --output ci-execution-receipt.json \
  --require-produced
```

Without `--require-produced`, the command still writes a truthful `failed` or
`unavailable` receipt and exits successfully when the observation is valid.
Use `--require-produced` when the receipt represents a required merge gate.

## Mobile and emulator preflight

For emulator or device jobs, run a small preflight before the full suite:

- verify the required accelerator is readable and writable;
- prohibit silent fallback to an unsupported execution mode;
- wait for the device and confirm boot completion;
- query the actual API level and architecture;
- install the test artifact or run one canary test;
- record boot duration and safe environment facts.

Keep multiline orchestration in a repository-owned, syntax-tested script.
Action inputs and wrapper fields may execute each line independently even when
the YAML value is syntactically valid.

## Diagnostic order

Investigate the first unsupported boundary, not the final generic exit code:

1. runner and environment preflight;
2. build and artifact identity;
3. target boot and transport health;
4. test discovery and internally consistent counts;
5. application assertions;
6. post-processing;
7. evidence retention.

Preserve the exact revision, runner image, safe environment facts, phase
results, test counts, artifacts, and limitations. A receipt proves only what
those observations support.

## Evidence-envelope mapping

The receipt is an artifact for a deterministic-check evidence envelope:

- receipt `produced` may support the mapped capability for the same revision;
- receipt `failed` maps to evidence execution `failed`;
- receipt `unavailable` maps to evidence execution `unavailable`;
- failure class and phase remain observations, not authorization or risk
  acceptance.

This helper is not a general-purpose CI evidence bridge. Repositories still
need bounded automation that collects their native results and maps the receipt
to the appropriate capability.
