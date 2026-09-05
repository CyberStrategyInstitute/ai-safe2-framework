"""Bounded metadata inventory for security-relevant agent project assets."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".safe2",
    ".tox",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}

EXCLUDED_DIRECTORY_PREFIXES = (".test-temp", "pytest-")


def _include_directory(name: str) -> bool:
    return name not in EXCLUDED_DIRECTORIES and not name.startswith(EXCLUDED_DIRECTORY_PREFIXES)


def _bounded_sha256(path: Path, max_bytes: int) -> tuple[str | None, str]:
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(min(65_536, max_bytes + 1 - total)):
                total += len(chunk)
                if total > max_bytes:
                    return None, "size_limit"
                digest.update(chunk)
    except OSError:
        return None, "read_error"
    return digest.hexdigest(), "completed"

EXACT_FILES = {
    "AGENTS.md": "agent_instruction",
    "AGENTS.override.md": "agent_instruction",
    "CLAUDE.md": "agent_instruction",
    "GEMINI.md": "agent_instruction",
    "SOUL.md": "persistent_agent_state",
    "IDENTITY.md": "persistent_agent_state",
    "MEMORY.md": "persistent_agent_state",
    "HEARTBEAT.md": "scheduled_agent_operation",
    "SKILL.md": "agent_skill",
    ".mcp.json": "mcp_configuration",
    "mcp.json": "mcp_configuration",
    ".gitlab-ci.yml": "ci_pipeline",
    ".gitlab-ci.yaml": "ci_pipeline",
    "azure-pipelines.yml": "ci_pipeline",
    "azure-pipelines.yaml": "ci_pipeline",
    "Dockerfile": "container_definition",
    "docker-compose.yml": "container_definition",
    "docker-compose.yaml": "container_definition",
    "compose.yml": "container_definition",
    "compose.yaml": "container_definition",
    "Pulumi.yaml": "infrastructure_as_code",
}


def _classify(path: Path, relative: str) -> str | None:
    if path.name in EXACT_FILES:
        return EXACT_FILES[path.name]
    lower_name = path.name.lower()
    lower_relative = relative.lower().replace("\\", "/")
    if lower_name.endswith((".tf", ".bicep")):
        return "infrastructure_as_code"
    if lower_relative.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"}:
        return "ci_pipeline"
    if lower_relative.startswith((".claude/skills/", ".codex/skills/", ".grok/skills/", ".agents/skills/")) and lower_name == "skill.md":
        return "agent_skill"
    if lower_relative.startswith(".github/agents/") and path.suffix.lower() == ".md":
        return "agent_definition"
    if lower_name in {"settings.json", "config.toml"} and any(
        marker in lower_relative for marker in (".claude/", ".codex/", ".grok/", ".openclaw/", ".hermes/")
    ):
        return "harness_configuration"
    return None


def inventory_assets(
    root: Path,
    *,
    max_files: int = 50_000,
    hash_contents: bool = False,
    max_hash_bytes: int = 10_000_000,
) -> dict[str, Any]:
    """Inventory relevant filenames without reading file contents or following symlinks."""
    root = root.resolve()
    assets: list[dict[str, Any]] = []
    visited = 0
    truncated = False
    errors = 0
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names[:] = sorted(name for name in directory_names if _include_directory(name))
        for name in sorted(file_names):
            visited += 1
            if visited > max_files:
                truncated = True
                break
            path = Path(directory) / name
            if path.is_symlink():
                continue
            relative = str(path.relative_to(root))
            asset_type = _classify(path, relative)
            if not asset_type:
                continue
            try:
                stat = path.stat()
                modified = datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
                size = stat.st_size
            except OSError:
                errors += 1
                modified = None
                size = None
            asset: dict[str, Any] = {
                "type": asset_type,
                "path": relative,
                "size_bytes": size,
                "modified_at": modified,
                "content_collected": False,
            }
            if hash_contents:
                asset["content_sha256"], asset["hash_status"] = _bounded_sha256(
                    path, max_hash_bytes
                )
            assets.append(asset)
        if truncated:
            break
    counts: dict[str, int] = {}
    for asset in assets:
        counts[asset["type"]] = counts.get(asset["type"], 0) + 1
    return {
        "schema_version": "safe2.asset-inventory.v1",
        "root": str(root),
        "assets": assets,
        "counts": counts,
        "files_visited": visited,
        "max_files": max_files,
        "truncated": truncated,
        "metadata_errors": errors,
        "privacy": {
            "file_contents_read_locally": hash_contents,
            "file_contents_collected": False,
            "file_contents_emitted": False,
            "symlinks_followed": False,
        },
    }
