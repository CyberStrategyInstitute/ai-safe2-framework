# NEXUS-A2A Changelog

All notable changes to the NEXUS-A2A specification and Python SDK.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] -- false-assurance hardening (2026-10-06)

Found by the four-area battery in `tests/battery/`. Assessment record:
`docs/assessments/2026-10-06-false-assurance/`.

### Security

- **Guardian inline policy no longer substring-matches raw JSON.** String leaves and
  keys are percent-decoded (up to three rounds), NFKC-normalized, lower-cased, given
  `/` separators and collapsed slashes before matching. Built-in detectors now run in
  addition to `blocked_argument_patterns`:
  - `CREDENTIAL_PATH`: `.ssh/`, `.aws/`, `.kube/config`, `.netrc`, gcloud, docker
    config, `/etc/shadow`, `/etc/sudoers`
  - `PATH_TRAVERSAL`: any `..` segment
  - `METADATA_ENDPOINT`: `169.254.0.0/16` in decimal, hex, or octal spellings;
    `fd00:ec2::254`; `100.100.100.200`; metadata hostnames
  - `SECRET_IN_ARGUMENTS`: private-key headers, cloud and VCS tokens
  - `REMOTE_CODE_PIPE`: a download piped into an interpreter

  Of 24 evasions that v0.3 allowed, 24 are now denied. Denials report every rule that
  fired.
- **Remote Guardian no longer silently downgrades.** When `guardian_url` was set and
  `httpx` was not installed, `NEXUSGuardianClient` evaluated the default *inline* policy.
  That bypassed the remote policy and never engaged FAIL_CLOSED. A missing HTTP client is now
  an unavailable Guardian, and the configured fail mode applies. Found when the behavioral
  `nexus-score` failover check ran in a clean environment.
- **HEAR reasoning must be reviewable.** ACT-3/4 reasoning shorter than 40 characters
  or 5 words is denied (`REASONING_INSUFFICIENT`). Previously, `"x"` satisfied it.
- **OPA authz (`NEXUS/opa/nexus-authz.rego`):**
  - Decisions are always defined. Previously they were undefined for any call with no
    persistence declaration.
  - The most restrictive declared persistence scope wins. A `request` label no longer
    downgrades a `PERMANENT` write.
  - Explicit deny rules now gate `allow`.
  - `deny_reason` is populated.

- **AgBOM integrity.** `verify_chain_integrity()` now recomputes each version's content hash.
  Previously it compared stored hashes only, so a component edited inside a stored version
  verified as intact. Snapshots now deep-copy components, so a live edit can no longer rewrite
  history. Hashes for components that were never quarantined are unchanged from v0.3.
- **AgBOM rug-pull hold.** Re-discovering a known MCP server with a different tool-manifest
  digest no longer registers a second trusted server. The component is marked `quarantined`,
  its prior digest is kept, and the version reason is `mcp_capability_digest_changed`. Release
  requires `approve_capability_change(bom_ref, approver)`, which is recorded in the chain.
  Same-digest rediscovery is idempotent. A first digest on an unpinned server is recorded as
  `mcp_capability_digest_pinned`.

- **`nexus-score --v03-checks` tests behavior, not imports.** Guardian must deny a hostile
  argument, allow a benign one, and reject thin HEAR reasoning. A FAIL_CLOSED Guardian must
  deny when unreachable. AgBOM must detect a stored-version edit and hold a rug pull. OPA
  policies must pass `opa check --strict` and `opa test`; file presence no longer counts.
  On `main` the old checker printed "10/10 verified, all v0.3 controls satisfied", while
  the behavioral checks fail 3 of 10. Missing evidence (no `opa` binary) is NOT ASSESSED,
  never OK. Exit codes: 0 verified, 1 failed, 2 not assessed. Output is labeled an
  implementation self-check, not a conformance claim.
- **Memory Vaccine stub honesty.** Stub mode scores any text that lacks its test keywords at
  drift 0.05, including an explicit exfiltration instruction. Decisions and Guardian exports
  now carry `drift_method` (`stub:keyword-fixture`, `embedding:all-MiniLM-L6-v2`, or
  `not_assessed:request_scope`), and constructing a stub-mode vaccine emits a warning.

