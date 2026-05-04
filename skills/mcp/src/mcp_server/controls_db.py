"""
AI SAFE2 MCP Server — Controls Database
Loads ai-safe2-controls-v3.0.json at startup and provides
fast lookup by ID, keyword, pillar, priority, framework, and version.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from mcp_server.config import CONTROLS_JSON


class ControlsDB:
    """In-memory index of all 161 AI SAFE2 v3.0 controls."""

    def __init__(self, path: Path = CONTROLS_JSON) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        self.metadata: dict = raw["metadata"]
        self.risk_formula: dict = raw["risk_formula"]
        self.tier_requirements: dict = raw["tier_requirements"]
        self.frameworks: dict = raw["frameworks"]

        # Flat list of all controls (pillar + cross-pillar)
        self._pillar_controls: list[dict] = raw["pillar_controls"]
        self._cp_controls: list[dict] = raw["cross_pillar_controls"]
        self._all: list[dict] = self._pillar_controls + self._cp_controls

        # Indexes
        self._by_id: dict[str, dict] = {c["id"]: c for c in self._all}
        self._by_pillar: dict[str, list[dict]] = {}
        for c in self._all:
            pid = c["pillar_id"]
            self._by_pillar.setdefault(pid, []).append(c)

    # ── Lookups ────────────────────────────────────────────────────────────────

    def get_by_id(self, control_id: str) -> dict | None:
        return self._by_id.get(control_id)

    def get_by_pillar(self, pillar_id: str) -> list[dict]:
        return self._by_pillar.get(pillar_id.upper(), [])

    def search(
        self,
        query: str = "",
        pillar: str = "",
        priority: str = "",
        framework: str = "",
        version: str = "",
        act_tier: str = "",
        include_cp: bool = True,
        limit: int = 50,
    ) -> list[dict]:
        """
        Full-text search across id, name, description, builder_problem, and tags.
        Filters are ANDed together.
        """
        q = query.lower()
        results: list[dict] = []

        pool = self._all if include_cp else self._pillar_controls

        for c in pool:
            # Keyword filter
            if q:
                searchable = " ".join([
                    c.get("id", ""),
                    c.get("name", ""),
                    c.get("description", ""),
                    c.get("builder_problem", ""),
                    " ".join(c.get("tags", [])),
                ]).lower()
                if q not in searchable:
                    continue

            # Pillar filter
            if pillar and c.get("pillar_id", "").upper() != pillar.upper():
                continue

            # Priority filter
            if priority and c.get("priority", "").upper() != priority.upper():
                continue

            # Framework filter
            if framework:
                fw_list = c.get("compliance_frameworks", [])
                if not any(framework.upper() in fw.upper() for fw in fw_list):
                    continue

            # Version filter
            if version and c.get("version_added", "") != version:
                continue

            # ACT tier filter
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
        return {
            "total": len(self._all),
            "pillar_controls": len(self._pillar_controls),
            "cross_pillar_controls": len(self._cp_controls),
            "frameworks": len(self.frameworks),
        }


@lru_cache(maxsize=1)
def get_db() -> ControlsDB:
    """Singleton — loaded once at startup."""
    return ControlsDB()
