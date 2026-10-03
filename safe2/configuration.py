"""Versioned, bounded project configuration for the AI SAFE2 CLI."""

from __future__ import annotations

import json
import os
import stat
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

CONFIG_SCHEMA = "safe2.config.v1"
CONFIG_RELATIVE_PATH = Path(".safe2") / "config.toml"
MAX_CONFIG_BYTES = 1_048_576
PROFILES = ("local", "ci", "enterprise")

_DEFAULTS: dict[str, Any] = {
    "schema_version": CONFIG_SCHEMA,
    "project": {"profile": "local"},
    "privacy": {
        "collect_content": False,
        "collect_prompts": False,
        "collect_environment_values": False,
        "network_export": False,
    },
    "output": {"directory": ".safe2/evidence", "format": "json", "overwrite": False},
    "limits": {"max_files": 10_000, "max_file_bytes": 5_000_000},
}

_ALLOWED: dict[str, set[str]] = {
    "root": {"schema_version", "project", "privacy", "output", "limits"},
    "project": {"name", "profile"},
    "privacy": {
        "collect_content",
        "collect_prompts",
        "collect_environment_values",
        "network_export",
    },
    "output": {"directory", "format", "overwrite"},
    "limits": {"max_files", "max_file_bytes"},
}


class ConfigurationError(ValueError):
    """Raised when a configuration source cannot be trusted or validated."""


def default_configuration(
    *, profile: str = "local", project_name: str | None = None
) -> dict[str, Any]:
    """Return a new secure-default configuration for a named profile."""
    if profile not in PROFILES:
        raise ConfigurationError(f"unsupported profile: {profile}")
    result = deepcopy(_DEFAULTS)
    result["project"]["profile"] = profile
    if project_name:
        result["project"]["name"] = project_name
    if profile in {"ci", "enterprise"}:
        result["limits"]["max_files"] = 50_000
    return result