- **Registry-bound ACT tiers (AIM v0.3).** An agent's ACT tier is now an identity property set by its
  owner of record in the registered AIM, as the IETF draft (section 3.1.1) already specified.
  - With `GuardianPolicy(aim_registry=...)`:
    - The registered tier governs HEAR (`ACT_TIER_FROM_REGISTRY`), so a lower claim cannot skip it.
    - A claim above the registered tier is denied (`ACT_TIER_EXCEEDS_REGISTERED`).
    - An unregistered agent is denied (`AIM_NOT_REGISTERED`).
    - A presented AIM digest that differs from the registered one is denied (`AIM_DIGEST_MISMATCH`).
  - `nexus-authz.rego` and `nexus-aism-invariants.rego` read the tier from `data.nexus.aim.agents[<did>]`
    and expose `effective_act_tier`. Previously, a `config_change` that omitted `act_tier` skipped the
    ACT-2+ out-of-band approval, and an agent with no tier passed I-4 without any kill path. Both now
    treat a missing tier as ACT-4.
  - `AIMRegistry.to_opa_data()` produces the OPA document.

### Changed (behavior)

- **Breaking for callers that omit `act_tier`:** Guardian now treats an undeclared ACT
  tier as ACT-4, so HEAR applies (`ACT_TIER_UNDECLARED`). A tier outside 1-4 is denied
  (`ACT_TIER_INVALID`). To restore v0.3 behavior, pass
  `GuardianPolicy(treat_undeclared_tier_as=None)`.
- `schemas/aim-v0.3.schema.json`: v0.2 plus required `actTier` (1-4) and optional `maxDelegationDepth`,
  using v0.2's camelCase field names. The IETF draft's example uses snake_case (`act_tier`); that naming
  conflict is recorded here, not resolved. `nexus_sdk.aim` provides `AIMRegistry`, which records every
  AIM version, and `aim_digest`. The undeclared-tier-as-ACT-4 floor still applies when no registry is configured.
- Policies migrated to Rego v1 syntax. They load on OPA 0.65.0 (compose pin) and on
  1.x. Previously they failed on 1.x, and `nexus-aism-invariants.rego` failed
  type-checking on every version. The APay migration is decision-identical on 873
  differential inputs.

### Fixed

- `docker/docker-compose.yml` mounted `./opa` and `./schemas`, which resolve under
  `docker/` and do not exist. It now mounts `../opa` and `../schemas`. The OPA
  healthcheck no longer calls `curl`, which is absent from the `-static` image, so the
  gateway's `service_healthy` dependency can clear.
- `.github/workflows/opa.yml` watched a non-existent `opa/**` path. It now checks and
  tests `NEXUS/opa` on OPA 0.65.0 and 1.4.2.

---

## [0.5.0] -- 2026-10-04

### Summary

v0.5.0 is the Sovereign Payment Gateway release. It composes the
`CP.5.APAY/0.4` payment-integrity foundation into a deterministic execution
boundary designed so that compromising an agent process is not sufficient to
obtain a payment key, widen authority, replay authorization, restore spent
capacity, or declare settlement truth.

### Added

- Durable authority, exposure, replay, idempotency, settlement, and evidence
  boundaries with atomic state transitions.
- **Key Guardian** (`KeyGuardian`): an isolated credential-use boundary with
  transaction-bound authorization and no raw-key return path.
- Independent policy, runtime-attestation, human-intent, and settlement
  authorities with fail-closed decisions.
- Governed recovery, policy-parity verification, sandbox rail readiness, and
  machine-readable deployment-readiness evidence.
- Rail-neutral payment execution adapters and deterministic conformance tests.
- A dedicated, OIDC-based NEXUS publication workflow, clean-wheel smoke test,
  and release-tag isolation from the main `ai-safe2` package.

### Changed

- Python package version is now `0.5.0`; the distribution remains
  `nexus-a2a-sdk` and the import namespace remains `nexus_sdk`.
- Package documentation and project URLs now resolve to the maintained NEXUS
  subtree and security policy.
