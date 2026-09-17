# Assessment Scope

`safe2 evidence scope` creates a metadata-only inventory of the paths declared
inside or outside a deployable subject. It prevents a mixed repository from
silently treating tests, adversarial fixtures, examples, research, generated
artifacts, dependencies, and third-party code as identical production behavior.

This is the first engineering unit planned for CLI 0.6.0. Its merge does not by
itself create a CLI 0.6.0 release.

## Quick start

Create the system identity first:

```bash
safe2 evidence system safe2/data/system-identity-source-demo.json \
  --output system-identity.json \
  --strict
```

Build the scope inventory:

```bash
safe2 evidence scope safe2/data/assessment-scope-source-demo.json \
  --project-root . \
  --system-identity system-identity.json \
  --output assessment-scope.json
```

The packaged declaration is intentionally incomplete for the full AI SAFE²
repository. Unmatched paths remain `unknown` and `partial`. Add reviewed rules
for the actual deployment subject before using `--strict`.

## Classifications

| Classification | Intended meaning |
|---|---|
| `product` | Code or configuration shipped as part of the deployable subject |
| `test` | Test implementation or evaluation support outside runtime behavior |
| `adversarial_fixture` | Deliberately hostile content used to test a defense |
| `example` | Reference or instructional implementation |
| `research` | Research material not declared as deployed behavior |
| `generated` | Build, cache, report, or local evidence output |
| `dependency` | Installed or vendored dependency governed as a dependency |
| `third_party` | External implementation retained with third-party provenance |
| `configuration` | Configuration whose deployment relationship requires an explicit disposition |
| `documentation` | Human or agent documentation outside executable behavior |
| `unknown` | No reviewed rule establishes the path's deployment relationship |

## Dispositions

- `included`: inside the declared assessment boundary.
- `excluded`: inventoried but outside the declared boundary.
- `partial`: the relationship or coverage is incomplete.
- `not_applicable`: reviewed and determined not to apply to this subject.

Excluded and not-applicable are not synonyms. An excluded test may still supply
evidence about included product code. A not-applicable path requires an explicit
reviewed rule rather than absence of a match.

## Rule behavior

Rules use normalized, relative POSIX glob patterns and are evaluated in declared
order. Absolute paths, drive-qualified paths, backslashes, alternate-stream
syntax, and parent traversal are rejected.

When multiple rules match with different classification, disposition, or
component bindings, the conflict remains in the artifact. The first rule
supplies inventory fields only so the record stays deterministic. Any conflict
blocks `--strict` success.

The default must classify unmatched paths as `unknown`, with either `partial`
or `excluded` disposition. Strict mode fails when the result contains unknown,
partial, conflicting, truncated, or unsafe-link coverage, or contains no
included paths. The JSON artifact is written before the strict exit so the
reason remains inspectable.

## Security and evidence boundaries

The collector:

- reads path metadata but never file contents;
- does not follow symbolic links or Windows reparse points;
- caps the inventory at 10,000 entries;
- does not disclose the absolute project-root path;
- refuses to overwrite an existing output through the shared safe writer;
- binds the declaration to a validated system identity subject and fingerprint.

Every result states:

```json
{
  "decision_scope": "assessment_scope_inventory_only",
  "scope_verified": false,
  "content_inspected": false,
  "conformance_claim": false
}
```

Path rules remain attributed declarations. They do not prove build inclusion,
runtime loading, execution, authorization, control effectiveness, or AI SAFE²
conformance. A digest binds submitted bytes but does not authenticate the
declaration's author.

## Contracts

- `safe2.assessment-scope-source.v1`
- `safe2.assessment-scope-manifest.v1`

Retrieve them with:

```bash
safe2 schema export assessment-scope-source-v1
safe2 schema export assessment-scope-manifest-v1
```
