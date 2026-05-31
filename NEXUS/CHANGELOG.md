# NEXUS-A2A Changelog

All notable changes to the NEXUS-A2A specification and Python SDK.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