- The `full` extra now expands to its dependencies directly so package metadata
  can be resolved before the first public release exists.
- Removed the advertised `nexus-score` console entry point because its target
  module was not shipped. The source scoring utility remains available for
  repository workflows until it is redesigned as a supported SDK command.

### Compatibility and assurance

- Existing `CP.5.APAY/0.4` schemas, policy IDs, profile IDs, and wire contracts
  are intentionally unchanged. Package v0.5.0 adds the gateway without silently
  creating a new protocol version.
- In-process and reference implementations do not satisfy production readiness.
  Operators must bind production storage, protected signing, authenticated rail
  integrations, independent trust roots, and the evidence named by
  `NEXUSPaymentExecutionPlane.readiness()`.

## [0.4.0] -- 2026-09-21

### Summary

v0.4 is the Agent-to-Payment Release. It adds a fourth enforcement plane, **CP.5.APAY
(Agentic Payments Integrity Profile)**, covering the layer no published agent-payment
protocol claims: proof that the workload holding a valid credential is still running the
software that was approved, at the moment value moves.

AP2 (FIDO, April 2026), x402 (Linux Foundation, April 2026), Visa TAP, Mastercard Agent
Pay and KYA-OS answer recognition and authorization well. All of them assume the signing
host is trustworthy; none require proof of it. An attacker who owns the agent host
inherits its identity, registrations and mandates intact, and every signature they
produce verifies correctly.

Two AISM invariants are added: **I-7 Runtime-Bound Authority** and **I-8 Aggregate
Economic Containment**.

### Added -- SDK

- **`nexus_sdk/payments/objects.py`**: protocol-independent object model
  - Seven canonical identifiers: `principal_id`, `authority_grant_id`,
    `delegation_chain_id`, `runtime_measurement_id`, `policy_id`,
    `transaction_intent_id`, `revocation_epoch`
  - `Money` in exact integer minor units; rejects float construction, excess precision,
    and cross-currency comparison
  - `AssuranceLevel` (0 none/guest → 4 runtime-bound), `SettlementFinality`,
    `ConsequenceClass`, 40+ stable `PaymentReasonCode` values
  - `AuthorityConstraints.attenuation_violations()` across 18 axes; null on a set-valued
    axis is treated as the universal set, so an unconstrained child under a constrained
    parent is a widening rather than an inheritance
- **`nexus_sdk/payments/mandate.py`**: mandate compiler and trusted rendering surface
  - Deterministic rule engine, never a model: a model compiling its own spending limit is
    the vulnerability, since the injection that steers a purchase steers the constraint
    meant to bound it
  - Open-ended spend language and implied recurrence become recorded `Ambiguity` objects;
    `issue()` refuses while any remain unresolved
  - `render()` generates from constraints alone, consequence first
- **`nexus_sdk/payments/authority.py`**: authority graph and revocation plane
  - Subtree exposure accounting: a child's spend counts against every ancestor's ceiling
  - `RevocationPlane` as a monotonic epoch rather than a delete, so revocation does not
    race caches, facilitators or child agents
  - Velocity detection for micro-drain, split transactions and merchant dispersion
  - `exposure_after_revocation()`: measures value that still moved, not API latency
- **`nexus_sdk/payments/firewall.py`**: deterministic policy decision point; no language
  model participates; reports every failing rule, not the first
- **`nexus_sdk/payments/broker.py`**: isolated signing authority
  - `NullCredentialBroker` is the bound default and **refuses every request**
  - Broker re-checks decision, canonical digest, runtime reference and revocation epoch
    before touching a key, on the assumption that the caller may be compromised
- **`nexus_sdk/payments/evidence.py`**: Payment Transaction Receipt (PTR)
  - Hash-chained ledger with tamper detection; 41 required evidence fields
  - Three disclosure tiers; withheld fields are committed by digest, not dropped
  - Completeness measured across the union of a transaction's receipts
- **`nexus_sdk/payments/gateway.py`**: orchestration and conformance metrics
  - Re-reads the revocation epoch immediately before credential release
  - Ambiguous settlement is a first-class state and commits exposure
