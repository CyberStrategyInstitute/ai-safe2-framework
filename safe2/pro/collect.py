"""Collect `aisafe2-project-manifest/1` facts for `safe2 assess --pro`.

The manifest carries names, boolean flags, counts, and digests only. File contents,
prompts, secret values, command lines, environment values, and tool arguments are
read into memory when a flag requires it and are never written to the manifest or
to the collection notes. Files are read only through the bounded, symlink-rejecting
reader in `safe2.secure_io`, and discovered only through the bounded asset inventory.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from safe2 import __version__
from safe2.contracts import validate_artifact
from safe2.discovery.assets import inventory_assets
from safe2.discovery.local import HARNESSES
from safe2.pro.heuristics import Heuristics, load_heuristics
from safe2.secure_io import read_regular_bounded
from scanner.scanner import _KNOWN_SECRET

MANIFEST_VERSION = "aisafe2-project-manifest/1"
MANIFEST_SCHEMA = "aisafe2-project-manifest-1"
GENERATOR_NAME = "safe2 assess --pro"
NOTES_SCHEMA = "safe2.pro-collection-notes.v1"

_MAX_NAME = 200
_MAX_TOOLS = 500
_MAX_LINE_CHARS = 10_000
_MAX_FRONTMATTER_LINES = 200
_MAX_HOOKS = 200
_MAX_USER_AGENT_FILES = 200
_PINNED_DIGEST = re.compile(r"(?:@sha256:|(?<![A-Za-z0-9])sha256:)([0-9a-f]{64})(?![0-9a-f])")
_TOOL_NAME = re.compile(r"^[A-Za-z0-9_.:*\-]{1,200}$")
_EVENT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_FRONTMATTER_KEYS = {"name", "tools", "disallowedTools", "permissionMode", "memory"}
_SECRET_TERMS = ("token", "secret", "password", "credential", "api_key", "apikey", "api-key")
_READ_KINDS = {"agent_definition", "mcp_configuration", "harness_configuration", "environment_file"}
# Doctor's known user-level locations: (home directory, file, kind). Directories are listed
# only for agent definitions. `~/.claude.json` is not a doctor-known location and is not read.
_USER_FILES = ((".claude", "settings.json", "harness_configuration"), (".codex", "config.toml", "harness_configuration"))
_USER_AGENT_DIRS = ((".claude", "agents"),)


class ManifestCollectionError(ValueError):
    """Raised when facts cannot be collected completely enough to describe the project."""


class ManifestValidationError(ValueError):
    """Raised when a manifest does not satisfy the vendored schema. Carries paths only."""

    def __init__(self, violations: list[dict[str, str]]) -> None:
        self.violations = violations
        paths = ", ".join(sorted({row["instance_path"] for row in violations})[:10])
        super().__init__(f"manifest does not match {MANIFEST_VERSION}: {paths}")


@dataclass
class Collection:
    """The manifest plus local-only notes explaining every default and omission."""

    manifest: dict[str, Any]
    notes: dict[str, Any]


@dataclass
class _Source:
    display: str
    path: Path
    kind: str
    scope: str


@dataclass
class _Settings:
    allow: set[str] = field(default_factory=set)
    deny: set[str] = field(default_factory=set)
    ask: set[str] = field(default_factory=set)
    modes: list[str] = field(default_factory=list)
    hooks: list[tuple[str, str | None]] = field(default_factory=list)


def pro_asset_classifier(path: Path, relative: str) -> str | None:
    """Classify the extra files `--pro` needs; the default asset classes are unchanged."""
    lower = relative.lower().replace("\\", "/")
    parts = PurePosixPath(lower).parts
    name = path.name.lower()
    if name.endswith(".md") and any(
        parts[index : index + 2] == (".claude", "agents") for index in range(len(parts) - 1)
    ):
        return "agent_definition"
    if name == "settings.local.json" and ".claude" in parts[:-1]:
        return "harness_configuration"
    if name == ".env" or name.startswith(".env."):
        return "environment_file"
    return None


def count_secret_findings(text: str, *, markdown: bool, heuristics: Heuristics) -> int:
    """Count lines holding a secret-pattern match. The matched text is never kept."""
    patterns = heuristics.data["secret_patterns"]
    prefixes = tuple(patterns["placeholder_prefixes"])
    words = tuple(patterns["placeholder_words"])
    findings = 0
    for line in text.splitlines():
        # No line-length cap: a minified single-line JSON config must not hide a secret past a
        # cutoff. Every pattern is linear or bounded, and the file size is already bounded.
        if _KNOWN_SECRET.search(line) or heuristics.secret_private_key.search(line):
            findings += 1
            continue
        if markdown:
            continue
        for match in heuristics.secret_assignment.finditer(line):
            value = match.group(1)
            lowered = value.lower()
            if value.startswith(prefixes) or any(word in lowered for word in words):
                continue
            findings += 1
            break
    return findings


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _text_bytes(value: str) -> bytes:
    """UTF-8 that tolerates a lone surrogate in config text instead of raising."""
    return value.encode("utf-8", "surrogatepass")


def _canonical(value: object) -> bytes:
    return _text_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _split_top_level(value: str) -> list[str]:
    """Split on commas that are not inside parentheses, so a specifier never splits."""
    parts: list[str] = []
    depth, start = 0, 0
    for index, character in enumerate(value):
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        elif character == "," and depth == 0:
            parts.append(value[start:index])
            start = index + 1
    parts.append(value[start:])
    return [part.strip().strip("'\"") for part in parts if part.strip()]


def _clean_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = "".join(character for character in value if character.isprintable()).strip()
    return text[:_MAX_NAME] or None


def _tool_name(value: object) -> str | None:
    """Reduce a tool or rule to its bare name. Everything from the first `(` on is dropped."""
    if not isinstance(value, str):
        return None
    name = value.split("(", 1)[0].strip()
    return name if _TOOL_NAME.match(name) else None


def _bare_rule_name(value: object) -> str | None:
    """Return the tool name only for a rule that has no specifier."""
    if not isinstance(value, str) or "(" in value:
        return None
    return _tool_name(value)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Read only the allowlisted frontmatter keys; the body and other keys are never kept."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, Any] = {}
    current: str | None = None
    for line in lines[1:_MAX_FRONTMATTER_LINES]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or stripped.startswith("#"):
            continue
        if line[0] in " \t" or stripped.startswith("- "):
            if current in _FRONTMATTER_KEYS and stripped.startswith("- "):
                bucket = values.setdefault(current, [])
                if isinstance(bucket, list):
                    bucket.append(stripped[2:].strip().strip("'\""))
            continue
        key, separator, value = line.partition(":")
        current = key.strip()
        if not separator or current not in _FRONTMATTER_KEYS:
            continue
        value = value.strip()
        if current in {"tools", "disallowedTools"}:
            inner = value[1:-1] if value.startswith("[") and value.endswith("]") else value
            values[current] = _split_top_level(inner)
        else:
            values[current] = value.strip("'\"")
    return values


def _parse_json(raw: bytes) -> dict[str, Any] | None:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return None
    return data if isinstance(data, dict) else None


def _parse_toml(raw: bytes) -> dict[str, Any] | None:
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, RecursionError):
        return None


def _rule_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _hook_commands(hooks: object) -> list[tuple[str, str | None]]:
    found: list[tuple[str, str | None]] = []
    if not isinstance(hooks, dict):
        return found
    for event, entries in hooks.items():
        # Event names are a small fixed vocabulary; anything else is reported as "other".
        event_name = str(event) if _EVENT_NAME.match(str(event)) else "other"
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            inner = entry.get("hooks") if isinstance(entry.get("hooks"), list) else [entry]
            for hook in inner:
                if isinstance(hook, dict):
                    command = hook.get("command")
                    found.append((event_name, command if isinstance(command, str) else None))
    return found


def _claude_settings(data: dict[str, Any]) -> _Settings:
    settings = _Settings()
    permissions = data.get("permissions")
    if isinstance(permissions, dict):
        settings.allow.update(_rule_list(permissions.get("allow")))
        settings.deny.update(_rule_list(permissions.get("deny")))
        settings.ask.update(_rule_list(permissions.get("ask")))
        mode = permissions.get("defaultMode")
        if isinstance(mode, str) and mode:
            settings.modes.append(mode[:64])
    settings.hooks = _hook_commands(data.get("hooks"))
    return settings


def _pinned_digest(args: object) -> str | None:
    if not isinstance(args, list):
        return None
    for argument in args:
        if isinstance(argument, str):
            match = _PINNED_DIGEST.search(argument[:_MAX_LINE_CHARS])
            if match:
                return match.group(1)
    return None


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _auth_type(raw: dict[str, Any], transport: str) -> str:
    header_names = {str(key).lower() for key in _mapping(raw.get("headers") or raw.get("http_headers"))}
    env_names = {str(key).lower() for key in _mapping(raw.get("env"))}
    if "oauth" in raw or str(raw.get("auth", "")).lower() == "oauth" or "authorization_server" in raw:
        return "oauth"
    if any(key in raw for key in ("tls", "client_cert", "client_certificate", "mtls")):
        return "mtls"
    if "authorization" in header_names or any(key in raw for key in ("bearer_token", "bearer_token_env_var")):
        return "bearer"
    if any(term in name for name in header_names for term in ("api-key", "apikey", "api_key", "token")):
        return "api_key"
    if transport == "stdio" and any(term in name for name in env_names for term in _SECRET_TERMS):
        return "api_key"
    return "none"


def _server_entry(name: str, raw: object) -> tuple[dict[str, Any] | None, str | None]:
    """Return a manifest server entry from one config entry, or the reason it was skipped."""
    config = _mapping(raw)
    command, url = config.get("command"), config.get("url")
    if isinstance(command, str) and command:
        transport = "stdio"
    elif isinstance(url, str) and url:
        declared = str(config.get("type") or config.get("transport") or "").lower()
        path = urlsplit(url).path.rstrip("/")
        transport = "sse" if declared == "sse" or path.endswith("/sse") else "streamable-http"
    else:
        return None, "no_command_or_url"
    arguments = config.get("args") if isinstance(config.get("args"), list) else []
    pinned = _pinned_digest(arguments) if transport == "stdio" else None
    auth = _auth_type(config, transport)
    structure = {
        "name": name,
        "transport": transport,
        "command": PurePosixPath(str(command).replace("\\", "/")).name if transport == "stdio" else None,
        "argument_count": len(arguments),
        "pinned_digest": pinned,
        "environment_keys": sorted(str(key) for key in _mapping(config.get("env"))),
        "header_names": sorted(
            str(key).lower() for key in _mapping(config.get("headers") or config.get("http_headers"))
        ),
        "auth_type": auth,
        "url_host": (urlsplit(url).hostname or "") if transport != "stdio" and isinstance(url, str) else None,
    }
    return (
        {
            "name": name,
            "transport": transport,
            "pinned_digest": pinned,
            "auth_type": auth,
            "config_digest": _sha256(_canonical(structure)),
        },
        None,
    )


def _servers_in(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("mcpServers", "mcp_servers", "servers"):
        if isinstance(data.get(key), dict):
            return data[key]
    return {}


def _disambiguate(rows: list[tuple[dict[str, Any], str]]) -> None:
    """Give colliding names a path suffix so the server never merges two distinct subjects."""
    counts = Counter(entry["name"] for entry, _ in rows)
    for entry, display in rows:
        if counts[entry["name"]] > 1:
            entry["name"] = f"{entry['name']} [{display}]"[:_MAX_NAME]


def _mode_rank(mode: str, order: list[str]) -> int:
    if mode in order:
        return order.index(mode)
    return len(order) - 1 if len(order) > 1 else 0


def _user_sources(home: Path, notes: dict[str, Any]) -> list[_Source]:
    known = {name for spec in HARNESSES for name in spec["home"]}
    sources: list[_Source] = []
    for directory, filename, kind in _USER_FILES:
        candidate = home / directory / filename
        if directory in known and candidate.is_file():
            sources.append(_Source(f"~/{directory}/{filename}", candidate, kind, "user"))
    for directory, sub in _USER_AGENT_DIRS:
        folder = home / directory / sub
        if directory not in known or not folder.is_dir():
            continue
        try:
            names = sorted(entry.name for entry in folder.iterdir() if entry.name.lower().endswith(".md"))
        except OSError as exc:
            raise ManifestCollectionError(f"~/{directory}/{sub}: unreadable (not_a_readable_regular_file)") from exc
        if len(names) > _MAX_USER_AGENT_FILES:
            raise ManifestCollectionError(
                f"~/{directory}/{sub}: more than {_MAX_USER_AGENT_FILES} agent files; "
                "the manifest would silently omit some"
            )
        sources.extend(
            _Source(f"~/{directory}/{sub}/{name}", folder / name, "agent_definition", "user")
            for name in names
        )
    return sources


def _harness_of(display: str) -> str:
    return "github-copilot" if ".github/agents/" in display else "claude-code"


def collect_manifest(
    root: Path,
    *,
    project_name: str,
    max_files: int,
    max_file_bytes: int,
    home: Path | None = None,
    now: datetime | None = None,
    heuristics: Heuristics | None = None,
) -> Collection:
    """Collect the manifest for one project root. Raises ManifestCollectionError if incomplete."""
    heur = heuristics or load_heuristics()
    root = root.resolve()
    user_home = (home if home is not None else Path.home()).resolve()
    notes: dict[str, Any] = {
        "schema_version": NOTES_SCHEMA,
        "files": [],
        "agent_signals": [],
        "flag_reasons": [],
        "omitted_keys": [
            {
                "key": "ci_gate",
                "reason": "CI was not inspected: collection is local-only and opens no network connection.",
            },
            {
                "key": "project.project_id",
                "reason": "No stable project id is stored yet; the location is an open owner decision. The server falls back to project.name.",
            },
        ],
        "not_collected": [
            {"path": "~/.claude.json", "reason": "outside the user-level locations doctor already knows"},
        ],
        "heuristics": {"schema_version": heur.data["schema_version"], "sha256": heur.digest},
        "limitations": [
            "Flags are heuristics over names and structure; they are not proof of runtime behavior.",
        ],
    }
    inventory = inventory_assets(
        root,
        max_files=max_files,
        hash_contents=False,
        max_hash_bytes=max_file_bytes,
        extra_classifier=pro_asset_classifier,
    )
    if inventory["truncated"]:
        raise ManifestCollectionError(
            f"asset inventory stopped at limits.max_files={max_files}; raise the limit and rerun "
            "so the manifest does not omit agents or servers"
        )

    state_assets: set[str] = set()
    ci_markers: set[str] = set()
    unattended_markers = _mapping(heur.data["unattended"]["ci_markers"])
    sources: list[_Source] = []
    for asset in sorted(inventory["assets"], key=lambda row: row["path"]):
        kind, relative = asset["type"], asset["path"]
        if kind in {"persistent_agent_state", "scheduled_agent_operation"}:
            state_assets.add(kind)
            notes["files"].append({"path": relative, "scope": "project", "kind": kind, "status": "present"})
        elif kind == "ci_pipeline":
            try:
                text = read_regular_bounded(root / relative, limit=max_file_bytes).decode("utf-8", "replace").lower()
            except ValueError as exc:
                raise ManifestCollectionError(f"{relative}: unreadable ({_reason(exc)})") from exc
            for harness, markers in unattended_markers.items():
                if any(marker in text for marker in markers):
                    ci_markers.add(harness)
        elif kind in _READ_KINDS:
            sources.append(_Source(PurePosixPath(*Path(relative).parts).as_posix(), root / relative, kind, "project"))
    sources.extend(_user_sources(user_home, notes))

    config_files: list[dict[str, Any]] = []
    settings_all = _Settings()
    servers: list[tuple[dict[str, Any], str]] = []
    server_tools: set[str] = set()
    definitions: list[tuple[_Source, bytes]] = []
    incomplete: list[str] = []
    for source in sorted(sources, key=lambda row: (row.scope, row.display)):
        try:
            raw = read_regular_bounded(source.path, limit=max_file_bytes)
        except ValueError as exc:
            # A user-level file that exists but cannot be read is not skipped: dropping it could
            # hide a permissive setting and make the project look safer than it is.
            incomplete.append(f"{source.display}: unreadable ({_reason(exc)})")
            continue
        text = raw.decode("utf-8", "replace")
        config_files.append(
            {
                "path": source.display,
                "sha256": _sha256(raw),
                "secret_findings": count_secret_findings(
                    text, markdown=source.kind == "agent_definition", heuristics=heur
                ),
            }
        )
        notes["files"].append({"path": source.display, "scope": source.scope, "kind": source.kind, "status": "read"})
        if source.kind == "agent_definition":
            definitions.append((source, raw))
            continue
        if source.kind == "environment_file":
            continue
        is_toml = source.path.suffix.lower() == ".toml"
        data = _parse_toml(raw) if is_toml else _parse_json(raw)
        if data is None:
            incomplete.append(f"{source.display}: not a valid {'TOML' if is_toml else 'JSON'} object")
            continue
        for name, entry in sorted(_servers_in(data).items(), key=lambda item: str(item[0])):
            server_name = _clean_name(name)
            parsed, skipped = _server_entry(server_name or "", entry) if server_name else (None, "invalid_name")
            if parsed is None:
                notes["not_collected"].append({"path": f"{source.display}#{server_name or 'invalid'}", "reason": skipped})
            else:
                servers.append((parsed, source.display))
                server_tools.add(_tool_name("mcp__" + re.sub(r"[^A-Za-z0-9_.:*-]", "_", server_name)) or "")
        if ".claude/" in f"/{source.display}" and source.path.suffix.lower() == ".json" and source.kind == "harness_configuration":
            parsed_settings = _claude_settings(data)
            settings_all.allow |= parsed_settings.allow
            settings_all.deny |= parsed_settings.deny
            settings_all.ask |= parsed_settings.ask
            settings_all.modes += parsed_settings.modes
            settings_all.hooks += parsed_settings.hooks
        elif source.kind == "harness_configuration" and ".codex" not in source.display:
            notes["not_collected"].append({"path": source.display, "reason": "harness config not parsed (hash and secret count only)"})
    if incomplete:
        raise ManifestCollectionError("; ".join(incomplete))
    if len(config_files) > 500:
        raise ManifestCollectionError("more than 500 config files; narrow the project before using --pro")

    order = list(heur.data["permission_mode_order"])
    mode = max(settings_all.modes, key=lambda value: _mode_rank(value, order)) if settings_all.modes else None
    bare_ask = {name for rule in settings_all.ask if (name := _bare_rule_name(rule))}
    bare_deny = {name for rule in settings_all.deny if (name := _bare_rule_name(rule))}
    allowed = sorted({name for rule in settings_all.allow if (name := _tool_name(rule))} - bare_deny)
    # An agent with no `tools:` line inherits the allow-list and every configured MCP server,
    # so the server-level names stand in for tools the CLI cannot enumerate.
    inherited_tools = sorted(set(allowed) | (server_tools - {""}))
    ask_categories = {category for name in bare_ask for category in heur.categorize(name)}
    approvals = sorted(point for point, category in heur.approval_categories.items() if category in ask_categories)

    agents: list[tuple[dict[str, Any], str]] = []
    unattended_modes = set(heur.data["unattended"]["permission_modes"])
    memory_off = set(heur.data["memory"]["off_values"])
    project_memory = bool(state_assets & set(heur.data["memory"]["state_asset_types"]))
    project_scheduled = bool(state_assets & set(heur.data["unattended"]["scheduled_asset_types"]))
    for source, raw in definitions:
        harness = _harness_of(source.display)
        frontmatter = _parse_frontmatter(raw.decode("utf-8", "replace"))
        stem = PurePosixPath(source.display).name.removesuffix(".md").removesuffix(".agent")
        name = _clean_name(frontmatter.get("name")) or stem
        applies = harness == "claude-code"
        declared = frontmatter.get("tools")
        inherited = not isinstance(declared, list)
        names = {
            n
            for item in (declared if not inherited else inherited_tools if applies else [])
            if (n := _tool_name(item))
        }
        names -= {n for item in _rule_list(frontmatter.get("disallowedTools")) if (n := _tool_name(item))}
        names -= bare_deny if applies else set()
        if len(names) > _MAX_TOOLS:
            raise ManifestCollectionError(f"{source.display}: more than {_MAX_TOOLS} tools; narrow the agent")
        categories = {category for tool in names for category in heur.categorize(tool)}
        mode_signals: list[str] = []
        if str(frontmatter.get("permissionMode", "")) in unattended_modes:
            mode_signals.append("agent_permission_mode")
        if applies and mode in unattended_modes:
            mode_signals.append("settings_permission_mode")
        if project_scheduled:
            mode_signals.append("scheduled_asset")
        if harness in ci_markers:
            mode_signals.append("ci_headless_marker")
        memory_signals: list[str] = []
        if "memory" in categories:
            memory_signals.append("memory_tool")
        memory_value = frontmatter.get("memory")
        if isinstance(memory_value, str) and memory_value.lower() not in memory_off:
            memory_signals.append("memory_frontmatter")
        if project_memory:
            memory_signals.append("memory_state_file")
        spawns, memory, money = "spawn" in categories, bool(memory_signals), "money" in categories
        entry: dict[str, Any] = {
            "name": name,
            "harness": harness,
            "definition_digest": _sha256(raw),
            "tools": sorted(names)[:_MAX_TOOLS],
            "can_spawn_subagents": spawns,
            "persistent_memory": memory,
            "runs_unattended": bool(mode_signals),
            "sends_externally": "send" in categories,
            "moves_money": money,
            "approval_points": approvals if applies else [],
        }
        subject = f"agent:{source.display}"
        for flag, active in (("mandate_configured", spawns), ("memory_provenance", memory), ("budget_ceiling_configured", money)):
            if active:
                entry[flag] = False
                notes["flag_reasons"].append(
                    {"subject": subject, "flag": flag, "value": False, "reason": heur.data["cannot_detect"][flag]}
                )
        notes["agent_signals"].append(
            {
                "subject": subject,
                "tools_inherited": inherited,
                "unattended_signals": mode_signals,
                "memory_signals": memory_signals,
            }
        )
        agents.append((entry, source.display))
    _disambiguate(agents)
    _disambiguate(servers)

    hooks = sorted(
        {
            (event, _sha256(_text_bytes(command)) if command is not None else None)
            for event, command in settings_all.hooks
        },
        key=lambda row: (row[0], row[1] or ""),
    )
    if len(hooks) > _MAX_HOOKS:
        raise ManifestCollectionError(f"more than {_MAX_HOOKS} distinct hooks; the manifest would omit some")
    reported_mode = None if mode is None else (mode if mode in order else "other")
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "generator": {"name": GENERATOR_NAME, "version": __version__},
        "generated_at": (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": {"name": (_clean_name(project_name) or root.name)[:_MAX_NAME]},
        "agents": sorted(
            (entry for entry, _ in agents),
            key=lambda row: (row["harness"], row["name"], row["definition_digest"]),
        ),
        "mcp_servers": sorted(
            (entry for entry, _ in servers),
            key=lambda row: (row["name"], row["transport"], row["config_digest"]),
        ),
        "hooks": [
            {"event": event, **({"command_digest": digest} if digest else {})} for event, digest in hooks
        ],
        "config_files": sorted(config_files, key=lambda row: row["path"]),
    }
    if mode is not None or settings_all.allow or settings_all.deny or settings_all.ask:
        manifest["permissions"] = {
            "allow_rules": len(settings_all.allow),
            "deny_rules": len(settings_all.deny),
            "digest": _sha256(
                _canonical(
                    {
                        "mode": reported_mode,
                        "allow": sorted(settings_all.allow),
                        "deny": sorted(settings_all.deny),
                        "ask": sorted(settings_all.ask),
                    }
                )
            ),
            **({"mode": reported_mode} if reported_mode is not None else {}),
        }
    for entry in (manifest["agents"], manifest["mcp_servers"]):
        if len(entry) > 200:
            raise ManifestCollectionError("more than 200 agents or MCP servers; narrow the project before using --pro")
    return Collection(manifest=manifest, notes=notes)


def _reason(exc: Exception) -> str:
    """A short reason code that never repeats file contents or the OS error text."""
    message = str(exc)
    if "exceeds" in message:
        return "size_limit"
    if "symbolic-link" in message:
        return "symlink"
    return "not_a_readable_regular_file"


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate against the vendored schema. Raises with field paths, never values."""
    violations = validate_artifact(MANIFEST_SCHEMA, manifest)
    if violations:
        raise ManifestValidationError(violations)


def render_manifest(manifest: dict[str, Any]) -> bytes:
    """Deterministic serialization: sorted keys, stable indentation, trailing newline."""
    return (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def render_notes(notes: dict[str, Any], manifest_sha256: str) -> bytes:
    """Local-only notes explaining defaults and omissions. Never uploaded."""
    body = {**notes, "manifest_sha256": manifest_sha256}
    return (json.dumps(body, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
