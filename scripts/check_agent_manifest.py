"""Validate AI SAFE2 v3.1 machine-discovery metadata and invariants."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "ai-safe2.manifest.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    if not MANIFEST_PATH.exists():
        print("Agent manifest check FAILED: ai-safe2.manifest.json is missing")
        return 1
    if not (ROOT / "AGENTS.md").exists():
        print("Agent manifest check FAILED: AGENTS.md is missing")
        return 1

    manifest = load_json(MANIFEST_PATH)
    framework = manifest.get("framework", {})
    machine = manifest.get("machine_readable", {})
    profile = manifest.get("profiles", {}).get("cp5_mcp", {})
    uas_profile = manifest.get("profiles", {}).get("uas_regulatory", {})
    persistence = manifest.get("persistence", {})
    implementations = manifest.get("implementations", {})

    expected = {
        "framework.version": (framework.get("version"), "3.1.0"),
        "framework.core_control_count": (framework.get("core_control_count"), 161),
        "cp5_mcp.control_count": (profile.get("control_count"), 19),
        "cp5_mcp.specification": (profile.get("specification"), "MCP 2026-07-28"),
        "cp5_mcp.server_discover_required": (profile.get("server_discover_required"), False),
        "uas_regulatory.requirement_count": (uas_profile.get("requirement_count"), 27),
        "uas_regulatory.adds_to_core_control_count": (
            uas_profile.get("adds_to_core_control_count"),
            False,
        ),
        "uas_regulatory.adds_cross_pillar_control": (
            uas_profile.get("adds_cross_pillar_control"),
            False,
        ),
        "nexus.version": (implementations.get("nexus", {}).get("version"), "0.3"),
        "gateway.version": (implementations.get("gateway", {}).get("version"), "3.0"),
        "scanner.rule_count": (implementations.get("scanner", {}).get("rule_count"), 64),
        "scanner.mcp_profile_rule_count": (
            implementations.get("scanner", {}).get("mcp_profile_rule_count"),
            12,
        ),
    }
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            errors.append(f"{label}: expected {wanted!r}, found {actual!r}")

    required_paths = [
        framework.get("normative_entrypoint"),
        framework.get("cross_pillar_entrypoint"),
        machine.get("core_controls"),
        machine.get("mcp_profile"),
        machine.get("dashboard_mcp_profile_mirror"),
        machine.get("aism_model"),
        machine.get("aism_assessment_schema"),
        machine.get("uas_regulatory_profile"),
        profile.get("normative_document"),
        profile.get("machine_readable_data"),
        uas_profile.get("normative_document"),
        uas_profile.get("machine_readable_data"),
        implementations.get("nexus", {}).get("entrypoint"),
        implementations.get("nexus", {}).get("mcp_adapter"),
        implementations.get("gateway", {}).get("entrypoint"),
        implementations.get("scanner", {}).get("entrypoint"),
    ]
    for rel in required_paths:
        if not rel or not (ROOT / rel).exists():
            errors.append(f"manifest path missing or unresolved: {rel!r}")

    core_path = ROOT / machine["core_controls"]
    profile_path = ROOT / machine["mcp_profile"]
    dashboard_path = ROOT / machine["dashboard_mcp_profile_mirror"]
    core = load_json(core_path)
    mcp = load_json(profile_path)
    dashboard = load_json(dashboard_path)
    uas = load_json(ROOT / uas_profile["machine_readable_data"])

    if core.get("metadata", {}).get("total_controls") != 161:
        errors.append("core dataset metadata must declare exactly 161 controls")
    pillar_records = core.get("pillar_controls", [])
    cross_pillar_records = core.get("cross_pillar_controls", [])
    core_ids = [item.get("id") for item in [*pillar_records, *cross_pillar_records]]
    if len(pillar_records) != 151 or len(cross_pillar_records) != 10:
        errors.append("core dataset must contain 151 pillar and 10 Cross-Pillar controls")
    if len(core_ids) != 161 or len(set(core_ids)) != 161 or any(not item for item in core_ids):
        errors.append("core dataset must contain exactly 161 unique, non-empty control IDs")
    if {item.get("id") for item in cross_pillar_records} != {
        f"CP.{number}" for number in range(1, 11)
    }:
        errors.append("core Cross-Pillar IDs must be CP.1 through CP.10")
    if mcp.get("metadata", {}).get("framework_controls_total") != 161:
        errors.append("MCP profile must preserve the 161-control framework total")
    if mcp.get("metadata", {}).get("profile_controls") != 19:
        errors.append("MCP profile metadata must declare 19 profile controls")
    if mcp.get("metadata", {}).get("mcp_spec_version") != "2026-07-28":
        errors.append("MCP profile must bind to MCP 2026-07-28")
    if len(mcp.get("controls", [])) != 19:
        errors.append("MCP profile must contain exactly 19 controls")
    if {item.get("id") for item in mcp.get("controls", [])} != {
        f"MCP-{number}" for number in range(1, 20)
    }:
        errors.append("MCP profile IDs must be MCP-1 through MCP-19")
    if mcp != dashboard:
        errors.append("dashboard MCP profile mirror must exactly match canonical profile data")
    uas_requirements = [
        requirement
        for layer in uas.get("layers", [])
        for requirement in layer.get("requirements", [])
    ]
    if len(uas_requirements) != 27 or len(set(uas_requirements)) != 27:
        errors.append("UAS regulatory profile must contain 27 unique profile requirements")
    catalog = uas.get("requirement_catalog", [])
    catalog_ids = [item.get("id") for item in catalog]
    if len(catalog) != 27 or set(catalog_ids) != set(uas_requirements):
        errors.append("UAS requirement catalog must describe the same 27 profile requirements")
    for item in catalog:
        if not all(item.get(field) for field in ("requirement", "control_refs", "evidence_criteria")):
            errors.append(f"UAS catalog entry is incomplete: {item.get('id')!r}")
    if uas.get("profile", {}).get("core_control_count_remains") != 161:
        errors.append("UAS regulatory profile must preserve the 161-control core")
    if uas.get("profile", {}).get("cross_pillar_range_remains") != "CP.1-CP.10":
        errors.append("UAS regulatory profile must preserve CP.1 through CP.10")

    wanted_scopes = ["request", "handle_scoped", "durable", "swarm_shared"]
    if persistence.get("canonical_scopes") != wanted_scopes:
        errors.append(f"canonical persistence scopes must be {wanted_scopes!r}")
    if persistence.get("state_handle_is_identity") is not False:
        errors.append("state handles must not be represented as identity")
    if implementations.get("nexus", {}).get("required_for_framework_conformance") is not False:
        errors.append("NEXUS must not be represented as mandatory for framework conformance")
    if "not production-ready" not in implementations.get("nexus", {}).get("mcp_adapter_status", ""):
        errors.append("NEXUS MCP adapter status must explicitly remain non-production")

    agent_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for token in (
        "ai-safe2.manifest.json",
        "161-control",
        "MCP-1 through MCP-19",
        "handle_scoped",
        "server/discover",
        "not production-ready",
        "UAS regulatory profile extension",
    ):
        if token not in agent_text:
            errors.append(f"AGENTS.md missing required machine-consumption guidance: {token}")

    if errors:
        print("Agent manifest check FAILED")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Agent manifest check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
