"""
AI SAFE2 MCP Server — Tier Enforcement
Defines what each tier can access and applies limits.

free tier  — email registration, rate-limited, limited control/framework access
pro tier   — Toolkit purchaser, full 161 controls, all 32 frameworks

Tiers are enforced per tool call. The tool functions call check_tier() to
gate access and apply limits before returning results.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp_server.config import (
    FREE_CONTROL_LIMIT,
    FREE_FRAMEWORK_LIMIT,
    FREE_RATE_LIMIT,
    PRO_RATE_LIMIT,
    VALID_TIERS,
)


@dataclass(frozen=True)
class TierPolicy:
    name: str
    control_limit: int                  # max controls returned per lookup
    framework_limit: int                # max frameworks in compliance mapping
    rate_limit_per_hour: int
    can_use_code_review: bool
    can_use_classify_agent: bool        # full ACT-3/ACT-4 classification
    can_use_get_resource: bool          # policy templates and schemas
    can_use_full_aaf: bool              # full AIVSS AAF scoring formula
    can_access_all_frameworks: bool
    description: str


TIER_POLICIES: dict[str, TierPolicy] = {
    "free": TierPolicy(
        name="Free",
        control_limit=FREE_CONTROL_LIMIT,
        framework_limit=FREE_FRAMEWORK_LIMIT,
        rate_limit_per_hour=FREE_RATE_LIMIT,
        can_use_code_review=False,
        can_use_classify_agent=False,
        can_use_get_resource=False,
        can_use_full_aaf=False,
        can_access_all_frameworks=False,
        description=(
            "Free tier: up to 30 controls per lookup, 5 frameworks in compliance "
            "mapping, basic risk scoring (no AAF). Upgrade to Pro for full access. "
            "cyberstrategyinstitute.com/ai-safe2/"
        ),
    ),
    "pro": TierPolicy(
        name="Pro (Toolkit)",
        control_limit=500,
        framework_limit=32,
        rate_limit_per_hour=PRO_RATE_LIMIT,
        can_use_code_review=True,
        can_use_classify_agent=True,
        can_use_get_resource=True,
        can_use_full_aaf=True,
        can_access_all_frameworks=True,
        description="Full access: 161 controls, 32 frameworks, AAF scoring, code review.",
    ),
}

# Frameworks available to free tier (most common compliance standards)
FREE_FRAMEWORKS = {
    "NIST_AI_RMF", "ISO_42001", "SOC2_Type2", "GDPR", "OWASP_LLM_Top10"
}


def get_policy(tier: str) -> TierPolicy:
    """Return policy for a tier, defaulting to 'free' for unknown tiers."""
    if tier not in VALID_TIERS:
        return TIER_POLICIES["free"]
    return TIER_POLICIES[tier]


def apply_control_limit(tier: str, controls: list[Any]) -> tuple[list[Any], dict]:
    """Truncate controls list to tier limit. Return (limited_list, meta)."""
    policy = get_policy(tier)
    total = len(controls)
    limited = controls[: policy.control_limit]
    meta: dict = {
        "tier": tier,
        "returned": len(limited),
        "total_available": total,
    }
    if len(limited) < total:
        meta["upgrade_note"] = (
            f"Showing {policy.control_limit} of {total} matching controls. "
            "Upgrade to Pro for full results: cyberstrategyinstitute.com/ai-safe2/"
        )
    return limited, meta


def apply_framework_limit(tier: str, frameworks: dict) -> tuple[dict, dict]:
    """Filter frameworks dict to tier-allowed set. Return (filtered, meta)."""
    policy = get_policy(tier)
    if policy.can_access_all_frameworks:
        return frameworks, {"tier": tier, "frameworks_returned": len(frameworks)}

    allowed = {k: v for k, v in frameworks.items() if k in FREE_FRAMEWORKS}
    meta = {
        "tier": tier,
        "frameworks_returned": len(allowed),
        "frameworks_available": len(frameworks),
        "upgrade_note": (
            f"Showing {len(FREE_FRAMEWORKS)} of 32 frameworks. "
            "Upgrade to Pro for all 32: cyberstrategyinstitute.com/ai-safe2/"
        ),
    }
    return allowed, meta


def gate_tool(tier: str, required_capability: str) -> dict | None:
    """
    Return an error dict if the tier does not have the required capability,
    else return None (access granted).

    Capabilities: 'code_review', 'classify_agent', 'get_resource', 'full_aaf'
    """
    policy = get_policy(tier)
    capability_map = {
        "code_review": policy.can_use_code_review,
        "classify_agent": policy.can_use_classify_agent,
        "get_resource": policy.can_use_get_resource,
        "full_aaf": policy.can_use_full_aaf,
    }
    if not capability_map.get(required_capability, False):
        return {
            "error": "Upgrade required",
            "tier": tier,
            "required": "pro",
            "capability": required_capability,
            "upgrade_url": "https://cyberstrategyinstitute.com/ai-safe2/",
            "detail": (
                f"This feature requires a Pro (Toolkit) token. "
                f"Purchase at cyberstrategyinstitute.com/ai-safe2/"
            ),
        }
    return None