def _regular_file(path: Path) -> None:
    if path.parent.is_symlink():
        raise ConfigurationError("symbolic-link configuration directories are not allowed")
    try:
        info = path.lstat()
    except OSError as exc:
        raise ConfigurationError(f"configuration is not readable: {path}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise ConfigurationError("symbolic-link configuration files are not allowed")
    if not stat.S_ISREG(info.st_mode):
        raise ConfigurationError("configuration must be a regular file")
    if info.st_size > MAX_CONFIG_BYTES:
        raise ConfigurationError(f"configuration exceeds {MAX_CONFIG_BYTES} bytes")


def _validate_keys(data: dict[str, Any]) -> None:
    unknown = set(data) - _ALLOWED["root"]
    if unknown:
        raise ConfigurationError(f"unknown top-level keys: {', '.join(sorted(unknown))}")
    for section in ("project", "privacy", "output", "limits"):
        value = data.get(section, {})
        if not isinstance(value, dict):
            raise ConfigurationError(f"{section} must be a table")
        unknown = set(value) - _ALLOWED[section]
        if unknown:
            raise ConfigurationError(f"unknown {section} keys: {', '.join(sorted(unknown))}")


def validate_configuration(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a parsed configuration without weakening defaults."""
    if not isinstance(data, dict):
        raise ConfigurationError("configuration root must be a table")
    _validate_keys(data)
    if data.get("schema_version") != CONFIG_SCHEMA:
        raise ConfigurationError(f"schema_version must be {CONFIG_SCHEMA}")

    project = data.get("project", {})
    profile = project.get("profile", "local")
    if profile not in PROFILES:
        raise ConfigurationError(f"project.profile must be one of: {', '.join(PROFILES)}")
    name = project.get("name")
    if name is not None and (not isinstance(name, str) or not name.strip() or len(name) > 128):
        raise ConfigurationError(
            "project.name must be a non-empty string of at most 128 characters"
        )

    result = default_configuration(profile=profile, project_name=name)
    for section in ("privacy", "output", "limits"):
        result[section].update(data.get(section, {}))

    for key in _ALLOWED["privacy"]:
        if not isinstance(result["privacy"][key], bool):
            raise ConfigurationError(f"privacy.{key} must be true or false")
    if result["output"]["format"] not in {"json"}:
        raise ConfigurationError("output.format must be json")
    if not isinstance(result["output"]["directory"], str) or not result["output"]["directory"]:
        raise ConfigurationError("output.directory must be a non-empty string")
    output_directory = Path(result["output"]["directory"])
    if output_directory.is_absolute() or output_directory.drive:
        raise ConfigurationError("output.directory must be relative to the project")
    if ".." in output_directory.parts:
        raise ConfigurationError("output.directory must not escape the project")
    if not isinstance(result["output"]["overwrite"], bool):
        raise ConfigurationError("output.overwrite must be true or false")
    for key in _ALLOWED["limits"]:
        value = result["limits"][key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigurationError(f"limits.{key} must be a positive integer")
    if result["limits"]["max_files"] > 1_000_000:
        raise ConfigurationError("limits.max_files must not exceed 1000000")
    if result["limits"]["max_file_bytes"] > 100_000_000:
        raise ConfigurationError("limits.max_file_bytes must not exceed 100000000")
    return result


def read_configuration(path: Path) -> dict[str, Any]:
    """Read one bounded TOML configuration and return its normalized form."""
    _regular_file(path)
    try:
        raw = path.read_bytes()
        parsed = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(f"configuration is not valid UTF-8 TOML: {path}") from exc
    return validate_configuration(parsed)


def discover_configuration(start: Path) -> Path | None:
    """Find the nearest project configuration without crossing filesystem ancestry."""
    current = start.absolute()
    if current.is_file():
        current = current.parent
    for root in (current, *current.parents):
        candidate = root / CONFIG_RELATIVE_PATH
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return None


def resolve_configuration(
    *,
    explicit: Path | None = None,
    start: Path | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[dict[str, Any], str]:
    """Resolve explicit, environment, project, then built-in configuration precedence."""
    env = os.environ if environ is None else environ
    if explicit is not None:
        return read_configuration(explicit), "explicit"
    configured = env.get("SAFE2_CONFIG")
    if configured:
        return read_configuration(Path(configured)), "environment"
    discovered = discover_configuration(start or Path.cwd())
    if discovered is not None:
        return read_configuration(discovered), "project"
    return default_configuration(), "defaults"


def render_configuration(data: dict[str, Any]) -> str:
    """Render the constrained v1 configuration as deterministic TOML."""
    validated = validate_configuration(data)
    lines = [f'schema_version = "{CONFIG_SCHEMA}"', ""]
    for section in ("project", "privacy", "output", "limits"):
        lines.append(f"[{section}]")
        for key, value in validated[section].items():
            if isinstance(value, bool):
                encoded = "true" if value else "false"
            elif isinstance(value, int):
                encoded = str(value)
            else:
                encoded = json.dumps(value, ensure_ascii=True)
            lines.append(f"{key} = {encoded}")
        lines.append("")
    return "\n".join(lines)


def initialize_project(root: Path, *, profile: str, project_name: str | None) -> Path:
    """Create a configuration exclusively; existing paths and symlink parents fail closed."""
    root = root.absolute()
    try:
        root_info = root.lstat()
    except OSError as exc:
        raise ConfigurationError("project path must be an existing directory") from exc
    if stat.S_ISLNK(root_info.st_mode):
        raise ConfigurationError("symbolic-link project paths are not allowed")
    if not stat.S_ISDIR(root_info.st_mode):
        raise ConfigurationError("project path must be an existing directory")
    config_dir = root / CONFIG_RELATIVE_PATH.parent
    if config_dir.is_symlink():
        raise ConfigurationError("symbolic-link configuration directories are not allowed")
    try:
        config_dir.mkdir(mode=0o700, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(
            f"configuration directory cannot be created: {config_dir}"
        ) from exc
    if not config_dir.is_dir():
        raise ConfigurationError("configuration directory path is not a directory")
    target = config_dir / CONFIG_RELATIVE_PATH.name
    payload = render_configuration(
        default_configuration(profile=profile, project_name=project_name)
    )
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise ConfigurationError(f"configuration already exists: {target}") from exc
    return target
