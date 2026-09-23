# NEXUS-A2A Changelog

All notable changes to the NEXUS-A2A specification and Python SDK.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
