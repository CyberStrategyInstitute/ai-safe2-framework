"""
AI SAFE2 Tool: map_to_frameworks
Map a compliance requirement to AI SAFE2 v3.0 controls.

Free tier: returns 5 frameworks (NIST AI RMF, ISO 42001, SOC 2, GDPR, OWASP LLM).
Pro tier:  returns all 32 frameworks.
"""
from __future__ import annotations

from mcp_server.controls_db import get_db
from mcp_server.tiers import FREE_FRAMEWORKS, apply_control_limit, apply_framework_limit

# Canonical framework metadata for display
FRAMEWORK_META = {
    "NIST_AI_RMF":     {"name": "NIST AI RMF 1.0/2.0",     "type": "ai_specific"},
    "ISO_42001":       {"name": "ISO/IEC 42001:2023",       "type": "ai_specific"},
    "OWASP_AIVSS_v0.8":{"name": "OWASP AIVSS v0.8",        "type": "ai_specific"},
    "OWASP_LLM_Top10": {"name": "OWASP Top 10 LLM",        "type": "ai_specific"},
    "OWASP_Agentic_Top10":{"name":"OWASP Agentic Top 10 (ASI)","type":"ai_specific"},
    "MITRE_ATLAS":     {"name": "MITRE ATLAS (Oct 2025)",   "type": "ai_specific"},
    "MIT_AI_Risk_v4":  {"name": "MIT AI Risk Repository v4","type": "ai_specific"},
    "Google_SAIF":     {"name": "Google SAIF",              "type": "ai_specific"},
    "CSA_Agentic_CP":  {"name": "CSA Agentic Control Plane","type": "ai_specific"},
    "CSA_Zero_Trust_LLMs":{"name":"CSA Zero Trust for LLMs","type":"ai_specific"},
    "MAESTRO":         {"name": "MAESTRO (CSA 7-Layer)",    "type": "ai_specific"},
    "Arcanum_PI":      {"name": "Arcanum PI Taxonomy",      "type": "ai_specific"},
    "AIDEFEND":        {"name": "AIDEFEND (7 Tactics)",     "type": "ai_specific"},
    "AIID":            {"name": "AIID Agentic Incidents",   "type": "ai_specific"},
    "EU_AI_Act":       {"name": "EU AI Act (2024)",         "type": "ai_specific"},
    "Intl_AI_Safety_2026":{"name":"International AI Safety Report 2026","type":"ai_specific"},
    "CSETv1":          {"name": "CSETv1 Harm",              "type": "ai_specific"},
    "HIPAA":           {"name": "HIPAA",                    "type": "enterprise"},
    "PCI_DSS_v4":      {"name": "PCI-DSS v4.0",            "type": "enterprise"},
    "SOC2_Type2":      {"name": "SOC 2 Type II",            "type": "enterprise"},
    "ISO_27001":       {"name": "ISO 27001:2022",           "type": "enterprise"},
    "NIST_CSF_2":      {"name": "NIST CSF 2.0",            "type": "enterprise"},
    "NIST_SP800_53":   {"name": "NIST SP 800-53 Rev 5",    "type": "enterprise"},
    "FedRAMP":         {"name": "FedRAMP",                  "type": "enterprise"},
    "CMMC_2":          {"name": "CMMC 2.0",                 "type": "enterprise"},
    "CIS_v8":          {"name": "CIS Controls v8",          "type": "enterprise"},
    "GDPR":            {"name": "GDPR",                     "type": "enterprise"},
    "CCPA_CPRA":       {"name": "CCPA / CPRA",              "type": "enterprise"},
    "SEC_Disclosure":  {"name": "SEC Cyber Disclosure",     "type": "enterprise"},
    "DORA":            {"name": "DORA",                     "type": "enterprise"},
    "CVE_CVSS":        {"name": "CVE / CVSS",               "type": "enterprise"},
    "Zero_Trust":      {"name": "Zero Trust",               "type": "enterprise"},
}


def map_to_frameworks(
    requirement: str,
    framework_ids: list[str] | None = None,
    tier: str = "free",
) -> dict:
    """
    Map a compliance requirement or framework to relevant AI SAFE2 v3.0 controls.

    Args:
        requirement: A compliance requirement, framework name, or keyword to map.
                     Examples: 'GDPR Article 22', 'SOC 2 CC.7.4', 'EU AI Act',
                     'prompt injection defense', 'human oversight autonomous AI'.
        framework_ids: Optional list of specific framework IDs to filter by.
                       If empty, searches across all frameworks (tier-limited).
        tier: Caller access tier.

    Returns:
        dict with 'mappings' (framework -> controls) and 'meta'.
    """
    db = get_db()
    q = requirement.lower()

    # Determine framework set based on tier
    if not framework_ids:
        all_fw_ids = set(FRAMEWORK_META.keys())
        if tier != "pro":
            available_fw_ids = FREE_FRAMEWORKS
        else:
            available_fw_ids = all_fw_ids
    else:
        if tier != "pro":
            available_fw_ids = {f for f in framework_ids if f in FREE_FRAMEWORKS}
        else:
            available_fw_ids = set(framework_ids)

    mappings: dict[str, dict] = {}

    for fw_id in sorted(available_fw_ids):
        # Find controls mapped to this framework
        matched = db.search(framework=fw_id, limit=200)

        # Apply keyword filter only when the requirement is clearly a topic keyword
        # (not a framework name or regulation reference like "GDPR Article 22")
        # This prevents over-filtering when the requirement is a citation rather than a keyword
        if q and len(q) > 3 and not any(fw_id.lower().replace("_", " ") in q for fw_id in available_fw_ids):
            keyword_filtered = [
                c for c in matched
                if q in (c.get("name","") + " " + c.get("description","") + " " +
                         c.get("builder_problem","") + " " + " ".join(c.get("tags",[]))).lower()
            ]
            # Fall back to unfiltered if keyword filter returns nothing
            matched = keyword_filtered if keyword_filtered else matched

        if matched:
            limited, _ = apply_control_limit(tier, matched)
            fw_meta = FRAMEWORK_META.get(fw_id, {"name": fw_id, "type": "unknown"})
            mappings[fw_id] = {
                "framework_name": fw_meta["name"],
                "framework_type": fw_meta["type"],
                "control_count": len(limited),
                "controls": [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "pillar": c["pillar_name"],
                        "priority": c["priority"],
                        "version": c["version_added"],
                    }
                    for c in limited
                ],
            }

    filtered_mappings, fw_meta = apply_framework_limit(tier, mappings)

    return {
        "requirement": requirement,
        "mappings": filtered_mappings,
        "meta": {
            **fw_meta,
            "total_frameworks_with_matches": len(mappings),
            "total_controls_matched": sum(len(v["controls"]) for v in mappings.values()),
        },
    }