- **`nexus_sdk/payments/opa_input.py`**: single input contract shared by the Python
  firewall and the Rego policy
- **`nexus_sdk/payments/adapters.py`**: `IdentityNormalizer` (implemented) plus AP2,
  x402, Visa TAP, Mastercard Agent Pay and KYA-OS bindings as **fail-closed contracts**

### Added -- Policy and schemas

- **`opa/nexus-apay.rego`**: out-of-process payment enforcement, default deny, with a
  separate `release_credential` gate
- **`opa/nexus-aism-invariants.rego`**: invariants I-7 and I-8; aggregate score now /8
- **`schemas/apay-authority-grant-v0.4.schema.json`**
- **`schemas/apay-ptr-v0.4.schema.json`**

### Added -- Documentation

- **`payments/README.md`**: CP.5.APAY profile, standards landscape, execution sequence,
  required metrics, MVP acceptance gates, buyer and standards positioning
- **`payments/THREAT-MODEL.md`**: adversaries, 14-entry risk register with residual risk,
  and an explicit known-limits section
- **`payments/CONTROLS.md`**: APAY-01..20 with AI SAFE² mapping, rationale, test
  references, and three conformance levels
- **`payments/CHALLENGE-LAB.md`**: twelve falsifiable experiments, including one
  (EXP-08, catalog poisoning) designed to fail in order to document a stated limit

### Added -- Tests

- **`tests/test_apay.py`**: 95 tests. Every control has at least one test proving it
  denies what it claims to deny. `TestHonesty` fails if a fail-closed default is made
  permissive.
- **`tests/test_apay_opa_contract.py`**: 7 tests. Parses the Rego, extracts every
  `input.*` path it reads, and fails if anything is not supplied by the shared builder -
  because a rule with an absent input path is undefined, and an undefined violation rule
  is a control that silently stopped existing.
- Suite total after hardening: **306 passing**

### Fixed

- **`pyproject.toml`**: `build-backend` was `setuptools.backends.legacy:build`, which does
  not exist. The package could not be installed from source at all. Corrected to
  `setuptools.build_meta`.

### Known limitations (stated, not deferred)

- No production rail binding is implemented. Every AP2/TAP/Agent Pay/KYA-OS claim in this
  release describes what a binding must verify, not tested integration.
- `opa/nexus-apay.rego` is not validated against a live OPA server in this repository's
  CI. Its input contract is test-enforced; its evaluation semantics are not.
- Semantic intent integrity is mitigated, not solved. No control proves the principal
  meant what they said.
- Catalog poisoning is not addressed. An authentic merchant selling the wrong thing at a
  permitted price passes every provenance check; only containment survives it.
- Consent decay is a human-factors problem. Legibility helps; habituation is not
  engineered away.
- `[project.scripts] nexus-score = "nexus_sdk._cli:main"` still points at a module that
  does not exist. The console script is non-functional. Not fixed in this release.

---

## [0.3.0] -- 2026-05-30

### Summary

v0.3 is the ACS Integration Release. It closes the per-call argument inspection gap
identified in the NEXUS-vs-ACS analysis, adds OpenTelemetry-native audit export,
implements dynamic Agent Bill of Materials, and publishes the first NEXUS-ACS Bridge
Specification. AI SAFE2 v3.0 score moves from 24/25 (stub mode) toward 25/25 with
full Guardian + OPA + SPIRE deployment.

### Added -- SDK

- **`nexus_sdk/guardian.py`**: Guardian Integration Profile (ACS-compatible)
  - `GuardianPolicy`: inline verdict engine with 8-rule hierarchy
  - `GuardianStepContext`: AOS JSON-RPC 2.0 compatible step context with NEXUS DID identity
  - `NEXUSAgentContext`: replaces bare string `agent.id` with DID + SPIFFE workload attestation
  - `NEXUSGuardianClient`: three failover modes (FAIL_CLOSED, FAIL_OPEN, FAIL_MANDATE_ONLY)
  - `build_tool_call_step()`, `build_memory_store_step()`: factory helpers
  - Per-call argument-level inspection: path traversal, IMDS endpoint detection, credential tool blocking
  - HEAR Doctrine enforcement: ACT-3/4 agents require reasoning chain before execution

