#!/usr/bin/env python3
"""
nexus-score.py
NEXUS-A2A implementation self-check against AI SAFE2 v3.1 controls.

This is an implementation checker, not independent framework validation or a
conformance claim. Each v0.3 check exercises behavior (a hostile input must be
denied, tampering must be detected); a check whose evidence is unavailable is
reported NOT ASSESSED, never OK.

Usage:
    python nexus-score.py --aim path/to/agent.aim.json
    python nexus-score.py --check-env          # Check current environment
    python nexus-score.py --report             # Full report
    python nexus-score.py --v03-checks         # Run v0.3-specific control checks

Output: SAFE2 v3.1 pillar scores, AAF estimate, missing controls, recommendations.
Exit (--v03-checks): 0 all verified, 1 any check failed, 2 none failed but some not assessed.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import warnings
from dataclasses import dataclass


@dataclass
class ControlCheck:
    control_id: str
    name: str
    pillar: str
    required_for: str       # "NEXUS-Full" | "NEXUS-Personal" | "All"
    check_fn: str           # What we're checking
    passed: bool = False
    note: str = ""
    assessed: bool = True   # False: evidence unavailable; never counted as passed


def check_environment() -> list[ControlCheck]:
    """
    Check whether the local environment has NEXUS dependencies deployed.
    Each check maps to a SAFE2 v3.0 control.
    """
    checks = []

    # P0: Python SDK importable
    try:
        import nexus_sdk
        checks.append(ControlCheck("SDK", "NEXUS SDK installed", "P1", "All",
                                   "import nexus_sdk", passed=True))
    except ImportError:
        checks.append(ControlCheck("SDK", "NEXUS SDK installed", "P1", "All",
                                   "import nexus_sdk", passed=False,
                                   note="pip install (run from sdk/python/)"))

    # P1: Memory Vaccine
    try:
        from nexus_sdk.memory import MemoryVaccine
        MemoryVaccine("test", "test purpose", use_stub_embeddings=True)
        checks.append(ControlCheck("S1.5", "Memory Vaccine (L4)", "P1", "All",
                                   "MemoryVaccine import + instantiation", passed=True))
    except Exception as e:
        checks.append(ControlCheck("S1.5", "Memory Vaccine (L4)", "P1", "All",
                                   "MemoryVaccine", passed=False, note=str(e)))

    # P1: Production embeddings
    try:
        from sentence_transformers import SentenceTransformer
        checks.append(ControlCheck("S1.5-prod", "Production embeddings (sentence-transformers)", "P1", "All",
                                   "import sentence_transformers", passed=True))
    except ImportError:
        checks.append(ControlCheck("S1.5-prod", "Production embeddings", "P1", "All",
                                   "import sentence_transformers", passed=False,
                                   note="pip install sentence-transformers  (stub mode active)"))

    # P2: OPA reachable
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:8181/health", timeout=1)
        checks.append(ControlCheck("L3-OPA", "OPA policy engine (L3)", "P3", "All",
                                   "GET http://localhost:8181/health", passed=True))
    except Exception:
        checks.append(ControlCheck("L3-OPA", "OPA policy engine (L3)", "P3", "All",
                                   "GET http://localhost:8181/health", passed=False,
                                   note="OPA not running. Deploy: opa run --server --bundle ./opa/"))

    # P3: httpx for async bridges
    try:
        import httpx
        checks.append(ControlCheck("BRIDGES", "Async protocol bridges (httpx)", "P3", "All",
                                   "import httpx", passed=True))
    except ImportError:
        checks.append(ControlCheck("BRIDGES", "Async protocol bridges", "P3", "All",
                                   "import httpx", passed=False,
                                   note="pip install httpx  (sync test bridges still work)"))

    # P0: SPIFFE/SPIRE (check socket)
    spire_socket = os.path.exists("/tmp/spire-agent/public/api.sock")
    checks.append(ControlCheck("L1-SPIRE", "SPIFFE/SPIRE workload identity (L1/L2)", "P1", "NEXUS-Full",
                                "socket /tmp/spire-agent/public/api.sock",
                                passed=spire_socket,
                                note="" if spire_socket else "SPIRE not detected (production L1 requirement)"))

    return checks


def score_aim(aim_path: str) -> dict:
    """
    Score an AIM against AI SAFE2 v3.0 requirements.
    Returns SAFE2 pillar scores and recommendations.
    """
    try:
        with open(aim_path) as f:
            aim = json.load(f)
    except Exception as e:
        return {"error": f"Could not load AIM: {e}"}

    scores = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    issues = []
    recommendations = []

    # P1: Sanitize and Isolate
    if aim.get("pqcPublicKeys", {}).get("mlDsa65"):
        scores["P1"] += 1
    else:
        issues.append("Missing ML-DSA-65 key (FIPS 204 required)")

    if aim.get("pqcPublicKeys", {}).get("mlKem1024"):
        scores["P1"] += 1
    else:
        issues.append("Missing ML-KEM-1024 key (FIPS 203, required for NEXUS-Full)")

    if aim.get("memoryGovernance", {}).get("poisoningDetection") == "embedding-distance":
        scores["P1"] += 2
    elif aim.get("memoryGovernance"):
        scores["P1"] += 1
        issues.append("memoryGovernance present but poisoningDetection != embedding-distance")
    else:
        issues.append("No memoryGovernance section (S1.5 required)")

    if aim.get("jurisdictionProfile"):
        scores["P1"] += 1
    else:
        issues.append("No jurisdictionProfile (sovereignty zone enforcement missing)")

    # P2: Audit and Inventory
    if aim.get("ownerChain", "").startswith("did:"):
        scores["P2"] += 2
    else:
        issues.append("Missing ownerChain DID (A2.4 owner_of_record required)")

    if aim.get("capabilityDigest", "").startswith("sha256:"):
        scores["P2"] += 1
    else:
        recommendations.append("Add capabilityDigest for supply chain integrity (A2.3)")

    if aim.get("purposeDeclaration") and len(aim["purposeDeclaration"]) >= 20:
        scores["P2"] += 1
    else:
        issues.append("purposeDeclaration missing or too short (needed for CBGM baseline)")

    if aim.get("spiffeID", "").startswith("spiffe://"):
        scores["P2"] += 1
    else:
        issues.append("Invalid or missing spiffeID (A2.5 execution trace requires workload identity)")

    # P3: Fail-Safe and Recovery
    if aim.get("memoryGovernance", {}).get("rollbackEnabled"):
        scores["P3"] += 2
    else:
        recommendations.append("Enable rollbackEnabled in memoryGovernance (F3.4)")

    if aim.get("swarmProfile", {}).get("quorumRequired"):
        scores["P3"] += 1
    else:
        recommendations.append("Set quorumRequired in swarmProfile if swarm-eligible (F3.3)")

    if aim.get("jouleWorkProfile", {}).get("circuitBreakOnNegativeBalance"):
        scores["P3"] += 1
    else:
        recommendations.append("Enable circuitBreakOnNegativeBalance in jouleWorkProfile")

    if aim.get("jouleWorkProfile", {}).get("efficiencyFloor", 1.0) <= 0.90:
        scores["P3"] += 1
    else:
        recommendations.append("Set efficiencyFloor <= 0.90 in jouleWorkProfile (CP.8)")

    # P4: Engage and Monitor
    if aim.get("memoryGovernance", {}).get("driftThreshold", 1.0) <= 0.30:
        scores["P4"] += 2
    else:
        issues.append("driftThreshold > 0.30 reduces detection sensitivity (M4.4)")

    if aim.get("swarmProfile", {}).get("swarmEligible") is not None:
        scores["P4"] += 1
    else:
        recommendations.append("Declare swarmEligible explicitly (M4.6 emergence detection)")

    if aim.get("agentClass") in {"orchestrator", "swarm-member"}:
        scores["P4"] += 1

    # P5: Evolve and Educate
    if aim.get("a2asMigration") or aim.get("maturityLevel"):
        scores["P5"] += 2

    if aim.get("maturityLevel") in {"associate", "senior", "principal"}:
        scores["P5"] += 2

    if aim.get("signature"):
        scores["P5"] += 1

    # Cap each pillar at 5
    for k in scores:
        scores[k] = min(5, scores[k])

    total = sum(scores.values())

    # AAF estimation (AI SAFE2 v3.0 Section 8)
    aaf = estimate_aaf(aim)

    return {
        "aim_path": aim_path,
        "agent_did": aim.get("agentDID", "unknown"),
        "agent_class": aim.get("agentClass", "unknown"),
        "maturity_level": aim.get("maturityLevel", "unknown"),
        "pillar_scores": scores,
        "total_safe2_score": total,
        "max_possible": 25,
        "aaf_estimate": aaf,
        "issues": issues,
        "recommendations": recommendations,
        "overall_grade": "PASS" if total >= 20 and len(issues) == 0 else
                         "PARTIAL" if total >= 15 else "FAIL",
    }


def estimate_aaf(aim: dict) -> dict:
    """
    Estimate AIVSS AAF (Agentic Amplification Factor) from AIM fields.
    Full AAF requires runtime data; this is a structural estimate only.
    Reference: AI SAFE2 v3.0 Section 8
    """
    factors = {}

    # Factor 1: Execution Autonomy
    maturity_map = {"intern": 0, "member": 0.3, "associate": 0.5, "senior": 0.7, "principal": 1.0}
    factors["execution_autonomy"] = maturity_map.get(aim.get("maturityLevel", "intern"), 0)

    # Factor 4: Contextual Awareness
    scope = aim.get("memoryGovernance", {}).get("persistenceScope", "session")
    factors["contextual_awareness"] = {"session": 0, "cross-session": 0.5, "permanent": 1.0}.get(scope, 0)

    # Factor 7: Persistent State Retention
    factors["persistent_state"] = 1.0 if scope in {"cross-session", "permanent"} else 0.0

    # Factor 9: Multi-Agent
    factors["multi_agent"] = 1.0 if aim.get("agentClass") in {"orchestrator", "swarm-member"} else 0.0

    # Factor 10: Self-Modification (assume 0 if not declared)
    factors["self_modification"] = 0.0  # Conservative default

    total_aaf = sum(factors.values())
    return {
        "total_aaf": round(total_aaf, 2),
        "factors": factors,
        "note": "Structural estimate only. Runtime factors (tool surface, NLP interface, non-determinism) require deployment telemetry."
    }


def print_report(result: dict):
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"NEXUS-A2A / AI SAFE2 v3.0 Compliance Report")
    print(f"{'='*60}")
    print(f"Agent DID:     {result['agent_did']}")
    print(f"Class:         {result['agent_class']}")
    print(f"Maturity:      {result['maturity_level']}")
    print(f"\nPillar Scores:")
    for pillar, score in result['pillar_scores'].items():
        bar = '█' * score + '░' * (5 - score)
        print(f"  {pillar}: {bar} {score}/5")
    print(f"\nTotal: {result['total_safe2_score']}/25   Grade: {result['overall_grade']}")
    print(f"AAF Estimate: {result['aaf_estimate']['total_aaf']:.1f}/10")

    if result['issues']:
        print(f"\nIssues (fix before production):")
        for i in result['issues']:
            print(f"  - {i}")

    if result['recommendations']:
        print(f"\nRecommendations:")
        for r in result['recommendations']:
            print(f"  * {r}")

    if result['overall_grade'] == "PASS":
        print(f"\nPASS: AIM meets NEXUS-A2A v0.2 structural requirements.")
    else:
        print(f"\n{'PARTIAL' if result['overall_grade'] == 'PARTIAL' else 'FAIL'}: Address issues before production deployment.")
    print()


def print_env_report(checks: list):
    print(f"\n{'='*60}")
    print(f"NEXUS-A2A Environment Check")
    print(f"{'='*60}")
    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    for c in checks:
        status = "OK " if c.passed else "---"
        note = f"  ({c.note})" if c.note and not c.passed else ""
        print(f"  [{status}] {c.control_id}: {c.name}{note}")
    print(f"\n{passed}/{total} checks passed")
    if passed < total:
        print("\nNext steps: address failed checks to unlock build phases.")
    print()


def check_v03_controls() -> list[ControlCheck]:
    """
    NEXUS v0.3 specific control checks.
    Maps to the eight ACS-derived improvements and the SAFE2 v3.0 gap closures.
    """
    checks = []

    # Guardian Integration Profile (P0 -- S1.3): behavior, not import
    try:
        from nexus_sdk.guardian import GuardianPolicy, build_tool_call_step
        policy = GuardianPolicy()
        hostile = policy.evaluate(build_tool_call_step(
            "did:nexus:score", "spiffe://nexus.local/score", "read_file",
            {"path": "C:\\Users\\u\\.ssh\\id_ed25519"}, act_tier=1))
        benign = policy.evaluate(build_tool_call_step(
            "did:nexus:score", "spiffe://nexus.local/score", "read_file",
            {"path": "docs/readme.md"}, act_tier=1))
        thin_hear = policy.evaluate(build_tool_call_step(
            "did:nexus:score", "spiffe://nexus.local/score", "wire_money",
            {"amount": 1}, act_tier=4, reasoning="x"))
        ok = hostile.denied and benign.allowed and thin_hear.denied
        checks.append(ControlCheck("S1.3-GIP", "Guardian per-call verdict (hostile denied, benign allowed, HEAR)", "P1",
                                   "NEXUS-Full", "GuardianPolicy.evaluate on 3 probes", passed=ok,
                                   note="" if ok else f"hostile={hostile.decision} benign={benign.decision} thin_hear={thin_hear.decision}"))
    except Exception as e:
        checks.append(ControlCheck("S1.3-GIP", "Guardian Integration Profile", "P1",
                                   "NEXUS-Full", "guardian.py", passed=False, note=str(e)))

    # Guardian Failover Modes: an unreachable remote Guardian must deny when FAIL_CLOSED
    try:
        from nexus_sdk.guardian import NEXUSGuardianClient, build_tool_call_step
        client = NEXUSGuardianClient(guardian_url="http://127.0.0.1:9/unreachable",
                                     fail_mode=NEXUSGuardianClient.FAIL_CLOSED)
        v = client.evaluate(build_tool_call_step("did:nexus:score", "spiffe://nexus.local/score",
                                                 "search", {"q": "x"}, act_tier=1))
        default_closed = NEXUSGuardianClient().fail_mode == NEXUSGuardianClient.FAIL_CLOSED
        ok = v.denied and default_closed
        checks.append(ControlCheck("S1.3-FAILOVER", "Guardian unreachable -> deny (FAIL_CLOSED default)", "P1",
                                   "All", "NEXUSGuardianClient against an unreachable Guardian", passed=ok,
                                   note="" if ok else f"decision={v.decision} default_closed={default_closed}"))
    except Exception as e:
        checks.append(ControlCheck("S1.3-FAILOVER", "Guardian failover modes", "P1",
                                   "All", "NEXUSGuardianClient fail_mode", passed=False, note=str(e)))

    # OTel NOR Export + OCSF deny mapping fix (A2.5)
    try:
        from nexus_sdk.otel import InMemoryNORExporter, NEXUSOutputReceipt, OCSFEventClass, nor_to_otel_attributes
        exporter = InMemoryNORExporter()
        nor = NEXUSOutputReceipt(agent_did="did:nexus:test", action_type="tool_call",
                                  action_detail="read_file", outcome="deny")
        attrs = nor_to_otel_attributes(nor)
        deny_class = attrs.get("ocsf.class_uid")
        if deny_class == OCSFEventClass.POLICY_VIOLATION.value:
            checks.append(ControlCheck("A2.5-NOR", "NOR OTel export + OCSF deny -> POLICY_VIOLATION", "P2",
                                       "All", "nor_to_otel_attributes deny -> 6002", passed=True))
        else:
            checks.append(ControlCheck("A2.5-NOR", "NOR OCSF deny mapping", "P2",
                                       "All", "deny -> POLICY_VIOLATION", passed=False,
                                       note=f"Expected POLICY_VIOLATION(6002), got {deny_class}"))
    except Exception as e:
        checks.append(ControlCheck("A2.5-NOR", "NOR OTel export", "P2",
                                   "All", "otel.py", passed=False, note=str(e)))

    # AgBOM dynamic inventory (A2.3, M4.6): tampering detected, rug pull held
    try:
        from nexus_sdk.agbom import AgBOMManager
        mgr = AgBOMManager("did:nexus:test-agent")
        mgr.discover_mcp_server("test-server", "http://localhost:3000", tool_manifest_digest="a" * 64, version="1.0.0")
        mgr.discover_mcp_server("other-server", "http://localhost:3001", tool_manifest_digest="b" * 64)
        clean_ok = mgr.verify_chain_integrity()[0]
        mgr.discover_mcp_server("test-server", "http://localhost:3000", tool_manifest_digest="c" * 64)
        rug_held = [c.name for c in mgr.get_quarantined_components()] == ["test-server"]
        mgr._version_history[0].components[0].supplier = "http://evil.example"
        tamper_caught = not mgr.verify_chain_integrity()[0]
        ok = clean_ok and rug_held and tamper_caught
        checks.append(ControlCheck("A2.3-AGBOM", "AgBOM hash chain (tamper detected, rug pull held)", "P2",
                                   "All", "AgBOMManager: clean verify, digest change, stored-version edit",
                                   passed=ok,
                                   note="" if ok else f"clean={clean_ok} rug_held={rug_held} tamper_caught={tamper_caught}"))
    except Exception as e:
        checks.append(ControlCheck("A2.3-AGBOM", "Dynamic AgBOM", "P2",
                                   "All", "agbom.py", passed=False, note=str(e)))

    # ACS Bridge (CP.5 interoperability)
    try:
        from nexus_sdk.bridges import ProtocolBridgeFactory, NEXUSACSBridge
        bridge = NEXUSACSBridge()
        cael_tc = {"agent_did": "did:nexus:test", "spiffe_id": "spiffe://nexus.local/agent/test",
                   "tool_name": "read_file", "arguments": {"path": "/tmp/test"},
                   "idempotency_key": "test-key"}
        req = bridge.build_tool_call_request(cael_tool_call=cael_tc)
        assert req["jsonrpc"] == "2.0"
        assert req["method"] == "steps/toolCallRequest"
        checks.append(ControlCheck("CP5-ACS", "NEXUS-ACS Bridge v0.1 (AOS JSON-RPC 2.0)", "P1",
                                   "All", "NEXUSACSBridge.build_tool_call_request", passed=True))
    except Exception as e:
        checks.append(ControlCheck("CP5-ACS", "NEXUS-ACS Bridge", "P1",
                                   "All", "bridges:acs", passed=False, note=str(e)))

    # Memory Vaccine ACS export (I-3 provenance integration)
    try:
        from nexus_sdk.memory import MemoryVaccine, MemoryZone
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mv = MemoryVaccine("test-agent", "test purpose", use_stub_embeddings=True)
        decision = mv.validate_write(content="test memory", zone=MemoryZone.CROSS_SESSION,
                                     owner_did="did:nexus:test-agent")
        ctx = mv.to_acs_guardian_context(content="test memory", zone=MemoryZone.CROSS_SESSION,
                                          owner_did="did:nexus:test-agent", decision=decision)
        # ctx contains flattened provenance fields: source_did, zone, drift_score, embedding_hash
        assert "zone" in ctx
        assert "source_did" in ctx or "provenance" in ctx
        assert "embedding_hash" in ctx
        checks.append(ControlCheck("I3-MV-ACS", "Memory Vaccine ACS context export (I-3)", "P1",
                                   "All", "MemoryVaccine.to_acs_guardian_context", passed=True,
                                   note="export contract only; drift detection itself is not assessed here"))
    except Exception as e:
        checks.append(ControlCheck("I3-MV-ACS", "Memory Vaccine ACS export", "P1",
                                   "All", "to_acs_guardian_context", passed=False, note=str(e)))

    # AISM invariant / authz OPA policies: must type-check, not merely exist
    import os
    opa_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../opa"))
    opa_bin = os.environ.get("OPA_BIN") or shutil.which("opa")
    if not os.path.isfile(os.path.join(opa_dir, "nexus-aism-invariants.rego")):
        checks.append(ControlCheck("AISM-OPA", "AISM invariants + authz OPA policies type-check", "P3",
                                   "NEXUS-Full", opa_dir, passed=False,
                                   note="Missing: opa/nexus-aism-invariants.rego"))
    elif not opa_bin:
        checks.append(ControlCheck("AISM-OPA", "AISM invariants + authz OPA policies type-check", "P3",
                                   "NEXUS-Full", opa_dir, passed=False, assessed=False,
                                   note="NOT ASSESSED: no opa binary (set OPA_BIN); file presence is not evidence"))
    else:
        r = subprocess.run([opa_bin, "check", "--strict", opa_dir], capture_output=True, text=True)
        t = subprocess.run([opa_bin, "test", opa_dir], capture_output=True, text=True)
        ok = r.returncode == 0 and t.returncode == 0
        checks.append(ControlCheck("AISM-OPA", "AISM invariants + authz OPA policies type-check and pass tests", "P3",
                                   "NEXUS-Full", f"{opa_bin} check --strict + opa test", passed=ok,
                                   note="" if ok else (r.stderr or r.stdout or t.stdout)[:200].strip()))

    # JSON schemas present
    schema_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../schemas")
    for schema_name in ["nor-v0.3.schema.json", "agbom-v0.3.schema.json", "guardian-v0.3.schema.json"]:
        schema_path = os.path.join(schema_base, schema_name)
        exists = os.path.isfile(schema_path)
        checks.append(ControlCheck(f"SCHEMA-{schema_name.split('-')[0].upper()}",
                                   f"JSON schema: {schema_name}", "P2",
                                   "All", schema_path, passed=exists,
                                   note="Missing schema" if not exists else ""))

    return checks


def print_v03_report(checks: list[ControlCheck]) -> int:
    print(f"\n{'='*60}")
    print("NEXUS-A2A v0.3 implementation self-check (not a conformance claim)")
    print(f"{'='*60}")
    passed = sum(1 for c in checks if c.passed)
    failed = sum(1 for c in checks if c.assessed and not c.passed)
    unassessed = sum(1 for c in checks if not c.assessed)
    for c in checks:
        status = "OK " if c.passed else ("?? " if not c.assessed else "---")
        note = f"  ({c.note})" if c.note else ""
        print(f"  [{status}] {c.control_id} ({c.pillar}): {c.name}{note}")
    print(f"\n{passed} verified, {failed} failed, {unassessed} not assessed (of {len(checks)})")
    if failed:
        print(f"Address {failed} failing checks.")
    if unassessed:
        print(f"{unassessed} checks lacked evidence; they are not counted as passing.")
    print()
    return 1 if failed else (2 if unassessed else 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEXUS-A2A implementation self-check (AI SAFE2 v3.1)")
    parser.add_argument("--aim", help="Path to AIM JSON file to score")
    parser.add_argument("--check-env", action="store_true", help="Check local environment")
    parser.add_argument("--report", action="store_true", help="Run all checks")
    parser.add_argument("--v03-checks", action="store_true", help="Run v0.3 control checks")
    args = parser.parse_args()

    if args.check_env or args.report:
        checks = check_environment()
        print_env_report(checks)

    exit_code = 0
    if args.v03_checks or args.report:
        v03_checks = check_v03_controls()
        exit_code = print_v03_report(v03_checks)

    if args.aim:
        result = score_aim(args.aim)
        print_report(result)

    if not (args.aim or args.check_env or args.report or args.v03_checks):
        parser.print_help()
    sys.exit(exit_code)
