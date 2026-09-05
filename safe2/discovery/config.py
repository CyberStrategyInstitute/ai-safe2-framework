"""Opt-in structural inspection of agent and MCP configuration files."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

SECRET_KEY_TERMS = ("token", "secret", "password", "credential", "api_key", "apikey", "authorization")
SAFE_POLICY_VALUES = {
    "default",
    "ask",
    "on-request",
    "on-failure",
    "never",
    "untrusted",
    "workspace-write",
    "read-only",
    "danger-full-access",
    "bypass",
    "disabled",
    "none",
}


def _safe_name(value: object) -> str:
    text = "".join(character for character in str(value) if character.isprintable())
    return text[:100]


def _secret_key_count(value: Any) -> int:
    if isinstance(value, dict):
        count = sum(any(term in str(key).lower() for term in SECRET_KEY_TERMS) for key in value)
        return count + sum(_secret_key_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(_secret_key_count(item) for item in value)
    return 0


def _named_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _summarize_mcp(data: dict[str, Any]) -> list[dict[str, Any]]:
    servers = _named_mapping(data.get("mcpServers") or data.get("mcp_servers") or data.get("servers"))
    rows = []
    for name, raw in sorted(servers.items(), key=lambda item: str(item[0])):
        config = _named_mapping(raw)
        transport = "remote" if "url" in config else "local" if "command" in config else "unknown"
        env = _named_mapping(config.get("env"))
        headers = _named_mapping(config.get("headers"))
        args = config.get("args")
        rows.append(
            {
                "name": _safe_name(name),
                "transport": transport,
                "environment_key_count": len(env),
                "header_name_count": len(headers),
                "argument_count": len(args) if isinstance(args, list) else 0,
                "has_command": "command" in config,
                "has_url": "url" in config,
            }
        )
    return rows


def _rule_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 1 if value is not None else 0


def _summarize_permissions(data: dict[str, Any]) -> dict[str, int]:
    permissions = _named_mapping(data.get("permissions"))
    return {
        name: _rule_count(permissions.get(name))
        for name in ("allow", "deny", "ask")
        if name in permissions
    }


def _summarize_hooks(data: dict[str, Any]) -> list[dict[str, Any]]:
    hooks = _named_mapping(data.get("hooks"))
    return [
        {"event": _safe_name(name), "registration_count": _rule_count(value)}
        for name, value in sorted(hooks.items(), key=lambda item: str(item[0]))
    ]


def _safe_scalar(data: dict[str, Any], *names: str) -> str | bool | int | float | None:
    for name in names:
        value = data.get(name)
        if isinstance(value, (str, bool, int, float)):
            return value
    return None


def inspect_config(path: Path, *, max_bytes: int = 1_048_576) -> dict[str, Any]:
    """Read one opted-in config locally and emit only an allowlisted structural summary."""
    base = {"path": str(path), "content_emitted": False, "secret_values_emitted": False}
    if path.is_symlink():
        return {**base, "status": "skipped", "reason": "symlink"}
    try:
        size = path.stat().st_size
    except OSError as exc:
        return {**base, "status": "failed", "error_type": type(exc).__name__}
    if size > max_bytes:
        return {**base, "status": "skipped", "reason": "size_limit", "size_bytes": size}
    try:
        raw = path.read_bytes()
        if path.suffix.lower() == ".toml":
            data = tomllib.loads(raw.decode("utf-8"))
            config_format = "toml"
        else:
            data = json.loads(raw.decode("utf-8"))
            config_format = "json"
        if not isinstance(data, dict):
            return {**base, "status": "failed", "error_type": "non_object_root"}
    except (
        OSError,
        RecursionError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
    ) as exc:
        return {**base, "status": "failed", "error_type": type(exc).__name__, "size_bytes": size}
    runtime_policy = {
        "sandbox_mode": _safe_scalar(data, "sandbox_mode", "sandboxMode"),
        "approval_policy": _safe_scalar(data, "approval_policy", "approvalPolicy", "permission_mode"),
    }
    runtime_policy = {
        key: str(value).lower() if str(value).lower() in SAFE_POLICY_VALUES else "other"
        for key, value in runtime_policy.items()
        if value is not None
    }
    return {
        **base,
        "status": "completed",
        "format": config_format,
        "size_bytes": size,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "top_level_keys": sorted(_safe_name(key) for key in list(data)[:200]),
        "secret_like_key_count": _secret_key_count(data),
        "mcp_servers": _summarize_mcp(data),
        "permission_rule_counts": _summarize_permissions(data),
        "hook_events": _summarize_hooks(data),
        "runtime_policy": runtime_policy,
    }


def inspect_inventory(root: Path, inventory: dict[str, Any], *, max_bytes: int = 1_048_576) -> dict[str, Any]:
    """Inspect only config assets identified by the bounded project inventory."""
    root = root.resolve()
    candidates = [
        asset
        for asset in inventory.get("assets", [])
        if asset.get("type") in {"mcp_configuration", "harness_configuration"}
    ]
    results = []
    for asset in candidates:
        supplied_path = asset.get("path")
        if not isinstance(supplied_path, str):
            results.append(
                {"path": "invalid", "status": "failed", "reason": "invalid_asset_path"}
            )
            continue
        relative = Path(supplied_path)
        if relative.is_absolute():
            results.append(
                {"path": supplied_path, "status": "failed", "reason": "outside_root"}
            )
            continue
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            results.append(
                {"path": supplied_path, "status": "failed", "reason": "outside_root"}
            )
            continue
        result = inspect_config(candidate, max_bytes=max_bytes)
        result["path"] = supplied_path
        results.append(result)
    completed = [row for row in results if row["status"] == "completed"]
    return {
        "schema_version": "safe2.configuration-inspection.v1",
        "mode": "explicit_opt_in",
        "files": results,
        "summary": {
            "candidates": len(candidates),
            "completed": len(completed),
            "incomplete": len(results) - len(completed),
            "mcp_servers": sum(len(row.get("mcp_servers", [])) for row in completed),
            "secret_like_keys": sum(row.get("secret_like_key_count", 0) for row in completed),
        },
        "privacy": {
            "contents_read_locally": True,
            "contents_emitted": False,
            "secret_values_emitted": False,
            "urls_commands_arguments_emitted": False,
        },
    }