- **`nexus_sdk/otel.py`**: OpenTelemetry-native NOR export
  - `NEXUSOutputReceipt` (NOR): cryptographic audit receipt for every agent action
  - `InMemoryNORExporter`: test utility for NOR span collection
  - `NEXUSNORSpan`: production OTel span exporter
  - `nor_to_otel_attributes()`: OCSF event class mapping (deny always maps to POLICY_VIOLATION 6002)
  - `OCSFEventClass` enum: API_ACTIVITY, POLICY_VIOLATION, DATA_ACTIVITY, AUTHENTICATION_ACTIVITY
  - `build_tool_call_nor()`, `build_memory_nor()`: factory helpers
  - SIEM-native: traces flow directly into Splunk, Elastic, Datadog via standard OTel pipeline

- **`nexus_sdk/agbom.py`**: Dynamic Agent Bill of Materials
  - `AgBOMManager`: real-time, hash-chained component inventory
  - `AgBOMComponent` (CycloneDX v1.6 compatible): 8 component types including mcp_server
  - `AgBOMVersion`: hash-chained version history with Ed25519-ready signatures
  - `discover_mcp_server()`: auto-creates AgBOM version on MCP server discovery
  - `to_cyclonedx()`, `to_spdx_summary()`, `to_dict()`: multi-format export
  - `verify_chain_integrity()`: full chain validation
  - Unsigned component detection for supply chain risk scoring

- **`nexus_sdk/bridges/__init__.py`** (updated):
  - `NEXUSACSBridge`: NEXUS-ACS Bridge Specification v0.1
    - `build_tool_call_request()`: wraps CAEL tool calls in AOS `steps/toolCallRequest` format
    - `build_memory_store_request()`: `steps/memoryStore` with NEXUS memory provenance extension
    - `build_message_request()`: `steps/message` for input/output interception
    - `parse_verdict()`: parses AOS Guardian response into `GuardianVerdictResult`
  - `ProtocolBridgeFactory`: updated to include "acs" protocol; auto-detects from guardian_url

- **`nexus_sdk/memory.py`** (updated):
  - `MemoryVaccine.to_acs_guardian_context()`: exports provenance metadata for ACS Guardian steps
  - `MemoryVaccine.validate_write_with_guardian()`: validates write against external Guardian endpoint

### Added -- Specifications and Policy

- **`opa/nexus-aism-invariants.rego`**: Six AISM invariants as OPA/Rego Guardian policy templates
  - I-1 Authenticated Borders: DID + SPIFFE mandatory at every communication boundary
  - I-2 Monotonic Scope Narrowing: scope attenuation enforced at every delegation hop
  - I-3 Memory Provenance: cryptographic provenance required for non-SESSION memory
  - I-4 Physical Kill Switch: ACT-2+ agents must have registered kill switch pathway
  - I-5 Owner of Record: every agent must have HEAR-acknowledged human owner
  - I-6 Bias as Security Observable: behavioral drift treated as security event
  - `aism_score` (0.0-1.0), `aism_verdict` (allow/deny), `invariant_violations` aggregate

- **`schemas/nor-v0.3.schema.json`**: JSON Schema for NEXUS Output Receipt
- **`schemas/agbom-v0.3.schema.json`**: JSON Schema for Agent Bill of Materials (CycloneDX-compatible)
- **`schemas/guardian-v0.3.schema.json`**: JSON Schema for Guardian Integration Profile wire format

### Added -- Infrastructure

- **`docker/docker-compose.yml`**: Reference sovereign gateway deployment
  - Services: nexus-gateway, opa (policy sidecar), otel-collector, spire-server, redis
  - Wraps any upstream MCP server with NEXUS governance without code changes
  - All inter-service communication on isolated nexus-internal network
  - Guardian FAIL_CLOSED by default
- **`docker/.env.example`**: Configuration template with all environment variables documented
- **`docker/otel/collector-config.yaml`**: OTel Collector config for NOR-to-SIEM export

### Added -- Governance

