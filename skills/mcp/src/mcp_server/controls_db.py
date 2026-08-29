"""
AI SAFE2 MCP Server: controls database.

Loads the 161-control core taxonomy and the AI SAFE2 v3.1 CP.5.MCP profile.
The MCP profile contains sub-controls and does not change the 161-control
framework total.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from mcp_server.config import (
    CONTROLS_JSON,
    FRAMEWORK_VERSION,
    MCP_PROFILE_JSON,
    MCP_SPEC_VERSION,
)


class ControlsDB:
    """In-memory index of AI SAFE2 v3.1 framework and platform-profile controls."""

    def __init__(
        self,
        path: Path = CONTROLS_JSON,
        mcp_profile_path: Path = MCP_PROFILE_JSON,
    ) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        self.metadata: dict = dict(raw["metadata"])
        self.metadata["version"] = FRAMEWORK_VERSION
        self.metadata["release_version"] = FRAMEWORK_VERSION
        self.metadata["core_taxonomy_source_version"] = raw["metadata"].get("version", "3.0.0")
        self.metadata["mcp_spec_version"] = MCP_SPEC_VERSION

        self.risk_formula: dict = raw["risk_formula"]
        self.tier_requirements: dict = raw["tier_requirements"]
        self.frameworks: dict = raw["frameworks"]

        self._pillar_controls: list[dict] = raw["pillar_controls"]
        self._cp_controls: list[dict] = raw["cross_pillar_controls"]
        self._framework_controls: list[dict] = self._pillar_controls + self._cp_controls

        self._platform_profiles: dict[str, list[dict]] = {}
        if mcp_profile_path.exists():
            with open(mcp_profile_path, encoding="utf-8") as f:
                mcp_profile = json.load(f)
            self._platform_profiles["CP.5.MCP"] = mcp_profile.get("controls", [])
            self.metadata["mcp_profile_version"] = mcp_profile.get("metadata", {}).get("version")
            self.metadata["mcp_profile_controls"] = len(self._platform_profiles["CP.5.MCP"])

        self._profile_controls: list[dict] = [
            control
            for controls in self._platform_profiles.values()
            for control in controls
        ]
        self._queryable_controls: list[dict] = self._framework_controls + self._profile_controls

        self._by_id: dict[str, dict] = {c["id"]: c for c in self._queryable_controls}
        self._by_pillar: dict[str, list[dict]] = {}
        for c in self._framework_controls:
            pid = c["pillar_id"]
            self._by_pillar.setdefault(pid, []).append(c)

    def get_by_id(self, control_id: str) -> dict | None:
        """Resolve framework controls and CP.5.MCP profile controls by ID."""
        return self._by_id.get(control_id)

    def get_by_pillar(self, pillar_id: str) -> list[dict]:
        return self._by_pillar.get(pillar_id.upper(), [])

    def get_platform_profile(self, profile_id: str) -> list[dict]:
        return self._platform_profiles.get(profile_id.upper(), self._platform_profiles.get(profile_id, []))

    def search(
        self,
        query: str = "",
        pillar: str = "",
        priority: str = "",
        framework: str = "",
        version: str = "",
        act_tier: str = "",
        include_cp: bool = True,
        include_profiles: bool = True,
        limit: int = 50,
    ) -> list[dict]:
        """Search framework controls and, by default, platform-profile controls."""
        q = query.lower()
        results: list[dict] = []

        pool: list[dict] = list(self._framework_controls if include_cp else self._pillar_controls)
        if include_profiles:
            pool.extend(self._profile_controls)

        for c in pool:
            if q:
                searchable = " ".join(
                    [
                        c.get("id", ""),
                        c.get("name", ""),
                        c.get("description", ""),
                        c.get("builder_problem", ""),
                        " ".join(c.get("tags", [])),
                    ]
                ).lower()
                if q not in searchable:
                    continue

            if pillar and c.get("pillar_id", "").upper() != pillar.upper():
                continue

            if priority and c.get("priority", "").upper() != priority.upper():
                continue

            if framework:
                fw_list = c.get("compliance_frameworks", [])
                if not any(framework.upper() in fw.upper() for fw in fw_list):
                    continue

            if version and c.get("version_added", c.get("mcp_spec_version", "")) != version:
                continue

            if act_tier:
                act_reqs = c.get("act_minimum", [])
                if act_tier not in act_reqs:
                    continue

            results.append(c)

        return results[:limit]

    def get_cross_pillar(self) -> list[dict]:
        return self._cp_controls

    def get_act_requirements(self, tier: str) -> dict | None:
        return self.tier_requirements.get(tier)

    def count(self) -> dict:
        """Keep framework and profile counts separate to prevent double counting."""
        return {
            "total": len(self._framework_controls),
            "pillar_controls": len(self._pillar_controls),
            "cross_pillar_controls": len(self._cp_controls),
            "platform_profile_controls": len(self._profile_controls),
            "queryable_controls": len(self._queryable_controls),
            "frameworks": len(self.frameworks),
        }


@lru_cache(maxsize=1)
def get_db() -> ControlsDB:
    """Singleton loaded once at startup."""
    return ControlsDB()
