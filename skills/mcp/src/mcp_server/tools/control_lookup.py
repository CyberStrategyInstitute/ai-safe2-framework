"""
AI SAFE2 Tool: control_lookup
Search and retrieve AI SAFE2 v3.0 controls by keyword, pillar, priority,
framework mapping, ACT tier, or exact ID.

Free tier: returns up to 30 controls.
Pro tier:  returns up to 500 controls.
"""
from __future__ import annotations

from mcp_server.controls_db import get_db
from mcp_server.tiers import apply_control_limit


def control_lookup(
    query: str = "",
    control_id: str = "",
    pillar: str = "",
    priority: str = "",
    framework: str = "",
    version_added: str = "",
    act_tier: str = "",
    include_cross_pillar: bool = True,
    tier: str = "free",
) -> dict:
    """
    Look up AI SAFE2 v3.0 controls.

    Args:
        query: Keyword search across control name, description, builder problem, and tags.
        control_id: Exact control ID (e.g., 'S1.5', 'CP.10', 'P1.T1.2').
        pillar: Filter by pillar ID ('P1'...'P5' or 'CP' for cross-pillar).
        priority: Filter by priority ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW').
        framework: Filter by framework mapping (e.g., 'EU_AI_Act', 'SOC2_Type2').
        version_added: Filter by version ('v2.0', 'v2.1', 'v3.0').
        act_tier: Filter for controls required at a specific ACT tier ('ACT-1'...'ACT-4').
        include_cross_pillar: Include CP.1-CP.10 in results (default True).
        tier: Caller access tier ('free' or 'pro').

    Returns:
        dict with 'controls' list and 'meta' dict.
    """
    db = get_db()

    # Exact ID lookup — always returns single result regardless of tier
    if control_id:
        ctrl = db.get_by_id(control_id)
        if ctrl is None:
            return {
                "controls": [],
                "meta": {"query": control_id, "found": 0, "error": f"No control found with ID '{control_id}'"},
            }
        return {"controls": [ctrl], "meta": {"query": control_id, "found": 1}}

    # Search
    raw_results = db.search(
        query=query,
        pillar=pillar,
        priority=priority,
        framework=framework,
        version=version_added,
        act_tier=act_tier,
        include_cp=include_cross_pillar,
        limit=500,  # tier limit applied below
    )

    limited, meta = apply_control_limit(tier, raw_results)
    meta.update({
        "query": query,
        "filters": {
            "pillar": pillar,
            "priority": priority,
            "framework": framework,
            "version_added": version_added,
            "act_tier": act_tier,
        },
        "framework_total": db.count()["frameworks"],
    })

    return {"controls": limited, "meta": meta}