- **`governance/GOVERNANCE.md`**: Multi-sovereign governance charter
  - NEXUS-TGC structure, steering committee seats, workstreams
  - Standard, constitutional, and emergency amendment processes
  - Five permanent Constitutional Constraints (CC-1 through CC-5)
  - Phase roadmap (2026-2030)
  - Steering committee nomination process (open through September 1, 2026)

- **`governance/ietf-draft-nexus-l1-l2.md`**: Pre-submission IETF Internet-Draft framing
  - Covers L1 Transport Security Profile (mTLS 1.3, SPIFFE, PQC)
  - Covers L2 Agent Identity and Delegation Protocol (AIM, VCC, ANS)
  - IANA considerations, normative references, security considerations

### Added -- Repository

- **`LICENSE`**: Apache 2.0
- **`CHANGELOG.md`**: This file
- **`CONTRIBUTING.md`**: Contribution guide with DCO requirements
- **`SECURITY.md`**: Vulnerability disclosure policy
- **`CODE_OF_CONDUCT.md`**: Contributor Covenant v2.1
- **`pyproject.toml`**: PEP 517 packaging (installable via `pip install nexus-a2a-sdk`)
- **`examples/`**: Working examples directory

### Updated -- Tests

- Total test count: 189 tests (67 v0.2 baseline + 122 v0.3 additions), all passing
- New test classes: TestGuardianCore, TestGuardianStepContext, TestGuardianNEXUSIdentity,
  TestGuardianMemoryHooks, TestGuardianFailover, TestGuardianReasoningChain,
  TestNORCore, TestNOROTelExport, TestNORInMemoryExporter, TestAgBOMCore,
  TestAgBOMHashChain, TestAgBOMMCPDiscovery, TestAgBOMFormats, TestACSBridgeCore,
  TestACSBridgeVerdictParsing, TestACSBridgeMemoryHooks, TestMemoryVaccineACSExport,
  TestIntegrationStack, TestSAFE2v03Compliance

### Fixed

- OCSF event class mapping: deny outcome now correctly maps to POLICY_VIOLATION (6002)
  regardless of action_type. Prior behavior: `tool_call` check fired before `deny` check,
  so a denied tool_call received API_ACTIVITY (6003). Security classification was wrong.

### AI SAFE2 v3.0 Score Impact

| Pillar | v0.2 | v0.3 | Delta |
|--------|------|------|-------|
| P1 Sanitize and Isolate | 5/5 | 5/5 | Guardian fills S1.3 gap |
| P2 Audit and Inventory | 5/5 | 5/5 | NOR OTel + AgBOM fills A2.3/A2.5 gap |
| P3 Fail-Safe and Recovery | 5/5 | 5/5 | Guardian inline deny fills F3.1 gap |
| P4 Engage and Monitor | 4/5 | 4/5 | Drift via AgBOM unsigned count (full score requires production embeddings) |
| P5 Evolve and Educate | 5/5 | 5/5 | |
| **Total** | **24/25** | **24/25 (stub) / 25/25 (full)** | |

Full 25/25 requires OPA + SPIRE + production sentence-transformers in deployment.

---

## [0.2.0] -- 2026-04-15

### Summary

Initial public release. Core NEXUS-A2A specification with Python SDK.

### Added

- **`nexus_sdk/cael.py`**: CAEL envelope (CAELEnvelope, CAELSender, Performative, ContextCompartment)
- **`nexus_sdk/memory.py`**: Memory Vaccine (four zones, drift detection, provenance, checkpoints)
- **`nexus_sdk/bridges/__init__.py`**: Protocol bridges (MCP, A2A, OpenAI, LangChain, CrewAI, n8n, REST)
- **`opa/nexus-authz.rego`**: L3 core authorization policy
- **`schemas/aim-v0.2.schema.json`**: Agent Identity Manifest schema
- **`compliance/scoring/nexus-score.py`**: AI SAFE2 v3.0 compliance checker
- **`README.md`**: Specification overview and quick start
- 67 passing tests

### AI SAFE2 v3.0 Score: 24/25 (stub mode)

---

*Maintained by Cyber Strategy Institute. Contributions welcome via the process in CONTRIBUTING.md.*
