"""Discover agent harnesses without reading credentials or secret values."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.bounded_process import run_bounded

HARNESSES = (
    {"id": "codex", "commands": ("codex",), "home": (".codex",), "project": ("AGENTS.md", ".codex")},
    {"id": "claude-code", "commands": ("claude",), "home": (".claude",), "project": ("CLAUDE.md", ".claude")},
    {"id": "antigravity", "commands": ("antigravity",), "home": (".antigravity",), "project": (".antigravity",)},
    {"id": "hermes", "commands": ("hermes",), "home": (".hermes",), "project": (".hermes",)},
    {"id": "openclaw", "commands": ("openclaw",), "home": (".openclaw",), "project": (".openclaw",)},
    {"id": "grok", "commands": ("grok",), "home": (".grok",), "project": (".grok",)},
)


def _path_record(path: Path, kind: str, scope: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "scope": scope,
        "path": str(path),
        "is_directory": path.is_dir(),
    }


def _discover_harness(spec: dict[str, Any], root: Path, home: Path) -> dict[str, Any] | None:
    evidence: list[dict[str, Any]] = []
    commands = []
    for command in spec["commands"]:
        executable = shutil.which(command)
        if executable:
            commands.append({"command": command, "path": executable})
    for name in spec["home"]:
        path = home / name
        if path.exists():
            evidence.append(_path_record(path, "configuration", "user"))
    for name in spec["project"]:
        path = root / name
        if path.exists():
            evidence.append(_path_record(path, "configuration", "project"))
    if not commands and not evidence:
        return None
    return {
        "id": spec["id"],
        "detected": True,
        "commands": commands,
        "evidence": evidence,
        "confidence": "high" if commands and evidence else "medium",
    }


def _discover_shells() -> list[dict[str, Any]]:
    candidates = (("powershell", "powershell"), ("pwsh", "powershell"), ("bash", "posix"), ("zsh", "posix"))
    rows = []
    for command, family in candidates:
        executable = shutil.which(command)
        if executable:
            rows.append({"id": command, "family": family, "path": executable})
    return rows


def _discover_wsl(timeout: float) -> dict[str, Any]:
    executable = shutil.which("wsl.exe") or shutil.which("wsl")
    result: dict[str, Any] = {
        "available": bool(executable),
        "distributions": [],
        "status": "not_available" if not executable else "available",
    }
    if not executable:
        return result
    try:
        completed = run_bounded(
            [executable, "--list", "--quiet"], timeout=timeout, max_bytes=1_000_000
        )
        if completed.exceeded:
            result["status"] = "failed"
            result["error_type"] = "wsl_output_limit"
            return result
        raw = completed.stdout.decode("utf-16-le", errors="replace")
        distributions = [
            line.strip().strip("\x00")[:100]
            for line in raw.splitlines()[:100]
            if line.strip().strip("\x00")
        ]
        result["distributions"] = distributions
        result["status"] = "completed" if completed.returncode == 0 else "failed"
        result["return_code"] = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["status"] = "failed"
        result["error_type"] = type(exc).__name__
    return result


def discover_local(root: Path, *, include_wsl: bool = True, timeout: float = 5.0) -> dict[str, Any]:
    """Return a metadata-only inventory; file contents and environment values are excluded."""
    root = root.resolve()
    home = Path.home().resolve()
    harnesses = [row for spec in HARNESSES if (row := _discover_harness(spec, root, home))]
    environments: list[dict[str, Any]] = [
        {
            "id": "host",
            "type": "operating_system",
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        }
    ]
    if include_wsl:
        environments.append({"id": "wsl", "type": "virtualized_linux", **_discover_wsl(timeout)})
    shells = _discover_shells()
    ci_markers = [name for name in ("GITHUB_ACTIONS", "GITLAB_CI", "TF_BUILD", "CI") if os.getenv(name)]
    return {
        "schema_version": "safe2.discovery.v1",
        "collected_at": datetime.now(UTC).isoformat(),
        "scope": {"type": "local", "root": str(root)},
        "privacy": {
            "mode": "metadata_only",
            "secret_values_collected": False,
            "configuration_contents_collected": False,
            "configuration_contents_read_locally": False,
            "raw_configuration_contents_retained": False,
            "configuration_values_emitted": False,
        },
        "harnesses": harnesses,
        "environments": environments,
        "shells": shells,
        "ci_markers": ci_markers,
        "summary": {
            "harnesses_detected": len(harnesses),
            "execution_environments": len(environments),
            "shells_detected": len(shells),
            "assessment_status": "inventory_only",
        },
        "limitations": [
            "Discovery is not proof that a detected harness is active, current, or securely configured.",
            "Configuration contents, credentials, remote hosts, containers, and cloud accounts were not inspected.",
            "WSL distribution names are inventoried; distribution contents are not inspected in this version.",
        ],
    }
